from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

import pytest
from django.test import override_settings

from apps.documents.storage import (
    DOCUMENT_STORAGE_CHUNK_SIZE,
    DocumentStorageCollision,
    DocumentStorageNotFound,
    DocumentStorageOperationError,
    FakeDocumentStorage,
    InvalidDocumentStorageKey,
    LocalPrivateDocumentStorage,
    get_document_storage,
    reset_document_storage_cache,
)
from apps.documents.storage_keys import (
    MAX_DOCUMENT_STORAGE_KEY_LENGTH,
    draft_cv_storage_key,
    validate_document_storage_key,
)

DRAFT_ID = uuid.UUID("11111111-2222-4333-8444-555555555555")
DOCUMENT_ID = uuid.UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
OTHER_DRAFT_ID = uuid.UUID("22222222-3333-4444-8555-666666666666")
OTHER_DOCUMENT_ID = uuid.UUID("bbbbbbbb-cccc-4ddd-8eee-ffffffffffff")
VALID_KEY = draft_cv_storage_key(DRAFT_ID, DOCUMENT_ID)
OTHER_KEY = draft_cv_storage_key(OTHER_DRAFT_ID, OTHER_DOCUMENT_ID)


class TrackingSource:
    def __init__(self, payload: bytes, *, fail_after_reads: int | None = None) -> None:
        self.payload = payload
        self.offset = 0
        self.read_sizes: list[int] = []
        self.fail_after_reads = fail_after_reads

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            raise AssertionError("storage must not call unbounded read()")
        self.read_sizes.append(size)
        if self.fail_after_reads is not None and len(self.read_sizes) > self.fail_after_reads:
            raise OSError("fictional stream failure")
        if self.offset >= len(self.payload):
            return b""
        chunk = self.payload[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


@pytest.fixture(params=["fake", "local"])
def storage(request, tmp_path):
    if request.param == "fake":
        return FakeDocumentStorage()
    return LocalPrivateDocumentStorage(tmp_path / "private-documents")


def stored_path(root: Path, key: str) -> Path:
    return root.joinpath(*key.split("/"))


def assert_no_temporary_files(root: Path) -> None:
    if root.exists():
        assert [
            path for path in root.rglob("*") if path.name.startswith(".") or path.suffix == ".tmp"
        ] == []


def symlink_supported(tmp_path: Path) -> bool:
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.write_text("fictional", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        return False
    return link.is_symlink()


def test_draft_cv_storage_key_is_canonical_and_contains_no_candidate_data():
    key = draft_cv_storage_key(
        uuid.UUID("ABCDEFAB-CDEF-4ABC-8DEF-ABCDEFABCDEF"),
        uuid.UUID("01234567-89AB-4CDE-8FAB-0123456789AB"),
    )

    assert (
        key
        == "drafts/abcdefab-cdef-4abc-8def-abcdefabcdef/01234567-89ab-4cde-8fab-0123456789ab.pdf"
    )
    assert "avery" not in key
    assert "example.test" not in key
    assert "\\" not in key
    assert validate_document_storage_key(key) == key


@pytest.mark.parametrize(
    ("draft_id", "document_id"),
    [
        ("11111111-2222-4333-8444-555555555555", DOCUMENT_ID),
        (DRAFT_ID, "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"),
        ("not-a-uuid", DOCUMENT_ID),
        (DRAFT_ID, None),
    ],
)
def test_draft_cv_storage_key_rejects_non_uuid_components(draft_id, document_id):
    with pytest.raises(Exception) as excinfo:
        draft_cv_storage_key(draft_id, document_id)

    assert "not-a-uuid" not in str(excinfo.value)


@pytest.mark.parametrize(
    "key",
    [
        "",
        "/drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf/",
        "drafts//11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        r"drafts\11111111-2222-4333-8444-555555555555\aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "../drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/../aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/%2e%2e/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf\x00",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf\x1f",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf\u2215",
        "C:/drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        r"\\server\share\drafts\11111111-2222-4333-8444-555555555555\aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "file://drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf?download=1",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf#fragment",
        "documents/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/extra/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.txt",
        f"drafts/{'a' * 60}/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "drafts/11111111-2222-4333-8444-555555555555/.aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf.tmp",
        "drafts/11111111-2222-4333-8444-555555555555/aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf"
        + "x" * (MAX_DOCUMENT_STORAGE_KEY_LENGTH + 1),
    ],
)
def test_invalid_storage_keys_are_rejected_before_storage_access(storage, key):
    with pytest.raises(InvalidDocumentStorageKey):
        storage.exists(key)


def test_storage_contract_round_trip_exists_delete_and_missing_delete(storage):
    assert storage.exists(VALID_KEY) is False

    storage.save(VALID_KEY, io.BytesIO(b"fictional-pdf-bytes"))

    assert storage.exists(VALID_KEY) is True
    with storage.open(VALID_KEY) as handle:
        assert handle.read() == b"fictional-pdf-bytes"

    storage.delete(VALID_KEY)
    assert storage.exists(VALID_KEY) is False
    storage.delete(VALID_KEY)
    with pytest.raises(DocumentStorageNotFound):
        storage.open(VALID_KEY)


def test_storage_contract_duplicate_save_preserves_original_bytes(storage):
    storage.save(VALID_KEY, io.BytesIO(b"original"))

    with pytest.raises(DocumentStorageCollision):
        storage.save(VALID_KEY, io.BytesIO(b"replacement"))

    with storage.open(VALID_KEY) as handle:
        assert handle.read() == b"original"


def test_storage_contract_enumerates_deterministically_and_filters_safe_prefix(storage):
    same_draft_second_key = draft_cv_storage_key(
        DRAFT_ID,
        uuid.UUID("cccccccc-dddd-4eee-8fff-000000000000"),
    )
    storage.save(OTHER_KEY, io.BytesIO(b"other"))
    storage.save(same_draft_second_key, io.BytesIO(b"second"))
    storage.save(VALID_KEY, io.BytesIO(b"first"))

    assert storage.iter_keys() == sorted([OTHER_KEY, same_draft_second_key, VALID_KEY])
    assert storage.iter_keys(prefix=f"drafts/{DRAFT_ID}/") == sorted(
        [same_draft_second_key, VALID_KEY]
    )
    assert storage.iter_keys(prefix="drafts/") == sorted(
        [OTHER_KEY, same_draft_second_key, VALID_KEY]
    )
    with pytest.raises(InvalidDocumentStorageKey):
        storage.iter_keys(prefix="../drafts/")


def test_local_adapter_uses_bounded_chunked_reads_and_no_whole_stream_buffering(tmp_path):
    storage = LocalPrivateDocumentStorage(tmp_path / "private-documents")
    payload = (b"a" * DOCUMENT_STORAGE_CHUNK_SIZE) + b"tail"
    source = TrackingSource(payload)

    storage.save(VALID_KEY, source)

    assert source.read_sizes
    assert all(size == DOCUMENT_STORAGE_CHUNK_SIZE for size in source.read_sizes)
    with storage.open(VALID_KEY) as handle:
        assert handle.read() == payload


def test_local_adapter_successful_save_leaves_no_temporary_files(tmp_path):
    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)

    storage.save(VALID_KEY, io.BytesIO(b"stored"))

    assert_no_temporary_files(root)


def test_local_adapter_source_failure_cleans_temporary_objects_and_preserves_unrelated(tmp_path):
    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)
    storage.save(OTHER_KEY, io.BytesIO(b"unrelated"))

    with pytest.raises(DocumentStorageOperationError):
        storage.save(VALID_KEY, TrackingSource(b"partial", fail_after_reads=0))

    assert storage.exists(VALID_KEY) is False
    with storage.open(OTHER_KEY) as handle:
        assert handle.read() == b"unrelated"
    assert_no_temporary_files(root)


