from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.cache import patch_vary_headers
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.drafts import (
    CredentialError,
    clear_creation_cookie,
    generate_creation_key,
    resolve_creation_key,
    set_creation_cookie,
)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


@never_cache
@require_GET
def csrf_bootstrap(request):
    response = JsonResponse({"csrf_token": get_token(request)})
    try:
        creation_key = resolve_creation_key(request, required=False)
    except CredentialError:
        creation_key = None
        clear_creation_cookie(response)
    if creation_key is None:
        set_creation_cookie(response, generate_creation_key())
    response["Cache-Control"] = "no-store"
    patch_vary_headers(response, ("Cookie",))
    return response
