from __future__ import annotations

import hashlib
import inspect
import io
import logging
import subprocess
from pathlib import Path

import pytest
from django.urls import get_resolver
from pypdf import PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import NameObject, NumberObject, StreamObject

from apps.documents import pdf_validation
from apps.documents.pdf_validation import (
    PDF_CONTENT_TYPE,
    PDF_MAX_OBJECT_VISITS,
    PDF_VALIDATION_CHUNK_SIZE,
    PDFValidationError,
    _inspect_dictionary,
    _UnsafePDFStructure,
    _walk_pdf_objects,
    normalize_pdf_display_name,
    validate_pdf_upload,
)

MAX_BYTES = 5_242_880


def blank_pdf(page_count: int = 1) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def encrypted_pdf() -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("fictional-password")
    writer.write(output)
    return output.getvalue()


def assemble_pdf(objects: list[str]) -> bytes:
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n{body}\nendobj\n".encode("ascii"))
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def raw_pdf(
    *,
    catalog_extra: str = "",
    pages_extra: str = "",
    page_extra: str = "",
    extra_objects: list[str] | None = None,
) -> bytes:
    objects = [
        f"<< /Type /Catalog /Pages 2 0 R {catalog_extra} >>",
        f"<< /Type /Pages /Kids [3 0 R] /Count 1 {pages_extra} >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] {page_extra} >>",
    ]
    objects.extend(extra_objects or [])
    return assemble_pdf(objects)


def zero_page_pdf() -> bytes:
    return assemble_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [] /Count 0 >>",
        ]
    )


def padded_to_size(pdf_bytes: bytes, target_size: int) -> bytes:
    assert len(pdf_bytes) < target_size
    padding_size = target_size - len(pdf_bytes)
    return pdf_bytes + b"\n%" + (b"a" * (padding_size - 2))


class GuardedChunkStream:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.offset = 0
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        assert 0 < size <= PDF_VALIDATION_CHUNK_SIZE
        self.read_sizes.append(size)
        if self.offset >= len(self.payload):
            return b""
        chunk = self.payload[self.offset : self.offset + min(size, 137)]
        self.offset += len(chunk)
        return chunk


def assert_validation_error(
    payload: bytes,
    *,
    code: str,
    filename: str = "avery-example-cv.pdf",
    content_type: str = PDF_CONTENT_TYPE,
    declared_size: int | None = None,
    temporary_parent: Path | None = None,
) -> PDFValidationError:
    with pytest.raises(PDFValidationError) as raised:
        validate_pdf_upload(
            io.BytesIO(payload),
            original_filename=filename,
            declared_content_type=content_type,
            declared_size=declared_size,
            temporary_parent=temporary_parent,
        )
    assert raised.value.code == code
    return raised.value


def test_valid_one_page_pdf_returns_safe_metadata_and_checksum(tmp_path):
    payload = blank_pdf()

    result = validate_pdf_upload(
        payload,
        original_filename=r"..\Avery Example CV.PDF",
        declared_content_type=PDF_CONTENT_TYPE,
        declared_size=1,
        temporary_parent=tmp_path,
    )

    assert result.original_name_display == "Avery Example CV.pdf"
    assert result.detected_content_type == PDF_CONTENT_TYPE
    assert result.size_bytes == len(payload)
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert result.page_count == 1
    assert list(tmp_path.iterdir()) == []


def test_valid_ten_page_pdf_is_accepted(tmp_path):
    result = validate_pdf_upload(
        blank_pdf(10),
        original_filename="ten-page-cv.pdf",
        declared_content_type=PDF_CONTENT_TYPE,
        temporary_parent=tmp_path,
    )

    assert result.page_count == 10


def test_zero_and_eleven_page_pdfs_are_rejected():
    assert_validation_error(zero_page_pdf(), code="unsafe_content")
    assert_validation_error(blank_pdf(11), code="unsafe_content")


def test_missing_empty_wrong_extension_mime_and_signature_are_rejected():
    with pytest.raises(PDFValidationError) as missing:
        validate_pdf_upload(
            None,
            original_filename="avery-example-cv.pdf",
            declared_content_type=PDF_CONTENT_TYPE,
        )
    assert missing.value.code == "missing_file"

    assert_validation_error(b"", code="empty")
    assert_validation_error(blank_pdf(), filename="avery-example-cv.txt", code="pdf_required")
    assert_validation_error(blank_pdf(), content_type="text/plain", code="pdf_required")
    assert_validation_error(b"noise%PDF-1.4", code="unreadable_unsupported")
    assert_validation_error(b"\n%PDF-1.4", code="unreadable_unsupported")


