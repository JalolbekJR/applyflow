import base64
import re
import secrets
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from django.utils.crypto import salted_hmac

from . import models as application_models
from .models import ApplicationDraft

SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
ETAG_PATTERN = re.compile(r'^"draft-([1-9][0-9]*)"$')
COOKIE_NAME_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
MAX_OWNERSHIP_COOKIE_VALUES = 4
MAX_CREATION_COOKIE_VALUES = 4
DUMMY_SECRET_HASH = (
    "pbkdf2_sha256$1000000$JtpraVYMlF8wH507tMtJYX$N4z09vykrQSBkmHIiG4TkTqrtAjUefMH3aEPaUHk9kk="
)


class CredentialError(Exception):
    pass


@dataclass(frozen=True)
class ParsedCredential:
    draft_id: uuid.UUID
    secret: str


def generate_credential(draft):
    secret = secrets.token_urlsafe(32)
    draft.set_secret(secret)
    return f"v1.{draft.pk}.{secret}"


def generate_creation_key() -> str:
    return secrets.token_urlsafe(32)


def creation_key_digest(creation_key: str) -> str:
    if not SECRET_PATTERN.fullmatch(creation_key):
        raise CredentialError
    return salted_hmac(
        "applyflow.draft-creation-digest.v1",
        creation_key,
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).hexdigest()


def replayable_credential(draft_id: uuid.UUID, creation_key: str) -> str:
    if not SECRET_PATTERN.fullmatch(creation_key):
        raise CredentialError
    digest = salted_hmac(
        "applyflow.draft-ownership-secret.v1",
        f"{draft_id}.{creation_key}",
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).digest()
    secret = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"v1.{draft_id}.{secret}"


def parse_credential(credential):
    if not isinstance(credential, str):
        raise CredentialError
    parts = credential.split(".")
    if len(parts) != 3 or parts[0] != "v1" or not SECRET_PATTERN.fullmatch(parts[2]):
        raise CredentialError
    try:
        draft_id = uuid.UUID(parts[1])
    except (ValueError, AttributeError, TypeError) as exc:
        raise CredentialError from exc
    return ParsedCredential(draft_id=draft_id, secret=parts[2])


def verify_credential(credential, *, now=None, queryset=None):
    parsed = parse_credential(credential)
    drafts = queryset
    if drafts is None:
        drafts = ApplicationDraft.objects.select_related("vacancy")
    try:
        draft = drafts.get(pk=parsed.draft_id)
    except ApplicationDraft.DoesNotExist:
        application_models.check_password(parsed.secret, DUMMY_SECRET_HASH)
        raise CredentialError from None
    if not draft.check_secret(parsed.secret) or not draft.is_active(now=now or timezone.now()):
        raise CredentialError
    return draft


def raw_cookie_values(request, cookie_name: str, *, maximum: int) -> list[str]:
    header = request.META.get("HTTP_COOKIE", "")
    if not header:
        return []

    values = []
    for raw_segment in header.split(";"):
        segment = raw_segment.strip()
        if not segment:
            continue
        if "=" not in segment:
            raise CredentialError
        name, value = segment.split("=", 1)
        if not COOKIE_NAME_PATTERN.fullmatch(name):
            raise CredentialError
        if name != cookie_name:
            continue
        values.append(value)
        if len(values) > maximum:
            raise CredentialError
    return values


def resolve_request_draft(request, *, required=False, now=None, queryset=None):
    credentials = raw_cookie_values(
        request,
        settings.DRAFT_COOKIE_NAME,
        maximum=MAX_OWNERSHIP_COOKIE_VALUES,
    )
    if not credentials:
        if required:
            raise CredentialError
        return None

    resolved = {}
    for credential in dict.fromkeys(credentials):
        try:
            draft = verify_credential(credential, now=now, queryset=queryset)
        except CredentialError:
            continue
        resolved[draft.pk] = draft
    if len(resolved) != 1:
        raise CredentialError
    return next(iter(resolved.values()))


def resolve_creation_key(request, *, required=True) -> str | None:
    creation_keys = raw_cookie_values(
        request,
        settings.DRAFT_CREATION_COOKIE_NAME,
        maximum=MAX_CREATION_COOKIE_VALUES,
    )
    unique_keys = list(dict.fromkeys(creation_keys))
    if not unique_keys:
        if required:
            raise CredentialError
        return None
    if len(unique_keys) != 1 or not SECRET_PATTERN.fullmatch(unique_keys[0]):
        raise CredentialError
    return unique_keys[0]


