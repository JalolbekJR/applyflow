from __future__ import annotations

import hashlib
import io
import os
import re
import tempfile
import unicodedata
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from django.conf import settings
from pypdf import PdfReader
from pypdf.errors import EmptyFileError, PdfReadError, PdfReadWarning, PyPdfError
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject

PDF_CONTENT_TYPE = "application/pdf"
PDF_EXTENSION = ".pdf"
PDF_SIGNATURE = b"%PDF-"
PDF_MAX_PAGES = 10
PDF_VALIDATION_CHUNK_SIZE = 64 * 1024
PDF_MAX_OBJECT_VISITS = 2_000
PDF_MAX_GRAPH_DEPTH = 40
PDF_MAX_CONTAINER_ITEMS = 1_000
PDF_MAX_WARNINGS = 20
PDF_MAX_STREAM_DECLARED_LENGTH = 5_242_880
PDF_DISPLAY_NAME_MAX_LENGTH = 120
PDF_FALLBACK_DISPLAY_NAME = "cv.pdf"

_WHITESPACE_RE = re.compile(r"\s+")
_INVISIBLE_FORMAT_CODEPOINTS = {
    "\u061c",
    "\u200b",
    "\u200c",
    "\u200d",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\ufeff",
}
_FORBIDDEN_KEYS = {
    "/AA",
    "/EmbeddedFiles",
    "/JS",
    "/JavaScript",
    "/Launch",
    "/OpenAction",
    "/RichMedia",
    "/XFA",
}
_FORBIDDEN_ACTIONS = {
    "/GoTo3DView",
    "/GoToE",
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Movie",
    "/Rendition",
    "/SetOCGState",
    "/Sound",
    "/SubmitForm",
    "/URI",
}
_FORBIDDEN_ANNOTATION_SUBTYPES = {
    "/3D",
    "/FileAttachment",
    "/Movie",
    "/RichMedia",
    "/Screen",
    "/Sound",
}


@dataclass(frozen=True)
class PDFValidationResult:
    original_name_display: str
    detected_content_type: str
    size_bytes: int
    sha256: str
    page_count: int


@dataclass(frozen=True)
class ValidatedPDFUpload:
    metadata: PDFValidationResult
    _path: Path

    def open(self) -> BinaryIO:
        return self._path.open("rb")


class PDFValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MissingPDFFile(PDFValidationError):
    def __init__(self) -> None:
        super().__init__("missing_file", "Upload a PDF file under 5 MB.")


class PDFRequired(PDFValidationError):
    def __init__(self) -> None:
        super().__init__("pdf_required", "Upload a PDF file under 5 MB.")


class EmptyPDFFile(PDFValidationError):
    def __init__(self) -> None:
        super().__init__("empty", "Upload a PDF file under 5 MB.")


class PDFTooLarge(PDFValidationError):
    def __init__(self) -> None:
        super().__init__("too_large", "Upload a PDF file under 5 MB.")


class UnreadablePDF(PDFValidationError):
    def __init__(self) -> None:
        super().__init__(
            "unreadable_unsupported",
            "We could not read that file type. Try exporting your CV as a PDF.",
        )


class UnsafePDFContent(PDFValidationError):
    def __init__(self) -> None:
        super().__init__(
            "unsafe_content",
            "We could not accept that PDF. Try exporting a simple PDF without active content.",
        )


class _UnsafePDFStructure(Exception):
    pass


class _UnreadablePDFStructure(Exception):
    pass


def validate_pdf_upload(
    source: bytes | bytearray | memoryview | BinaryIO | None,
    *,
    original_filename: str | None,
    declared_content_type: str | None,
    declared_size: int | None = None,
    max_bytes: int | None = None,
    temporary_parent: Path | str | None = None,
) -> PDFValidationResult:
    if source is None:
        raise MissingPDFFile()

    with validated_pdf_upload(
        source,
        original_filename=original_filename,
        declared_content_type=declared_content_type,
        declared_size=declared_size,
        max_bytes=max_bytes,
        temporary_parent=temporary_parent,
    ) as validated:
        return validated.metadata


