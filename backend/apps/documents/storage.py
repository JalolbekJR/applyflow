from __future__ import annotations

import io
import os
import secrets
import stat
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Protocol

from django.conf import settings

from .storage_keys import (
    StorageKeyError,
    validate_document_storage_key,
    validate_document_storage_prefix,
)

DOCUMENT_STORAGE_CHUNK_SIZE = 64 * 1024


class DocumentStorageError(Exception):
    """Base class for safe document storage boundary errors."""


class InvalidDocumentStorageKey(DocumentStorageError):
    """Raised when a storage key is not canonical."""


class DocumentStorageCollision(DocumentStorageError):
    """Raised when a save would overwrite an existing document."""


class DocumentStorageNotFound(DocumentStorageError):
    """Raised when a canonical key has no stored regular document."""


class DocumentStorageOperationError(DocumentStorageError):
    """Raised when storage cannot safely complete an operation."""


class DocumentStorage(Protocol):
    def save(self, key: str, source: BinaryIO) -> None: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...

    def iter_keys(self, prefix: str | None = None) -> list[str]: ...


def safe_storage_key(key: object) -> str:
    try:
        return validate_document_storage_key(key)
    except StorageKeyError as exc:
        raise InvalidDocumentStorageKey("Document storage key is invalid.") from exc


def safe_storage_prefix(prefix: object | None) -> str | None:
    try:
        return validate_document_storage_prefix(prefix)
    except StorageKeyError as exc:
        raise InvalidDocumentStorageKey("Document storage prefix is invalid.") from exc