def test_local_adapter_filesystem_failure_cleans_temporary_and_final_objects(tmp_path, monkeypatch):
    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)

    def fail_copy(_temporary_path, _target):
        raise OSError("fictional filesystem failure")

    monkeypatch.setattr(storage, "_copy_temporary_to_new_final", fail_copy)

    with pytest.raises(DocumentStorageOperationError):
        storage.save(VALID_KEY, io.BytesIO(b"partial"))

    assert storage.exists(VALID_KEY) is False
    assert_no_temporary_files(root)


def test_local_adapter_racing_collision_preserves_other_writer_bytes(tmp_path, monkeypatch):
    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)

    def simulate_racing_writer(temporary_path, target):
        target.write_bytes(b"other-writer")
        raise FileExistsError("fictional race")

    monkeypatch.setattr(storage, "_copy_temporary_to_new_final", simulate_racing_writer)

    with pytest.raises(DocumentStorageCollision):
        storage.save(VALID_KEY, io.BytesIO(b"current-writer"))

    assert stored_path(root, VALID_KEY).read_bytes() == b"other-writer"
    assert_no_temporary_files(root)


def test_local_adapter_rejects_directory_targets(tmp_path):
    root = tmp_path / "private-documents"
    target = stored_path(root, VALID_KEY)
    target.mkdir(parents=True)
    storage = LocalPrivateDocumentStorage(root)

    with pytest.raises(DocumentStorageOperationError):
        storage.exists(VALID_KEY)
    with pytest.raises(DocumentStorageOperationError):
        storage.delete(VALID_KEY)


def test_local_adapter_rejects_final_symlink_deterministically(tmp_path, monkeypatch):
    root = tmp_path / "private-documents"
    target = stored_path(root, VALID_KEY)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"not-used")
    storage = LocalPrivateDocumentStorage(root)
    original_is_symlink = Path.is_symlink

    def is_symlink(path):
        if path == target:
            return True
        return original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)

    with pytest.raises(DocumentStorageOperationError):
        storage.open(VALID_KEY)