@contextmanager
def validated_pdf_upload(
    source: bytes | bytearray | memoryview | BinaryIO | None,
    *,
    original_filename: str | None,
    declared_content_type: str | None,
    declared_size: int | None = None,
    max_bytes: int | None = None,
    temporary_parent: Path | str | None = None,
):
    if source is None:
        raise MissingPDFFile()

    limit = _configured_max_upload_bytes(max_bytes)
    if declared_size is not None and declared_size > limit:
        raise PDFTooLarge()
    if not _has_pdf_extension(original_filename):
        raise PDFRequired()
    if declared_content_type != PDF_CONTENT_TYPE:
        raise PDFRequired()

    display_name = normalize_pdf_display_name(original_filename)
    stream = _as_binary_stream(source)
    with _private_temporary_directory(temporary_parent) as temporary_directory:
        temporary_path = _temporary_pdf_path(temporary_directory)
        try:
            size_bytes, sha256 = _copy_bounded_upload(stream, temporary_path, limit)
            page_count = _inspect_pdf_file(temporary_path)
            yield ValidatedPDFUpload(
                metadata=PDFValidationResult(
                    original_name_display=display_name,
                    detected_content_type=PDF_CONTENT_TYPE,
                    size_bytes=size_bytes,
                    sha256=sha256,
                    page_count=page_count,
                ),
                _path=temporary_path,
            )
        finally:
            _unlink_temporary_file(temporary_path)


def normalize_pdf_display_name(original_filename: str | None) -> str:
    if not original_filename:
        return PDF_FALLBACK_DISPLAY_NAME

    basename = original_filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    normalized = unicodedata.normalize("NFKC", basename)
    cleaned = "".join(_safe_display_character(character) for character in normalized)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return PDF_FALLBACK_DISPLAY_NAME

    stem, extension = _split_pdf_display_extension(cleaned)
    stem = stem.strip(" .")
    if not stem:
        return PDF_FALLBACK_DISPLAY_NAME
    display = f"{stem}{extension}"
    if len(display) <= PDF_DISPLAY_NAME_MAX_LENGTH:
        return display

    max_stem_length = PDF_DISPLAY_NAME_MAX_LENGTH - len(extension)
    stem = stem[:max_stem_length].rstrip(" .")
    return f"{stem or PDF_FALLBACK_DISPLAY_NAME[:-4]}{extension}"


def _configured_max_upload_bytes(max_bytes: int | None) -> int:
    if max_bytes is not None:
        return max_bytes
    return settings.DOCUMENT_MAX_UPLOAD_BYTES


def _has_pdf_extension(original_filename: str | None) -> bool:
    if not original_filename:
        return False
    basename = original_filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    normalized = unicodedata.normalize("NFKC", basename)
    return normalized.lower().endswith(PDF_EXTENSION)


def _safe_display_character(character: str) -> str:
    if character in {"\t", "\n", "\r", "\f", "\v"}:
        return " "
    ordinal = ord(character)
    if ordinal < 32 or ordinal == 127:
        return ""
    if character in _INVISIBLE_FORMAT_CODEPOINTS:
        return ""
    if unicodedata.category(character) == "Cf":
        return ""
    return character


def _split_pdf_display_extension(name: str) -> tuple[str, str]:
    if name.lower().endswith(PDF_EXTENSION):
        return name[: -len(PDF_EXTENSION)], PDF_EXTENSION
    return name, PDF_EXTENSION


def _as_binary_stream(source: bytes | bytearray | memoryview | BinaryIO) -> BinaryIO:
    if isinstance(source, bytes | bytearray | memoryview):
        return io.BytesIO(bytes(source))
    read = getattr(source, "read", None)
    if not callable(read):
        raise MissingPDFFile()
    return source


def _copy_bounded_upload(source: BinaryIO, destination: Path, limit: int) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    signature = bytearray()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            while True:
                chunk = source.read(PDF_VALIDATION_CHUNK_SIZE)
                if chunk == b"":
                    break
                if not isinstance(chunk, bytes):
                    raise UnreadablePDF()
                size += len(chunk)
                if size > limit:
                    raise PDFTooLarge()
                if len(signature) < len(PDF_SIGNATURE):
                    missing = len(PDF_SIGNATURE) - len(signature)
                    signature.extend(chunk[:missing])
                digest.update(chunk)
                handle.write(chunk)
        _apply_private_file_permissions(destination)
    except Exception:
        _unlink_temporary_file(destination)
        raise

    if size == 0:
        raise EmptyPDFFile()
    if bytes(signature) != PDF_SIGNATURE:
        raise UnreadablePDF()
    return size, digest.hexdigest()


def _inspect_pdf_file(path: Path) -> int:
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", PdfReadWarning)
            with path.open("rb") as handle:
                reader = PdfReader(handle, strict=True)
                if reader.is_encrypted:
                    raise _UnsafePDFStructure()
                page_count = len(reader.pages)
                if page_count < 1 or page_count > PDF_MAX_PAGES:
                    raise _UnsafePDFStructure()
                _inspect_reader_structure(reader)
            warning_count = sum(
                issubclass(warning.category, PdfReadWarning) for warning in caught_warnings
            )
            if warning_count > PDF_MAX_WARNINGS:
                raise _UnreadablePDFStructure()
    except EmptyFileError as exc:
        raise EmptyPDFFile() from exc
    except _UnsafePDFStructure as exc:
        raise UnsafePDFContent() from exc
    except _UnreadablePDFStructure as exc:
        raise UnreadablePDF() from exc
    except (PdfReadError, PyPdfError, ValueError, OSError, RecursionError) as exc:
        raise UnreadablePDF() from exc
    return page_count