class LocalPrivateDocumentStorage:
    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        if not self._root.is_absolute():
            raise DocumentStorageOperationError("Document storage is not configured safely.")

    def save(self, key: str, source: BinaryIO) -> None:
        validated_key = safe_storage_key(key)
        target = self._path_for_key(validated_key, create_parent=True)
        if target.is_symlink() or target.exists():
            if target.is_file() and not target.is_symlink():
                raise DocumentStorageCollision("Document already exists.")
            raise DocumentStorageOperationError("Document storage target is unsafe.")

        temporary_path = self._temporary_path(target.parent, target.name)
        try:
            self._write_source_to_temporary(source, temporary_path)
            self._copy_temporary_to_new_final(temporary_path, target)
        except FileExistsError as exc:
            raise DocumentStorageCollision("Document already exists.") from exc
        except DocumentStorageError:
            raise
        except OSError as exc:
            raise DocumentStorageOperationError("Document storage operation failed.") from exc
        finally:
            self._unlink_if_present(temporary_path)

    def open(self, key: str) -> BinaryIO:
        target = self._path_for_key(safe_storage_key(key), create_parent=False)
        if not target.exists():
            raise DocumentStorageNotFound("Document was not found.")
        if target.is_symlink():
            raise DocumentStorageOperationError("Document storage target is unsafe.")
        try:
            descriptor = self._open_regular_descriptor(target)
        except FileNotFoundError as exc:
            raise DocumentStorageNotFound("Document was not found.") from exc
        except OSError as exc:
            raise DocumentStorageOperationError("Document storage operation failed.") from exc
        return os.fdopen(descriptor, "rb")

    def delete(self, key: str) -> None:
        target = self._path_for_key(safe_storage_key(key), create_parent=False)
        if not target.exists():
            return
        if target.is_symlink() or not target.is_file():
            raise DocumentStorageOperationError("Document storage target is unsafe.")
        try:
            target.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise DocumentStorageOperationError("Document storage operation failed.") from exc

    def exists(self, key: str) -> bool:
        target = self._path_for_key(safe_storage_key(key), create_parent=False)
        if not target.exists():
            return False
        if target.is_symlink() or not target.is_file():
            raise DocumentStorageOperationError("Document storage target is unsafe.")
        return True

    def iter_keys(self, prefix: str | None = None) -> list[str]:
        validated_prefix = safe_storage_prefix(prefix)
        root = self._existing_safe_root()
        if root is None:
            return []
        drafts_root = root / "drafts"
        if not drafts_root.exists():
            return []
        if drafts_root.is_symlink() or not drafts_root.is_dir():
            raise DocumentStorageOperationError("Document storage namespace is unsafe.")

        keys: list[str] = []
        for draft_dir in sorted(drafts_root.iterdir(), key=lambda item: item.name):
            if draft_dir.is_symlink() or not draft_dir.is_dir():
                continue
            for document_path in sorted(draft_dir.iterdir(), key=lambda item: item.name):
                if document_path.is_symlink() or not document_path.is_file():
                    continue
                if self._is_internal_temporary_name(document_path.name):
                    continue
                candidate_key = f"drafts/{draft_dir.name}/{document_path.name}"
                try:
                    canonical_key = safe_storage_key(candidate_key)
                except InvalidDocumentStorageKey:
                    continue
                if validated_prefix is None or canonical_key.startswith(validated_prefix):
                    keys.append(canonical_key)
        return keys

    def _path_for_key(self, key: str, *, create_parent: bool) -> Path:
        root = self._ensure_root()
        parts = key.split("/")
        target = root.joinpath(*parts)
        self._ensure_contained(target)
        if create_parent:
            self._ensure_safe_directory(target.parent)
        else:
            self._ensure_existing_parent_safe(target.parent)
        self._ensure_contained(target)
        return target

    def _ensure_root(self) -> Path:
        if self._root.exists():
            if self._root.is_symlink() or not self._root.is_dir():
                raise DocumentStorageOperationError("Document storage root is unsafe.")
        else:
            try:
                self._root.mkdir(mode=0o700, parents=True)
            except OSError as exc:
                raise DocumentStorageOperationError("Document storage operation failed.") from exc
        self._apply_private_directory_permissions(self._root)
        return self._resolved_root()

    def _existing_safe_root(self) -> Path | None:
        if not self._root.exists():
            return None
        if self._root.is_symlink() or not self._root.is_dir():
            raise DocumentStorageOperationError("Document storage root is unsafe.")
        return self._resolved_root()

    def _resolved_root(self) -> Path:
        try:
            resolved = self._root.resolve(strict=True)
        except OSError as exc:
            raise DocumentStorageOperationError("Document storage root is unsafe.") from exc
        if resolved.anchor == str(resolved):
            raise DocumentStorageOperationError("Document storage root is unsafe.")
        return resolved

    def _ensure_safe_directory(self, directory: Path) -> None:
        root = self._resolved_root()
        if directory == root:
            return
        self._ensure_contained(directory)
        self._ensure_safe_directory(directory.parent)
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir():
                raise DocumentStorageOperationError("Document storage directory is unsafe.")
        else:
            try:
                directory.mkdir(mode=0o700)
            except FileExistsError as exc:
                if directory.is_symlink() or not directory.is_dir():
                    raise DocumentStorageOperationError(
                        "Document storage directory is unsafe."
                    ) from exc
            except OSError as exc:
                raise DocumentStorageOperationError("Document storage operation failed.") from exc
        self._apply_private_directory_permissions(directory)
        self._ensure_contained(directory)

    def _ensure_existing_parent_safe(self, directory: Path) -> None:
        root = self._resolved_root()
        current = root
        if current == directory:
            return
        try:
            relative_parts = directory.relative_to(root).parts
        except ValueError as exc:
            raise DocumentStorageOperationError("Document storage target is unsafe.") from exc
        for part in relative_parts:
            current = current / part
            if current.exists():
                if current.is_symlink() or not current.is_dir():
                    raise DocumentStorageOperationError("Document storage directory is unsafe.")
                self._ensure_contained(current)

    def _ensure_contained(self, path: Path) -> None:
        root = self._resolved_root()
        try:
            path.resolve(strict=False).relative_to(root)
        except (OSError, ValueError) as exc:
            raise DocumentStorageOperationError("Document storage target is unsafe.") from exc

    def _temporary_path(self, parent: Path, final_name: str) -> Path:
        for _ in range(16):
            token = secrets.token_urlsafe(18)
            candidate = parent / f".{final_name}.{token}.tmp"
            if not candidate.exists() and not candidate.is_symlink():
                return candidate
        raise DocumentStorageOperationError("Document storage operation failed.")

    def _write_source_to_temporary(self, source: BinaryIO, temporary_path: Path) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        descriptor = os.open(temporary_path, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                while True:
                    chunk = source.read(DOCUMENT_STORAGE_CHUNK_SIZE)
                    if chunk == b"":
                        break
                    if not isinstance(chunk, bytes):
                        raise DocumentStorageOperationError("Document storage source is invalid.")
                    handle.write(chunk)
            self._apply_private_file_permissions(temporary_path)
        except Exception:
            self._unlink_if_present(temporary_path)
            raise

    def _copy_temporary_to_new_final(self, temporary_path: Path, target: Path) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        descriptor = os.open(target, flags, 0o600)
        try:
            with temporary_path.open("rb") as source, os.fdopen(descriptor, "wb") as destination:
                while True:
                    chunk = source.read(DOCUMENT_STORAGE_CHUNK_SIZE)
                    if chunk == b"":
                        break
                    destination.write(chunk)
            self._apply_private_file_permissions(target)
        except Exception:
            self._unlink_regular_file_if_present(target)
            raise

    def _open_regular_descriptor(self, target: Path) -> int:
        flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags)
        try:
            mode = os.fstat(descriptor).st_mode
            if not stat.S_ISREG(mode):
                raise DocumentStorageOperationError("Document storage target is unsafe.")
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def _unlink_if_present(self, path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise DocumentStorageOperationError("Document storage operation failed.") from exc

    def _unlink_regular_file_if_present(self, path: Path) -> None:
        if not path.exists() or path.is_symlink():
            return
        if path.is_file():
            self._unlink_if_present(path)

    def _apply_private_directory_permissions(self, path: Path) -> None:
        if os.name == "posix":
            try:
                path.chmod(0o700)
            except OSError as exc:
                raise DocumentStorageOperationError("Document storage operation failed.") from exc

    def _apply_private_file_permissions(self, path: Path) -> None:
        if os.name == "posix":
            try:
                path.chmod(0o600)
            except OSError as exc:
                raise DocumentStorageOperationError("Document storage operation failed.") from exc

    def _is_internal_temporary_name(self, name: str) -> bool:
        return name.startswith(".") or name.endswith(".tmp")


class FakeDocumentStorage:
    def __init__(
        self,
        *,
        fail_on_save: bool = False,
        fail_on_open: bool = False,
        fail_on_delete: bool = False,
    ) -> None:
        self._objects: dict[str, bytes] = {}
        self.fail_on_save = fail_on_save
        self.fail_on_open = fail_on_open
        self.fail_on_delete = fail_on_delete

    def save(self, key: str, source: BinaryIO) -> None:
        validated_key = safe_storage_key(key)
        if self.fail_on_save:
            raise DocumentStorageOperationError("Document storage operation failed.")
        if validated_key in self._objects:
            raise DocumentStorageCollision("Document already exists.")
        chunks: list[bytes] = []
        while True:
            chunk = source.read(DOCUMENT_STORAGE_CHUNK_SIZE)
            if chunk == b"":
                break
            if not isinstance(chunk, bytes):
                raise DocumentStorageOperationError("Document storage source is invalid.")
            chunks.append(chunk)
        self._objects[validated_key] = b"".join(chunks)

    def open(self, key: str) -> BinaryIO:
        validated_key = safe_storage_key(key)
        if self.fail_on_open:
            raise DocumentStorageOperationError("Document storage operation failed.")
        try:
            return io.BytesIO(self._objects[validated_key])
        except KeyError as exc:
            raise DocumentStorageNotFound("Document was not found.") from exc

    def delete(self, key: str) -> None:
        validated_key = safe_storage_key(key)
        if self.fail_on_delete:
            raise DocumentStorageOperationError("Document storage operation failed.")
        self._objects.pop(validated_key, None)

    def exists(self, key: str) -> bool:
        return safe_storage_key(key) in self._objects

    def iter_keys(self, prefix: str | None = None) -> list[str]:
        validated_prefix = safe_storage_prefix(prefix)
        keys = sorted(self._objects)
        if validated_prefix is None:
            return keys
        return [key for key in keys if key.startswith(validated_prefix)]


@lru_cache(maxsize=1)
def get_document_storage() -> DocumentStorage:
    if settings.DOCUMENT_STORAGE_BACKEND == "local_private":
        return LocalPrivateDocumentStorage(settings.DOCUMENT_PRIVATE_ROOT)
    raise DocumentStorageOperationError("Document storage backend is not configured safely.")


def reset_document_storage_cache() -> None:
    get_document_storage.cache_clear()