def create_or_resolve_draft(vacancy, creation_key: str, *, now=None):
    now = now or timezone.now()
    digest = creation_key_digest(creation_key)
    draft = (
        ApplicationDraft.objects.select_related("vacancy")
        .filter(creation_key_digest=digest)
        .first()
    )
    if draft is None:
        expires_at = min(
            now + settings.DRAFT_INACTIVITY_LIFETIME,
            now + settings.DRAFT_ABSOLUTE_LIFETIME,
            vacancy.closing_at or now + settings.DRAFT_ABSOLUTE_LIFETIME,
        )
        draft = ApplicationDraft(
            vacancy=vacancy,
            creation_key_digest=digest,
            last_activity_at=now,
            expires_at=expires_at,
        )
        credential = replayable_credential(draft.pk, creation_key)
        draft.set_secret(parse_credential(credential).secret)
        try:
            draft.save(force_insert=True)
            return draft, credential, True
        except IntegrityError:
            draft = (
                ApplicationDraft.objects.select_related("vacancy")
                .filter(creation_key_digest=digest)
                .first()
            )
            if draft is None:
                raise

    if now >= draft.created_at + settings.DRAFT_CREATION_KEY_LIFETIME:
        raise CredentialError
    credential = replayable_credential(draft.pk, creation_key)
    if not draft.check_secret(parse_credential(credential).secret) or not draft.is_active(now=now):
        raise CredentialError
    return draft, credential, False


def draft_etag(draft) -> str:
    return f'"draft-{draft.version}"'


def parse_if_match(value: str | None) -> int:
    match = ETAG_PATTERN.fullmatch(value or "")
    if match is None:
        raise ValueError("A quoted draft ETag is required.")
    return int(match.group(1))


def set_ownership_cookie(response, credential: str, draft, *, now=None) -> None:
    now = now or timezone.now()
    max_age = max(0, int((draft.expires_at - now).total_seconds()))
    response.set_cookie(
        settings.DRAFT_COOKIE_NAME,
        credential,
        max_age=max_age,
        path=settings.DRAFT_COOKIE_PATH,
        secure=settings.DRAFT_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
    )


def set_creation_cookie(response, creation_key: str) -> None:
    response.set_cookie(
        settings.DRAFT_CREATION_COOKIE_NAME,
        creation_key,
        max_age=int(settings.DRAFT_CREATION_KEY_LIFETIME.total_seconds()),
        path=settings.DRAFT_COOKIE_PATH,
        secure=settings.DRAFT_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
    )


def cookie_ancestor_paths(path: str) -> list[str]:
    parts = [part for part in path.split("/") if part]
    paths = ["/"]
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        paths.append(f"{current}/")
    return paths


def clear_ownership_cookie(response) -> None:
    clear_cookie_at_api_paths(
        response,
        settings.DRAFT_COOKIE_NAME,
        primary_storage_key=settings.DRAFT_COOKIE_NAME,
    )


def clear_creation_cookie(response) -> None:
    clear_cookie_at_api_paths(
        response,
        settings.DRAFT_CREATION_COOKIE_NAME,
        primary_storage_key=settings.DRAFT_CREATION_COOKIE_NAME,
    )


def clear_cookie_at_api_paths(response, cookie_name: str, *, primary_storage_key: str) -> None:
    paths = cookie_ancestor_paths(settings.DRAFT_COOKIE_PATH)
    paths.remove(settings.DRAFT_COOKIE_PATH)
    paths.insert(0, settings.DRAFT_COOKIE_PATH)
    for index, path in enumerate(paths):
        storage_key = primary_storage_key if index == 0 else f"{primary_storage_key}-clear-{index}"
        response.cookies[storage_key] = ""
        morsel = response.cookies[storage_key]
        morsel.set(cookie_name, "", "")
        morsel["max-age"] = 0
        morsel["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
        morsel["path"] = path
        morsel["secure"] = settings.DRAFT_COOKIE_SECURE
        morsel["httponly"] = True
        morsel["samesite"] = "Lax"