def _inspect_reader_structure(reader: PdfReader) -> None:
    root = reader.root_object
    if not isinstance(root, DictionaryObject) or "/Pages" not in root:
        raise _UnsafePDFStructure()
    if "/AcroForm" in root:
        raise _UnsafePDFStructure()

    roots: list[object] = [reader.trailer, root]
    for page in reader.pages:
        roots.append(page)
    _walk_pdf_objects(roots)


def _walk_pdf_objects(roots: list[object]) -> None:
    visits = 0
    visited_indirects: set[tuple[int, int]] = set()
    visited_containers: set[int] = set()
    stack: list[tuple[object, int, frozenset[int], frozenset[tuple[int, int]]]] = [
        (root, 0, frozenset(), frozenset()) for root in roots
    ]

    while stack:
        item, depth, container_ancestors, indirect_ancestors = stack.pop()
        if depth > PDF_MAX_GRAPH_DEPTH:
            raise _UnsafePDFStructure()
        visits += 1
        if visits > PDF_MAX_OBJECT_VISITS:
            raise _UnsafePDFStructure()

        if isinstance(item, IndirectObject):
            key = (item.idnum, item.generation)
            if key in indirect_ancestors:
                continue
            if key in visited_indirects:
                continue
            visited_indirects.add(key)
            try:
                stack.append(
                    (item.get_object(), depth + 1, container_ancestors, indirect_ancestors | {key})
                )
            except (PdfReadError, PyPdfError, ValueError, OSError, RecursionError) as exc:
                raise _UnreadablePDFStructure() from exc
            continue

        if isinstance(item, DictionaryObject):
            container_id = id(item)
            if container_id in container_ancestors:
                raise _UnsafePDFStructure()
            if container_id in visited_containers:
                continue
            visited_containers.add(container_id)
            next_container_ancestors = container_ancestors | {container_id}
            _inspect_dictionary(item)
            values = list(item.values())
            if len(values) > PDF_MAX_CONTAINER_ITEMS:
                raise _UnsafePDFStructure()
            stack.extend(
                (value, depth + 1, next_container_ancestors, indirect_ancestors) for value in values
            )
            continue

        if isinstance(item, ArrayObject | list | tuple):
            container_id = id(item)
            if container_id in container_ancestors:
                raise _UnsafePDFStructure()
            if container_id in visited_containers:
                continue
            visited_containers.add(container_id)
            if len(item) > PDF_MAX_CONTAINER_ITEMS:
                raise _UnsafePDFStructure()
            next_container_ancestors = container_ancestors | {container_id}
            stack.extend(
                (value, depth + 1, next_container_ancestors, indirect_ancestors) for value in item
            )


def _inspect_dictionary(item: DictionaryObject) -> None:
    keys = {str(key) for key in item}
    if keys & _FORBIDDEN_KEYS:
        raise _UnsafePDFStructure()
    if "/AcroForm" in keys:
        raise _UnsafePDFStructure()
    subtype = _name_value(item.get("/Subtype"))
    if subtype in _FORBIDDEN_ANNOTATION_SUBTYPES:
        raise _UnsafePDFStructure()
    action_type = _name_value(item.get("/S"))
    if action_type in _FORBIDDEN_ACTIONS:
        raise _UnsafePDFStructure()
    stream_length = item.get("/Length")
    if isinstance(item, StreamObject) and isinstance(stream_length, int):
        if stream_length > PDF_MAX_STREAM_DECLARED_LENGTH:
            raise _UnsafePDFStructure()


def _name_value(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _private_temporary_directory(
    temporary_parent: Path | str | None,
) -> tempfile.TemporaryDirectory[str]:
    temporary = tempfile.TemporaryDirectory(prefix="applyflow-pdf-", dir=temporary_parent)
    if os.name == "posix":
        try:
            Path(temporary.name).chmod(0o700)
        except OSError as exc:
            temporary.cleanup()
            raise UnreadablePDF() from exc
    return temporary


def _temporary_pdf_path(temporary_directory: str) -> Path:
    return Path(temporary_directory) / "upload.bin"


def _apply_private_file_permissions(path: Path) -> None:
    if os.name == "posix":
        path.chmod(0o600)


def _unlink_temporary_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
