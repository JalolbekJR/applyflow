import uuid

from django.http import Http404, JsonResponse
from django.views.csrf import csrf_failure as django_csrf_failure
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def error_payload(code: str, message: str, *, request_id=None) -> dict[str, object]:
    request_id = request_id or f"req_{uuid.uuid4().hex}"
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": {},
            "request_id": request_id,
        }
    }


def api_error_response(code: str, message: str, *, status: int) -> Response:
    request_id = f"req_{uuid.uuid4().hex}"
    response = Response(error_payload(code, message, request_id=request_id), status=status)
    response["X-Request-ID"] = request_id
    response["Cache-Control"] = "no-store"
    return response


def csrf_failure(request, reason=""):
    if not request.path_info.startswith("/api/v1/"):
        return django_csrf_failure(request, reason=reason)
    request_id = f"req_{uuid.uuid4().hex}"
    response = JsonResponse(
        error_payload(
            "csrf_failed",
            "CSRF validation failed.",
            request_id=request_id,
        ),
        status=403,
    )
    response["X-Request-ID"] = request_id
    response["Cache-Control"] = "no-store"
    return response


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", "api_error")
    message = "The request could not be completed."
    fields: dict[str, list[str]] = {}

    if isinstance(exc, (Http404, NotFound)):
        code = "not_found"
        message = "The requested resource was not found."
    elif isinstance(exc, ValidationError) and isinstance(response.data, dict):
        code = "validation_error"
        message = "Check the highlighted fields."
        response.status_code = 422
        fields = {
            key: [str(item) for item in value] if isinstance(value, list) else [str(value)]
            for key, value in response.data.items()
        }
    elif isinstance(response.data, dict):
        detail = response.data.get("detail")
        if isinstance(detail, ErrorDetail):
            code = detail.code
            message = str(detail)

    request_id = f"req_{uuid.uuid4().hex}"
    response.data = {
        "error": {
            "code": code,
            "message": message,
            "fields": fields,
            "request_id": request_id,
        }
    }
    response["X-Request-ID"] = request_id
    response["Cache-Control"] = "no-store"
    return response
