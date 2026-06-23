from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.drafts import (
    CredentialError,
    draft_etag,
    parse_if_match,
    resolve_request_draft,
    set_ownership_cookie,
)
from apps.applications.views import (
    authorized_response,
    clear_unavailable_response,
    draft_conflict_response,
    draft_version_required_response,
    no_store,
    unavailable_response,
)
from config.api_errors import api_error_response

from .pdf_validation import (
    EmptyPDFFile,
    MissingPDFFile,
    PDFRequired,
    PDFTooLarge,
    PDFValidationError,
    UnreadablePDF,
    UnsafePDFContent,
    validated_pdf_upload,
)
from .services import (
    DocumentStorageUnavailable,
    DraftConflict,
    DraftUnavailable,
    create_or_replace_draft_cv,
    delete_active_draft_cv,
)
from .upload_handlers import BoundedDocumentUploadHandler


def field_error_response(code: str, message: str, *, status: int, field_message: str):
    response = api_error_response(code, message, status=status)
    response.data["error"]["fields"] = {"file": [field_message]}
    return response


def storage_unavailable_response():
    return api_error_response(
        "document_storage_unavailable",
        "Document storage is temporarily unavailable.",
        status=503,
    )


def pdf_validation_response(error: PDFValidationError):
    if isinstance(error, PDFTooLarge):
        return field_error_response(
            "upload_too_large",
            "Upload a PDF file under 5 MB.",
            status=413,
            field_message="Upload a PDF file under 5 MB.",
        )
    if isinstance(error, PDFRequired):
        return field_error_response(
            "unsupported_file_type",
            "Upload a PDF file under 5 MB.",
            status=415,
            field_message="Upload a PDF file under 5 MB.",
        )
    if isinstance(error, MissingPDFFile | EmptyPDFFile):
        return field_error_response(
            "validation_error",
            "Check the highlighted fields.",
            status=422,
            field_message="Upload a PDF file under 5 MB.",
        )
    if isinstance(error, UnreadablePDF | UnsafePDFContent):
        return field_error_response(
            "invalid_pdf",
            "We could not read that file type. Try exporting your CV as a PDF.",
            status=422,
            field_message="We could not read that file type. Try exporting your CV as a PDF.",
        )
    return field_error_response(
        "invalid_pdf",
        "We could not read that file type. Try exporting your CV as a PDF.",
        status=422,
        field_message="We could not read that file type. Try exporting your CV as a PDF.",
    )


@method_decorator(csrf_protect, name="dispatch")
class CVDocumentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        return no_store(response)

    def get(self, request, draft_id):
        try:
            draft = resolve_request_draft(request, required=True)
        except CredentialError:
            return clear_unavailable_response()
        if draft.pk != draft_id:
            return clear_unavailable_response()
        return authorized_response(draft)

    def put(self, request, draft_id):
        try:
            draft, credential = resolve_request_draft(
                request,
                required=True,
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

        request.upload_handlers.insert(0, BoundedDocumentUploadHandler(request))
        try:
            uploaded_file = self._strict_file(request)
        except PDFValidationError as exc:
            return pdf_validation_response(exc)
        except ValidationError:
            raise
        except ParseError:
            if getattr(request, "_applyflow_document_upload_too_large", False):
                return pdf_validation_response(PDFTooLarge())
            raise
        if getattr(request, "_applyflow_document_upload_too_large", False):
            return pdf_validation_response(PDFTooLarge())

        try:
            with validated_pdf_upload(
                uploaded_file,
                original_filename=uploaded_file.name,
                declared_content_type=uploaded_file.content_type,
                declared_size=uploaded_file.size,
            ) as validated_upload:
                result = create_or_replace_draft_cv(
                    draft=draft,
                    credential=credential,
                    expected_version=expected_version,
                    validated_upload=validated_upload,
                )
        except PDFValidationError as exc:
            return pdf_validation_response(exc)
        except DraftConflict:
            return draft_conflict_response()
        except DraftUnavailable:
            return unavailable_response()
        except DocumentStorageUnavailable:
            return storage_unavailable_response()

        response = authorized_response(result.draft, status=201 if result.created else 200)
        set_ownership_cookie(response, credential, result.draft)
        return response

    def delete(self, request, draft_id):
        try:
            draft, credential = resolve_request_draft(
                request,
                required=True,
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

        try:
            draft = delete_active_draft_cv(
                draft=draft,
                credential=credential,
                expected_version=expected_version,
            )
        except DraftConflict:
            return draft_conflict_response()
        except DraftUnavailable:
            return unavailable_response()

        response = no_store(Response(status=204))
        response["ETag"] = draft_etag(draft)
        set_ownership_cookie(response, credential, draft)
        return response

    def _strict_file(self, request):
        content_type = (request.content_type or "").split(";", maxsplit=1)[0].strip().lower()
        if content_type != "multipart/form-data":
            raise PDFRequired()
        files = request.FILES
        data = request.POST
        if getattr(request, "_applyflow_document_upload_too_large", False):
            raise PDFTooLarge()
        if getattr(request, "_applyflow_document_invalid_multipart", False):
            raise ValidationError({"file": ["Send exactly one PDF file."]})
        if data:
            raise ValidationError({"file": ["Send only the PDF file field."]})
        file_keys = set(files)
        if file_keys != {"file"}:
            raise ValidationError({"file": ["Send exactly one PDF file."]})
        uploaded_files = files.getlist("file")
        if len(uploaded_files) != 1:
            raise ValidationError({"file": ["Send exactly one PDF file."]})
        return uploaded_files[0]
