from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.services import (
    lock_active_documents_for_draft,
    schedule_physical_deletion_for_draft,
)
from apps.vacancies.views import public_vacancies
from config.api_errors import api_error_response

from .drafts import (
    CredentialError,
    clear_creation_cookie,
    clear_ownership_cookie,
    create_or_resolve_draft,
    draft_etag,
    parse_if_match,
    resolve_creation_key,
    resolve_request_draft,
    set_ownership_cookie,
)
from .models import ApplicationDraft, DraftExperienceEntry
from .serializers import (
    CandidatePatchSerializer,
    DraftExperienceEntrySerializer,
    ExperiencePatchSerializer,
    public_draft,
)


def no_store(response):
    response["Cache-Control"] = "no-store"
    return response


def authorized_response(draft, *, status=200):
    response = Response(public_draft(draft), status=status)
    response["ETag"] = draft_etag(draft)
    return no_store(response)


def unavailable_response():
    return no_store(
        api_error_response(
            "draft_unavailable",
            "The application draft is unavailable.",
            status=404,
        )
    )


def clear_unavailable_response():
    response = unavailable_response()
    clear_ownership_cookie(response)
    return response


def draft_version_required_response():
    return api_error_response(
        "draft_version_required",
        "A current draft version is required.",
        status=428,
    )


def draft_conflict_response():
    return api_error_response(
        "draft_conflict",
        "The application draft changed. Refresh and try again.",
        status=409,
    )


def locked_draft_queryset():
    return ApplicationDraft.objects.select_for_update(of=("self",)).select_related("vacancy")


def save_successful_mutation(draft, *, now):
    draft.record_successful_mutation(now=now)
    draft.save(update_fields=["last_activity_at", "expires_at", "version", "updated_at"])


class DraftAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        return no_store(response)


class ActiveDraftView(DraftAPIView):
    def get(self, request):
        try:
            draft = resolve_request_draft(request)
        except CredentialError:
            return clear_unavailable_response()
        if draft is None:
            return no_store(Response(status=204))
        return authorized_response(draft)


