from __future__ import annotations

import re
import uuid

from django.core.exceptions import SuspiciousOperation

DRAFT_CV_STORAGE_PREFIX = "drafts"
DRAFT_CV_EXTENSION = ".pdf"
MAX_DOCUMENT_STORAGE_KEY_LENGTH = len(
    "drafts/00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000000.pdf"
)
_CANONICAL_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_RESERVED_TEMP_PREFIX = "."
_RESERVED_TEMP_SUFFIX = ".tmp"


class StorageKeyError(SuspiciousOperation):
    """Raised when a document storage key is not canonical or safe."""


def draft_cv_storage_key(draft_id: uuid.UUID, document_id: uuid.UUID) -> str:
    if not isinstance(draft_id, uuid.UUID) or not isinstance(document_id, uuid.UUID):
        raise StorageKeyError("Document storage key components must be UUID values.")
    return f"{DRAFT_CV_STORAGE_PREFIX}/{draft_id}/{document_id}{DRAFT_CV_EXTENSION}"


def validate_document_storage_key(key: object) -> str:
    if not isinstance(key, str):
        raise StorageKeyError("Document storage key is invalid.")
    _reject_unsafe_key_text(key)
    parts = key.split("/")
    if len(parts) != 3:
        raise StorageKeyError("Document storage key is invalid.")

    namespace, draft_id, document_name = parts
    if namespace != DRAFT_CV_STORAGE_PREFIX:
        raise StorageKeyError("Document storage key is invalid.")
    document_id, extension = _split_document_name(document_name)
    if extension != DRAFT_CV_EXTENSION:
        raise StorageKeyError("Document storage key is invalid.")
    _validate_canonical_uuid(draft_id)
    _validate_canonical_uuid(document_id)
    return key


def validate_document_storage_prefix(prefix: object | None) -> str | None:
    if prefix is None:
        return None
    if not isinstance(prefix, str):
        raise StorageKeyError("Document storage prefix is invalid.")
    _reject_unsafe_key_text(prefix, allow_trailing_slash=True)
    if prefix == f"{DRAFT_CV_STORAGE_PREFIX}/":
        return prefix
    parts = prefix.split("/")
    if len(parts) == 3 and parts[0] == DRAFT_CV_STORAGE_PREFIX and parts[2] == "":
        _validate_canonical_uuid(parts[1])
        return prefix
    raise StorageKeyError("Document storage prefix is invalid.")


def _reject_unsafe_key_text(value: str, *, allow_trailing_slash: bool = False) -> None:
    if not value or len(value) > MAX_DOCUMENT_STORAGE_KEY_LENGTH:
        raise StorageKeyError("Document storage key is invalid.")
    if not value.isascii():
        raise StorageKeyError("Document storage key is invalid.")
    if value.startswith("/") or (value.endswith("/") and not allow_trailing_slash):
        raise StorageKeyError("Document storage key is invalid.")
    if (
        "//" in value
        or "\\" in value
        or "\x00" in value
        or "%" in value
        or "?" in value
        or "#" in value
        or ":" in value
    ):
        raise StorageKeyError("Document storage key is invalid.")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise StorageKeyError("Document storage key is invalid.")
    if any(segment in {"", ".", ".."} for segment in value.split("/")) and not (
        allow_trailing_slash and value.endswith("/") and "" not in value[:-1].split("/")
    ):
        raise StorageKeyError("Document storage key is invalid.")
    if any(
        segment.startswith(_RESERVED_TEMP_PREFIX) or segment.endswith(_RESERVED_TEMP_SUFFIX)
        for segment in value.split("/")
        if segment
    ):
        raise StorageKeyError("Document storage key is invalid.")


def _split_document_name(document_name: str) -> tuple[str, str]:
    if not document_name.endswith(DRAFT_CV_EXTENSION):
        raise StorageKeyError("Document storage key is invalid.")
    return document_name[: -len(DRAFT_CV_EXTENSION)], DRAFT_CV_EXTENSION


def _validate_canonical_uuid(value: str) -> None:
    if not _CANONICAL_UUID_RE.fullmatch(value):
        raise StorageKeyError("Document storage key is invalid.")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise StorageKeyError("Document storage key is invalid.") from exc
    if str(parsed) != value:
        raise StorageKeyError("Document storage key is invalid.")
