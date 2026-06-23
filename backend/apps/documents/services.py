from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.applications.drafts import CredentialError, parse_credential
from apps.applications.models import ApplicationDraft

from .models import ApplicationDocument
from .pdf_validation import ValidatedPDFUpload
from .storage import (
    DocumentStorageCollision,
    DocumentStorageError,
    get_document_storage,
)
from .storage_keys import draft_cv_storage_key

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_STORAGE_COLLISION_RETRIES = 3


class DocumentServiceError(Exception):
    pass


class DraftUnavailable(DocumentServiceError):
    pass


class DraftConflict(DocumentServiceError):
    pass


class DocumentStorageUnavailable(DocumentServiceError):
    pass


class DocumentMetadataUnavailable(DocumentStorageUnavailable):
    pass


@dataclass(frozen=True)
class DocumentMutationResult:
    draft: ApplicationDraft
    created: bool


def active_document_for_draft(draft):
    return draft.documents.filter(deleted_at__isnull=True).first()


def create_or_replace_draft_cv(
    *,
    draft: ApplicationDraft,
    credential: str,
    expected_version: int,
    validated_upload: ValidatedPDFUpload,
) -> DocumentMutationResult:
    metadata = validated_upload.metadata
    if not SHA256_RE.fullmatch(metadata.sha256):
        raise DocumentServiceError("Validated PDF checksum is not canonical.")

    storage = get_document_storage()
    new_document_id, new_storage_key = _save_with_bounded_collision_retry(
        storage=storage,
        draft_id=draft.pk,
        validated_upload=validated_upload,
    )

    old_document_id = None
    created = True
    try:
        with transaction.atomic():
            locked_draft = (
                ApplicationDraft.objects.select_for_update(of=("self",))
                .select_related("vacancy")
                .get(pk=draft.pk)
            )
            _reauthorize_locked_draft(locked_draft, credential)
            if locked_draft.version != expected_version:
                raise DraftConflict()

            old_document = (
                ApplicationDocument.objects.select_for_update()
                .filter(draft=locked_draft, deleted_at__isnull=True)
                .first()
            )
            now = timezone.now()
            if old_document is not None:
                created = False
                old_document_id = old_document.pk
                retire_document_metadata(old_document, now=now)

            try:
                ApplicationDocument.objects.create(
                    id=new_document_id,
                    draft=locked_draft,
                    original_name_display=metadata.original_name_display,
                    storage_key=new_storage_key,
                    detected_content_type=metadata.detected_content_type,
                    size=metadata.size_bytes,
                    sha256=metadata.sha256,
                )
            except IntegrityError as exc:
                raise DocumentMetadataUnavailable() from exc
            locked_draft.record_successful_mutation(now=now)
            locked_draft.save(
                update_fields=["last_activity_at", "expires_at", "version", "updated_at"]
            )
            if old_document_id is not None:
                transaction.on_commit(
                    lambda document_id=old_document_id: attempt_physical_document_delete(
                        document_id
                    )
                )
    except ApplicationDraft.DoesNotExist as exc:
        _compensate_new_storage(storage, new_storage_key)
        raise DraftUnavailable() from exc
    except (DraftUnavailable, DraftConflict, DocumentMetadataUnavailable):
        _compensate_new_storage(storage, new_storage_key)
        raise

    locked_draft.refresh_from_db()
    return DocumentMutationResult(draft=locked_draft, created=created)


def delete_active_draft_cv(
    *,
    draft: ApplicationDraft,
    credential: str,
    expected_version: int,
) -> ApplicationDraft:
    try:
        with transaction.atomic():
            locked_draft = (
                ApplicationDraft.objects.select_for_update(of=("self",))
                .select_related("vacancy")
                .get(pk=draft.pk)
            )
            _reauthorize_locked_draft(locked_draft, credential)
            if locked_draft.version != expected_version:
                raise DraftConflict()

            document = (
                ApplicationDocument.objects.select_for_update()
                .filter(draft=locked_draft, deleted_at__isnull=True)
                .first()
            )
            if document is None:
                raise DraftUnavailable()

            now = timezone.now()
            retire_document_metadata(document, now=now)
            locked_draft.record_successful_mutation(now=now)
            locked_draft.save(
                update_fields=["last_activity_at", "expires_at", "version", "updated_at"]
            )
            transaction.on_commit(
                lambda document_id=document.pk: attempt_physical_document_delete(document_id)
            )
    except ApplicationDraft.DoesNotExist as exc:
        raise DraftUnavailable() from exc

    locked_draft.refresh_from_db()
    return locked_draft


def retire_document_metadata(document: ApplicationDocument, *, now) -> None:
    document.deleted_at = now
    document.original_name_display = ""
    document.save(update_fields=["deleted_at", "original_name_display"])


def lock_active_documents_for_draft(draft: ApplicationDraft) -> list[ApplicationDocument]:
    return list(
        ApplicationDocument.objects.select_for_update().filter(
            draft=draft,
            deleted_at__isnull=True,
        )
    )


def schedule_physical_deletion_for_draft(draft: ApplicationDraft) -> None:
    document_ids = list(
        ApplicationDocument.objects.filter(
            draft=draft,
            deleted_at__isnull=False,
            storage_deleted_at__isnull=True,
        ).values_list("pk", flat=True)
    )
    for document_id in document_ids:
        transaction.on_commit(
            lambda document_id=document_id: attempt_physical_document_delete(document_id)
        )


def attempt_physical_document_delete(document_id: uuid.UUID) -> bool:
    try:
        document = ApplicationDocument.objects.get(pk=document_id)
    except ApplicationDocument.DoesNotExist:
        return True
    if document.deleted_at is None:
        return False
    if document.storage_deleted_at is not None:
        return True
    try:
        get_document_storage().delete(document.storage_key)
    except DocumentStorageError:
        return False
    document.storage_deleted_at = timezone.now()
    document.save(update_fields=["storage_deleted_at"])
    return True


def _save_with_bounded_collision_retry(
    *,
    storage,
    draft_id: uuid.UUID,
    validated_upload: ValidatedPDFUpload,
) -> tuple[uuid.UUID, str]:
    for _ in range(MAX_STORAGE_COLLISION_RETRIES):
        document_id = uuid.uuid4()
        storage_key = draft_cv_storage_key(draft_id, document_id)
        try:
            with validated_upload.open() as handle:
                storage.save(storage_key, handle)
        except DocumentStorageCollision:
            continue
        except DocumentStorageError as exc:
            raise DocumentStorageUnavailable() from exc
        return document_id, storage_key
    raise DocumentStorageUnavailable()


def _compensate_new_storage(storage, storage_key: str) -> None:
    try:
        storage.delete(storage_key)
    except DocumentStorageError:
        return


def _reauthorize_locked_draft(draft: ApplicationDraft, credential: str) -> None:
    try:
        parsed = parse_credential(credential)
    except CredentialError as exc:
        raise DraftUnavailable() from exc
    if (
        parsed.draft_id != draft.pk
        or not draft.check_secret(parsed.secret)
        or not draft.is_active()
    ):
        raise DraftUnavailable()