def test_malformed_truncated_and_encrypted_pdfs_are_rejected():
    assert_validation_error(b"%PDF-1.4\ntruncated", code="unreadable_unsupported")
    assert_validation_error(blank_pdf()[:80], code="unreadable_unsupported")
    assert_validation_error(encrypted_pdf(), code="unsafe_content")


def test_exact_five_mib_passes_and_one_byte_over_fails(tmp_path):
    exact_payload = padded_to_size(blank_pdf(), MAX_BYTES)

    result = validate_pdf_upload(
        GuardedChunkStream(exact_payload),
        original_filename="exact.pdf",
        declared_content_type=PDF_CONTENT_TYPE,
        declared_size=MAX_BYTES,
        temporary_parent=tmp_path,
    )
    assert result.size_bytes == MAX_BYTES

    oversized = GuardedChunkStream(exact_payload + b"x")
    with pytest.raises(PDFValidationError) as raised:
        validate_pdf_upload(
            oversized,
            original_filename="too-large.pdf",
            declared_content_type=PDF_CONTENT_TYPE,
            declared_size=1,
            temporary_parent=tmp_path,
        )
    assert raised.value.code == "too_large"
    assert oversized.offset <= MAX_BYTES + PDF_VALIDATION_CHUNK_SIZE
    assert list(tmp_path.iterdir()) == []


def test_declared_size_cannot_be_trusted_in_either_direction(tmp_path):
    payload = blank_pdf()

    with pytest.raises(PDFValidationError) as too_large:
        validate_pdf_upload(
            payload,
            original_filename="declared-too-large.pdf",
            declared_content_type=PDF_CONTENT_TYPE,
            declared_size=MAX_BYTES + 1,
            temporary_parent=tmp_path,
        )
    assert too_large.value.code == "too_large"

    oversized = padded_to_size(payload, MAX_BYTES) + b"x"
    assert_validation_error(
        oversized,
        code="too_large",
        declared_size=1,
        temporary_parent=tmp_path,
    )


def test_reader_uses_bounded_chunked_reads_without_unbounded_read():
    stream = GuardedChunkStream(blank_pdf())

    validate_pdf_upload(
        stream,
        original_filename="chunked.pdf",
        declared_content_type=PDF_CONTENT_TYPE,
    )

    assert stream.read_sizes
    assert all(size == PDF_VALIDATION_CHUNK_SIZE for size in stream.read_sizes)


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        (r"C:\fakepath\avery-example-cv.pdf", "avery-example-cv.pdf"),
        ("../avery\t example\ncv.pdf", "avery example cv.pdf"),
        ("evil\u202ecod.exe.pdf", "evilcod.exe.pdf"),
        ("\u200f.pdf", "cv.pdf"),
        ("Ａｖｅｒｙ　ＣＶ.PDF", "Avery CV.pdf"),
        ("a" * 200 + ".pdf", "a" * 116 + ".pdf"),
    ],
)
def test_filename_normalization_cases(original, expected):
    assert normalize_pdf_display_name(original) == expected


@pytest.mark.parametrize(
    "payload",
    [
        raw_pdf(catalog_extra="/Names << /EmbeddedFiles << /Names [(cv) 4 0 R] >> >>"),
        raw_pdf(catalog_extra="/Names << /JavaScript << /Names [(x) 4 0 R] >> >>"),
        raw_pdf(catalog_extra="/OpenAction << /S /JavaScript /JS (app.alert(1)) >>"),
        raw_pdf(catalog_extra="/AA << /O << /S /JavaScript /JS (app.alert(1)) >> >>"),
        raw_pdf(catalog_extra="/OpenAction << /S /Launch /F (calc.exe) >>"),
        raw_pdf(catalog_extra="/OpenAction << /S /URI /URI (https://example.test) >>"),
        raw_pdf(catalog_extra="/AcroForm << /Fields [4 0 R] >>"),
        raw_pdf(catalog_extra="/AcroForm << /XFA (fictional) >>"),
    ],
)
def test_catalog_names_actions_and_active_forms_are_rejected(payload):
    assert_validation_error(payload, code="unsafe_content")


