import uuid

from django.http import Http404
from rest_framework.exceptions import ErrorDetail, NotFound, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


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
        fields = {
            key: [str(item) for item in value] if isinstance(value, list) else [str(value)]
            for key, value in response.data.items()
        }
    elif isinstance(response.data, dict):
        detail = response.data.get("detail")
        if isinstance(detail, ErrorDetail):
            code = detail.code
            message = str(detail)

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "fields": fields,
            "request_id": f"req_{uuid.uuid4().hex}",
        }
    }
    return response