def test_local_adapter_rejects_real_final_symlink_when_supported(tmp_path):
    if not symlink_supported(tmp_path):
        pytest.skip(
            "filesystem symlink creation is unavailable; deterministic branch test covers rejection"
        )
    root = tmp_path / "private-documents"
    target = stored_path(root, VALID_KEY)
    outside = tmp_path / "outside.pdf"
    target.parent.mkdir(parents=True)
    outside.write_bytes(b"outside")
    target.symlink_to(outside)
    storage = LocalPrivateDocumentStorage(root)

    with pytest.raises(DocumentStorageOperationError):
        storage.open(VALID_KEY)


def test_local_adapter_rejects_root_symlink_deterministically(tmp_path, monkeypatch):
    root = tmp_path / "private-documents"
    root.mkdir()
    storage = LocalPrivateDocumentStorage(root)
    original_is_symlink = Path.is_symlink

    def is_symlink(path):
        if path == root:
            return True
        return original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)

    with pytest.raises(DocumentStorageOperationError):
        storage.save(VALID_KEY, io.BytesIO(b"bytes"))


def test_local_adapter_prevents_parent_symlink_escape_when_supported(tmp_path):
    if not symlink_supported(tmp_path):
        pytest.skip(
            "filesystem symlink creation is unavailable; deterministic checks remain active"
        )
    root = tmp_path / "private-documents"
    outside = tmp_path / "outside"
    outside.mkdir()
    root.mkdir()
    (root / "drafts").symlink_to(outside, target_is_directory=True)
    storage = LocalPrivateDocumentStorage(root)

    with pytest.raises(DocumentStorageOperationError):
        storage.save(VALID_KEY, io.BytesIO(b"escape"))

    assert list(outside.iterdir()) == []


def test_local_adapter_enumeration_ignores_internal_and_noncanonical_files(tmp_path):
    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)
    storage.save(VALID_KEY, io.BytesIO(b"stored"))
    draft_dir = stored_path(root, VALID_KEY).parent
    (draft_dir / ".temporary.tmp").write_bytes(b"temporary")
    (draft_dir / "not-a-uuid.pdf").write_bytes(b"invalid")

    assert storage.iter_keys() == [VALID_KEY]


def test_local_adapter_does_not_log_paths_keys_or_contents(tmp_path, caplog):
    storage = LocalPrivateDocumentStorage(tmp_path / "private-documents")
    caplog.set_level(logging.DEBUG)

    with pytest.raises(InvalidDocumentStorageKey):
        storage.exists("../fictional-secret-key")

    assert caplog.records == []


def test_storage_interface_has_no_public_url_capability(storage):
    assert not hasattr(storage, "url")


def test_fake_adapter_failure_injection_and_duplicate_protection():
    storage = FakeDocumentStorage(fail_on_save=True)
    with pytest.raises(DocumentStorageOperationError):
        storage.save(VALID_KEY, io.BytesIO(b"bytes"))
    assert storage.iter_keys() == []

    storage = FakeDocumentStorage(fail_on_open=True)
    storage.fail_on_open = False
    storage.save(VALID_KEY, io.BytesIO(b"bytes"))
    storage.fail_on_open = True
    with pytest.raises(DocumentStorageOperationError):
        storage.open(VALID_KEY)

    storage = FakeDocumentStorage(fail_on_delete=True)
    storage.save(VALID_KEY, io.BytesIO(b"bytes"))
    with pytest.raises(DocumentStorageOperationError):
        storage.delete(VALID_KEY)
    assert storage.exists(VALID_KEY) is True


def test_document_storage_factory_selects_local_adapter_and_can_be_reset(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    with override_settings(
        DOCUMENT_STORAGE_BACKEND="local_private",
        DOCUMENT_PRIVATE_ROOT=first_root,
    ):
        reset_document_storage_cache()
        first = get_document_storage()
        assert isinstance(first, LocalPrivateDocumentStorage)
    with override_settings(
        DOCUMENT_STORAGE_BACKEND="local_private",
        DOCUMENT_PRIVATE_ROOT=second_root,
    ):
        reset_document_storage_cache()
        second = get_document_storage()
        assert isinstance(second, LocalPrivateDocumentStorage)
        assert second is not first
    reset_document_storage_cache()


def test_document_storage_factory_rejects_unknown_backend(tmp_path):
    with override_settings(DOCUMENT_STORAGE_BACKEND="fake", DOCUMENT_PRIVATE_ROOT=tmp_path):
        reset_document_storage_cache()
        with pytest.raises(DocumentStorageOperationError):
            get_document_storage()
    reset_document_storage_cache()


def test_private_storage_is_not_exposed_by_urls_or_media_settings(settings):
    from config.api_urls import urlpatterns as api_urlpatterns
    from config.urls import urlpatterns

    settings_source = Path(settings.BASE_DIR / "config" / "settings.py").read_text(encoding="utf-8")
    route_text = "\n".join(str(pattern.pattern) for pattern in [*urlpatterns, *api_urlpatterns])
    assert "static(" not in route_text
    assert "serve" not in route_text
    assert "documents/cv" in route_text
    assert getattr(settings, "MEDIA_ROOT", "") == ""
    assert "MEDIA_URL" not in settings_source
    assert "MEDIA_ROOT" not in settings_source