@pytest.mark.parametrize(
    "subtype",
    ["/FileAttachment", "/RichMedia", "/Movie", "/Sound", "/Screen", "/3D"],
)
def test_forbidden_annotation_subtypes_are_rejected(subtype):
    payload = raw_pdf(
        page_extra="/Annots [4 0 R]",
        extra_objects=[
            f"<< /Type /Annot /Subtype {subtype} /Rect [0 0 1 1] >>",
        ],
    )

    assert_validation_error(payload, code="unsafe_content")


def test_oversized_declared_stream_length_is_rejected_without_decoding_content():
    stream = StreamObject()
    stream[NameObject("/Length")] = NumberObject(5_242_881)

    with pytest.raises(_UnsafePDFStructure):
        _inspect_dictionary(stream)


def test_cyclic_graph_and_resource_bounds_are_rejected():
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(_UnsafePDFStructure):
        _walk_pdf_objects(cyclic)

    nested: list[object] = []
    current = nested
    for _ in range(50):
        child: list[object] = []
        current.append(child)
        current = child
    with pytest.raises(_UnsafePDFStructure):
        _walk_pdf_objects(nested)

    with pytest.raises(_UnsafePDFStructure):
        _walk_pdf_objects([0] * (PDF_MAX_OBJECT_VISITS + 1))


def test_malformed_indirect_reference_is_rejected_generically():
    payload = raw_pdf(catalog_extra="/Names << /Dests << /Names [(x) 99 0 R] >> >>")

    error = assert_validation_error(payload, code="unreadable_unsupported")

    assert "99" not in error.message
    assert "xref" not in error.message.lower()


def test_parser_exception_is_mapped_to_generic_safe_error(monkeypatch):
    def raise_parser_error(*args, **kwargs):
        raise PdfReadError("internal object 4 0 offset 123")

    monkeypatch.setattr(pdf_validation, "PdfReader", raise_parser_error)

    error = assert_validation_error(blank_pdf(), code="unreadable_unsupported")

    assert error.message == "We could not read that file type. Try exporting your CV as a PDF."
    assert "object" not in error.message
    assert "123" not in error.message


def test_temporary_files_are_removed_after_success_and_failure(tmp_path):
    validate_pdf_upload(
        blank_pdf(),
        original_filename="success.pdf",
        declared_content_type=PDF_CONTENT_TYPE,
        temporary_parent=tmp_path,
    )
    assert list(tmp_path.iterdir()) == []

    assert_validation_error(
        b"%PDF-1.4\ntruncated",
        code="unreadable_unsupported",
        temporary_parent=tmp_path,
    )
    assert list(tmp_path.iterdir()) == []


def test_validation_does_not_log_sensitive_file_details(caplog):
    caplog.set_level(logging.INFO)
    error = assert_validation_error(
        b"%PDF-1.4\ntruncated",
        code="unreadable_unsupported",
        filename="../private/avery-secret-cv.pdf",
    )

    assert error.message
    assert caplog.records == []
    assert "avery-secret-cv.pdf" not in error.message
    assert "sha" not in error.message.lower()
    assert "private" not in error.message.lower()


def test_validation_does_not_extract_text_or_use_external_processes(monkeypatch):
    from pypdf._page import PageObject

    monkeypatch.setattr(
        PageObject,
        "extract_text",
        lambda *args, **kwargs: pytest.fail("text extraction must not run"),
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("external processes must not run"),
    )

    validate_pdf_upload(
        blank_pdf(),
        original_filename="no-extraction.pdf",
        declared_content_type=PDF_CONTENT_TYPE,
    )


def test_validation_module_keeps_storage_database_route_and_extraction_boundaries_static():
    source = inspect.getsource(pdf_validation)

    assert "get_document_storage" not in source
    assert "LocalPrivateDocumentStorage" not in source
    assert "FakeDocumentStorage" not in source
    assert "models" not in source
    assert "urlpatterns" not in source
    assert "extract_text" not in source
    assert "images" not in source
    assert "subprocess" not in source


@pytest.mark.django_db
def test_validation_boundary_does_not_add_storage_db_or_url_routes(django_assert_num_queries):
    before_routes = {str(pattern.pattern) for pattern in get_resolver().url_patterns}

    with django_assert_num_queries(0):
        result = validate_pdf_upload(
            blank_pdf(),
            original_filename="boundary.pdf",
            declared_content_type=PDF_CONTENT_TYPE,
        )

    after_routes = {str(pattern.pattern) for pattern in get_resolver().url_patterns}
    assert result.sha256
    assert before_routes == after_routes