@method_decorator(csrf_protect, name="dispatch")
class DraftCollectionView(DraftAPIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            draft = resolve_request_draft(request)
        except CredentialError:
            return clear_unavailable_response()

        vacancy_slug = request.data.get("vacancy_slug") if isinstance(request.data, dict) else None
        vacancy = public_vacancies().filter(slug=vacancy_slug).first()
        if vacancy is None:
            return no_store(
                api_error_response(
                    "vacancy_unavailable",
                    "The vacancy is unavailable.",
                    status=404,
                )
            )

        if draft is not None:
            if draft.vacancy_id != vacancy.pk:
                return no_store(
                    api_error_response(
                        "active_draft_conflict",
                        "Another application draft is already active.",
                        status=409,
                    )
                )
            return authorized_response(draft)

        try:
            creation_key = resolve_creation_key(request)
            draft, credential, created = create_or_resolve_draft(vacancy, creation_key)
        except CredentialError:
            response = clear_unavailable_response()
            clear_creation_cookie(response)
            return response

        if draft.vacancy_id != vacancy.pk:
            response = no_store(
                api_error_response(
                    "active_draft_conflict",
                    "Another application draft is already active.",
                    status=409,
                )
            )
            set_ownership_cookie(response, credential, draft)
            clear_creation_cookie(response)
            return response

        response = authorized_response(draft, status=201 if created else 200)
        set_ownership_cookie(response, credential, draft)
        clear_creation_cookie(response)
        return response


@method_decorator(csrf_protect, name="dispatch")
class DraftDetailView(DraftAPIView):
    def get(self, request, draft_id):
        try:
            draft = resolve_request_draft(request, required=True)
        except CredentialError:
            return clear_unavailable_response()
        if draft.pk != draft_id:
            return clear_unavailable_response()
        return authorized_response(draft)

    def delete(self, request, draft_id):
        with transaction.atomic():
            try:
                draft = resolve_request_draft(
                    request,
                    required=True,
                    queryset=locked_draft_queryset(),
                )
            except CredentialError:
                return clear_unavailable_response()
            if draft.pk != draft_id:
                return clear_unavailable_response()
            try:
                expected_version = parse_if_match(request.headers.get("If-Match"))
            except ValueError:
                return draft_version_required_response()
            if expected_version != draft.version:
                return draft_conflict_response()

            lock_active_documents_for_draft(draft)
            draft.abandon(now=timezone.now())
            draft.save(
                update_fields=[
                    "status",
                    "credential_revoked_at",
                    "last_activity_at",
                    "expires_at",
                    "version",
                    "updated_at",
                ]
            )
            schedule_physical_deletion_for_draft(draft)

        response = no_store(Response(status=204))
        response["ETag"] = draft_etag(draft)
        clear_ownership_cookie(response)
        return response


@method_decorator(csrf_protect, name="dispatch")
class DraftSectionPatchView(DraftAPIView):
    serializer_class = None
    parser_classes = [JSONParser]

    def patch(self, request, draft_id):
        with transaction.atomic():
            try:
                draft, credential = resolve_request_draft(
                    request,
                    required=True,
                    queryset=locked_draft_queryset(),
                    include_credential=True,
                )
            except CredentialError:
                return clear_unavailable_response()
            if draft.pk != draft_id:
                return clear_unavailable_response()

            try:
                expected_version = parse_if_match(request.headers.get("If-Match"))
            except ValueError:
                return draft_version_required_response()
            if expected_version != draft.version:
                return draft_conflict_response()

            serializer = self.serializer_class(instance=draft, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_fields = set(serializer.validated_data)
            for field, value in serializer.validated_data.items():
                setattr(draft, field, value)
            now = timezone.now()
            draft.record_successful_mutation(now=now)
            update_fields.update({"last_activity_at", "expires_at", "version", "updated_at"})
            draft.save(update_fields=update_fields)

        response = authorized_response(draft)
        set_ownership_cookie(response, credential, draft)
        return response


class CandidatePatchView(DraftSectionPatchView):
    serializer_class = CandidatePatchSerializer


class ExperiencePatchView(DraftSectionPatchView):
    serializer_class = ExperiencePatchSerializer


@method_decorator(csrf_protect, name="dispatch")
class ExperienceEntryCollectionView(DraftAPIView):
    parser_classes = [JSONParser]

    def post(self, request, draft_id):
        with transaction.atomic():
            try:
                draft, credential = resolve_request_draft(
                    request,
                    required=True,
                    queryset=locked_draft_queryset(),
                    include_credential=True,
                )
            except CredentialError:
                return clear_unavailable_response()
            if draft.pk != draft_id:
                return clear_unavailable_response()

            try:
                expected_version = parse_if_match(request.headers.get("If-Match"))
            except ValueError:
                return draft_version_required_response()
            if expected_version != draft.version:
                return draft_conflict_response()

            serializer = DraftExperienceEntrySerializer(data=request.data, context={"draft": draft})
            serializer.is_valid(raise_exception=True)
            entry = DraftExperienceEntry(draft=draft, **serializer.validated_data)
            try:
                with transaction.atomic():
                    entry.save()
            except IntegrityError as exc:
                if draft.experience_entries.filter(position=entry.position).exists():
                    raise serializers.ValidationError(
                        {"position": ["Choose a unique position from 0 to 4."]}
                    ) from exc
                raise

            save_successful_mutation(draft, now=timezone.now())

        response = authorized_response(draft, status=201)
        set_ownership_cookie(response, credential, draft)
        return response


@method_decorator(csrf_protect, name="dispatch")
class ExperienceEntryDetailView(DraftAPIView):
    parser_classes = [JSONParser]

    def patch(self, request, draft_id, experience_id):
        with transaction.atomic():
            try:
                draft, credential = resolve_request_draft(
                    request,
                    required=True,
                    queryset=locked_draft_queryset(),
                    include_credential=True,
                )
            except CredentialError:
                return clear_unavailable_response()
            if draft.pk != draft_id:
                return clear_unavailable_response()

            try:
                expected_version = parse_if_match(request.headers.get("If-Match"))
            except ValueError:
                return draft_version_required_response()
            if expected_version != draft.version:
                return draft_conflict_response()

            entry = draft.experience_entries.filter(pk=experience_id).first()
            if entry is None:
                return unavailable_response()

            serializer = DraftExperienceEntrySerializer(
                instance=entry,
                data=request.data,
                partial=True,
                context={"draft": draft},
            )
            serializer.is_valid(raise_exception=True)
            for field, value in serializer.validated_data.items():
                setattr(entry, field, value)
            try:
                with transaction.atomic():
                    entry.save(update_fields=[*serializer.validated_data.keys(), "updated_at"])
            except IntegrityError as exc:
                if (
                    draft.experience_entries.exclude(pk=entry.pk)
                    .filter(position=entry.position)
                    .exists()
                ):
                    raise serializers.ValidationError(
                        {"position": ["Choose a unique position from 0 to 4."]}
                    ) from exc
                raise

            save_successful_mutation(draft, now=timezone.now())

        response = authorized_response(draft)
        set_ownership_cookie(response, credential, draft)
        return response

    def delete(self, request, draft_id, experience_id):
        with transaction.atomic():
            try:
                draft, credential = resolve_request_draft(
                    request,
                    required=True,
                    queryset=locked_draft_queryset(),
                    include_credential=True,
                )
            except CredentialError:
                return clear_unavailable_response()
            if draft.pk != draft_id:
                return clear_unavailable_response()

            try:
                expected_version = parse_if_match(request.headers.get("If-Match"))
            except ValueError:
                return draft_version_required_response()
            if expected_version != draft.version:
                return draft_conflict_response()

            entry = draft.experience_entries.filter(pk=experience_id).first()
            if entry is None:
                return unavailable_response()
            entry.delete()
            save_successful_mutation(draft, now=timezone.now())

        response = no_store(Response(status=204))
        response["ETag"] = draft_etag(draft)
        set_ownership_cookie(response, credential, draft)
        return response
