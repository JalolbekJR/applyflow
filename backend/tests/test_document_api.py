import hashlib
import io
import uuid

import pytest
from django.apps import apps
from django.db import IntegrityError
from django.test import Client
from django.test.client import MULTIPART_CONTENT, encode_multipart
from django.utils import timezone
from pypdf import PdfWriter

from apps.documents.storage import FakeDocumentStorage


@pytest.fixture
def vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="document-api-engineer",
        title="Document API Engineer",
        summary="Build private upload APIs.",
        description="A fictional vacancy used for document API tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


@pytest.fixture
def fake_storage(monkeypatch):
    storage = FakeDocumentStorage()
    monkeypatch.setattr("apps.documents.services.get_document_storage", lambda: storage)
    return storage


def pdf_bytes(page_count=1):
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def csrf_client():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/csrf/")
    return client, response.json()["csrf_token"]


def create_draft(client, vacancy, token):
    return client.post(
        "/api/v1/application-drafts/",
        {"vacancy_slug": vacancy.slug},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def multipart_put(client, path, payload, token, *, version=1, content_type=MULTIPART_CONTENT):
    return client.put(
        path,
        encode_multipart("BoUnDaRyStRiNg", payload),
        content_type=content_type,
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


def upload_file(name="avery-example-cv.pdf", content=None, content_type="application/pdf"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content or pdf_bytes(), content_type=content_type)


def assert_error(response, status, code):
    assert response.status_code == status
    payload = response.json()
    assert payload["error"]["code"] == code
    assert payload["error"]["request_id"].startswith("req_")
    assert response["Cache-Control"] == "no-store"


def document_path(draft_id):
    return f"/api/v1/application-drafts/{draft_id}/documents/cv/"


@pytest.mark.django_db
def test_get_cv_metadata_returns_aggregate_without_renewing(vacancy, fake_storage):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    original_activity = draft.last_activity_at
    original_expiry = draft.expires_at
    ApplicationDocument = apps.get_model("documents.ApplicationDocument")
    ApplicationDocument.objects.create(
        draft=draft,
        original_name_display="avery-example-cv.pdf",
        storage_key=f"drafts/{draft.pk}/{uuid.uuid4()}.pdf",
        detected_content_type="application/pdf",
        size=1234,
        sha256="b" * 64,
    )

    response = client.get(document_path(draft.pk))

    assert response.status_code == 200
    assert response["ETag"] == created["ETag"]
    assert "applyflow_draft" not in response.cookies
    payload = response.json()["draft"]["document"]
    assert payload == {
        "original_name_display": "avery-example-cv.pdf",
        "detected_content_type": "application/pdf",
        "size": 1234,
        "uploaded_at": payload["uploaded_at"],
    }
    serialized = response.content.decode()
    for hidden in ("storage_key", "sha256", "storage_deleted_at", "deleted_at", "page_count"):
        assert hidden not in serialized
    draft.refresh_from_db()
    assert draft.last_activity_at == original_activity
    assert draft.expires_at == original_expiry


@pytest.mark.django_db
def test_first_upload_stores_validated_bytes_checksum_and_safe_metadata(vacancy, fake_storage):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    credential = created.cookies["applyflow_draft"].value
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    payload = pdf_bytes()

    response = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("../Avery CV.PDF", payload)},
        token,
    )

    assert response.status_code == 201
    assert response["ETag"] == '"draft-2"'
    assert response.cookies["applyflow_draft"].value == credential
    document = apps.get_model("documents.ApplicationDocument").objects.get()
    assert document.draft_id == draft.pk
    assert document.application_id is None
    assert document.original_name_display == "Avery CV.pdf"
    assert document.detected_content_type == "application/pdf"
    assert document.size == len(payload)
    assert document.sha256 == hashlib.sha256(payload).hexdigest()
    assert document.deleted_at is None
    assert document.storage_deleted_at is None
    assert document.storage_key == f"drafts/{draft.pk}/{document.pk}.pdf"
    with fake_storage.open(document.storage_key) as stored:
        stored_bytes = stored.read()
    assert hashlib.sha256(stored_bytes).hexdigest() == document.sha256
    serialized = response.content.decode()
    assert document.storage_key not in serialized
    assert document.sha256 not in serialized


@pytest.mark.django_db
def test_replacement_retires_old_after_new_commit_and_deletes_old_storage(
    vacancy, fake_storage, django_capture_on_commit_callbacks
):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    first = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("first.pdf", pdf_bytes())},
        token,
    )
    assert first.status_code == 201
    old = apps.get_model("documents.ApplicationDocument").objects.get()

    with django_capture_on_commit_callbacks(execute=True):
        replacement = multipart_put(
            client,
            document_path(draft.pk),
            {"file": upload_file("second.pdf", pdf_bytes())},
            token,
            version=2,
        )

    assert replacement.status_code == 200
    old.refresh_from_db()
    new = apps.get_model("documents.ApplicationDocument").objects.get(deleted_at__isnull=True)
    assert old.pk != new.pk
    assert old.original_name_display == ""
    assert old.deleted_at is not None
    assert old.storage_deleted_at is not None
    assert not fake_storage.exists(old.storage_key)
    assert fake_storage.exists(new.storage_key)
    assert replacement["ETag"] == '"draft-3"'


@pytest.mark.django_db
def test_delete_logically_removes_and_physical_failure_stays_retryable(vacancy, monkeypatch):
    storage = FakeDocumentStorage(fail_on_delete=True)
    monkeypatch.setattr("apps.documents.services.get_document_storage", lambda: storage)
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    upload = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("delete-me.pdf", pdf_bytes())},
        token,
    )
    assert upload.status_code == 201
    document = apps.get_model("documents.ApplicationDocument").objects.get()

    response = client.delete(
        document_path(draft.pk),
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-2"',
    )

    assert response.status_code == 204
    assert response["ETag"] == '"draft-3"'
    document.refresh_from_db()
    assert document.deleted_at is not None
    assert document.original_name_display == ""
    assert document.storage_deleted_at is None
    assert storage.exists(document.storage_key)
    aggregate = client.get(document_path(draft.pk))
    assert aggregate.json()["draft"]["document"] is None


@pytest.mark.django_db
def test_authorization_and_stale_prechecks_happen_before_validator_or_storage(
    vacancy, fake_storage, monkeypatch
):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    def fail_validator(*args, **kwargs):
        raise AssertionError("validator must not run")

    monkeypatch.setattr("apps.documents.views.validated_pdf_upload", fail_validator)
    missing_cookie = Client(enforce_csrf_checks=True)
    missing_cookie.cookies["csrftoken"] = client.cookies["csrftoken"].value
    unauthorized = multipart_put(
        missing_cookie,
        document_path(draft.pk),
        {"file": upload_file("blocked.pdf", pdf_bytes())},
        token,
    )
    stale = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("blocked.pdf", pdf_bytes())},
        token,
        version=2,
    )
    missing_version = client.put(
        document_path(draft.pk),
        encode_multipart("BoUnDaRyStRiNg", {"file": upload_file("blocked.pdf", pdf_bytes())}),
        content_type=MULTIPART_CONTENT,
        HTTP_X_CSRFTOKEN=token,
    )

    assert_error(unauthorized, 404, "draft_unavailable")
    assert_error(stale, 409, "draft_conflict")
    assert_error(missing_version, 428, "draft_version_required")
    assert fake_storage.iter_keys() == []


@pytest.mark.django_db
def test_multipart_shape_and_pdf_validation_errors_do_not_mutate_draft(vacancy, fake_storage):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    path = document_path(draft.pk)

    missing = multipart_put(client, path, {}, token)
    extra_text = multipart_put(
        client,
        path,
        {"file": upload_file("cv.pdf", pdf_bytes()), "note": "unexpected"},
        token,
    )
    extra_file = multipart_put(
        client,
        path,
        {
            "file": upload_file("cv.pdf", pdf_bytes()),
            "attachment": upload_file("extra.pdf", pdf_bytes()),
        },
        token,
    )
    duplicate_file = multipart_put(
        client,
        path,
        {"file": [upload_file("one.pdf", pdf_bytes()), upload_file("two.pdf", pdf_bytes())]},
        token,
    )
    wrong_type = multipart_put(
        client,
        path,
        {"file": upload_file("cv.txt", pdf_bytes(), "text/plain")},
        token,
    )
    invalid_pdf = multipart_put(
        client,
        path,
        {"file": upload_file("cv.pdf", b"%PDF-1.4\ntruncated")},
        token,
    )
    json_body = client.put(
        path,
        {"file": "not-a-file"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )
    urlencoded_body = client.put(
        path,
        "file=not-a-file",
        content_type="application/x-www-form-urlencoded",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )
    multipart_prefix_spoof = client.put(
        path,
        encode_multipart("BoUnDaRyStRiNg", {"file": upload_file("cv.pdf", pdf_bytes())}),
        content_type="multipart/form-data-bad; boundary=BoUnDaRyStRiNg",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )
    malformed_multipart = client.put(
        path,
        (
            b"--bad\r\n"
            b'Content-Disposition: form-data; name="file"; filename="cv.pdf"\r\n'
            b"Content-Type: application/pdf\r\n\r\n"
            b"%PDF-1.4\n"
        ),
        content_type="multipart/form-data; boundary=bad",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_error(missing, 422, "validation_error")
    assert_error(extra_text, 422, "validation_error")
    assert_error(extra_file, 422, "validation_error")
    assert_error(duplicate_file, 422, "validation_error")
    assert_error(wrong_type, 415, "unsupported_file_type")
    assert_error(invalid_pdf, 422, "invalid_pdf")
    assert_error(json_body, 415, "unsupported_file_type")
    assert_error(urlencoded_body, 415, "unsupported_file_type")
    assert_error(multipart_prefix_spoof, 415, "unsupported_file_type")
    assert_error(malformed_multipart, 422, "validation_error")
    draft.refresh_from_db()
    assert draft.version == 1
    assert apps.get_model("documents.ApplicationDocument").objects.count() == 0
    assert fake_storage.iter_keys() == []


@pytest.mark.django_db
def test_storage_collision_retries_without_overwriting_existing_object(vacancy, fake_storage):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    first_id = uuid.UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
    first_key = f"drafts/{draft.pk}/{first_id}.pdf"
    fake_storage.save(first_key, io.BytesIO(b"original-collision"))
    generated = iter([first_id, uuid.UUID("bbbbbbbb-cccc-4ddd-8eee-ffffffffffff")])

    import apps.documents.services as services

    original_uuid4 = services.uuid.uuid4
    services.uuid.uuid4 = lambda: next(generated)
    try:
        response = multipart_put(
            client,
            document_path(draft.pk),
            {"file": upload_file("retry.pdf", pdf_bytes())},
            token,
        )
    finally:
        services.uuid.uuid4 = original_uuid4

    assert response.status_code == 201
    with fake_storage.open(first_key) as handle:
        assert handle.read() == b"original-collision"
    assert len(fake_storage.iter_keys(prefix=f"drafts/{draft.pk}/")) == 2


@pytest.mark.django_db
def test_storage_collision_retry_bound_fails_safely(vacancy, fake_storage, monkeypatch):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    colliding_id = uuid.UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
    colliding_key = f"drafts/{draft.pk}/{colliding_id}.pdf"
    fake_storage.save(colliding_key, io.BytesIO(b"original-collision"))

    import apps.documents.services as services

    monkeypatch.setattr(services.uuid, "uuid4", lambda: colliding_id)

    response = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("retry-bound.pdf", pdf_bytes())},
        token,
    )

    assert_error(response, 503, "document_storage_unavailable")
    with fake_storage.open(colliding_key) as handle:
        assert handle.read() == b"original-collision"
    draft.refresh_from_db()
    assert draft.version == 1
    assert apps.get_model("documents.ApplicationDocument").objects.count() == 0
    assert fake_storage.iter_keys(prefix=f"drafts/{draft.pk}/") == [colliding_key]


@pytest.mark.django_db
def test_storage_save_failure_does_not_mutate_draft_or_create_metadata(vacancy, monkeypatch):
    storage = FakeDocumentStorage(fail_on_save=True)
    monkeypatch.setattr("apps.documents.services.get_document_storage", lambda: storage)
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("storage-down.pdf", pdf_bytes())},
        token,
    )

    assert_error(response, 503, "document_storage_unavailable")
    draft.refresh_from_db()
    assert draft.version == 1
    assert apps.get_model("documents.ApplicationDocument").objects.count() == 0
    assert storage.iter_keys() == []


@pytest.mark.django_db
def test_database_failure_after_storage_save_compensates_new_object(
    vacancy, fake_storage, monkeypatch
):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    import apps.documents.services as services

    def fail_create(*args, **kwargs):
        raise IntegrityError("fictional metadata write failure")

    monkeypatch.setattr(services.ApplicationDocument.objects, "create", fail_create)

    response = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("metadata-failure.pdf", pdf_bytes())},
        token,
    )

    assert_error(response, 503, "document_storage_unavailable")
    draft.refresh_from_db()
    assert draft.version == 1
    assert apps.get_model("documents.ApplicationDocument").objects.count() == 0
    assert fake_storage.iter_keys() == []


@pytest.mark.django_db
def test_stale_after_storage_recheck_compensates_new_object(vacancy, monkeypatch):
    class StaleAfterSaveStorage(FakeDocumentStorage):
        def __init__(self, draft):
            super().__init__()
            self.draft = draft

        def save(self, key, source):
            super().save(key, source)
            apps.get_model("applications.ApplicationDraft").objects.filter(pk=self.draft.pk).update(
                version=2
            )

    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    storage = StaleAfterSaveStorage(draft)
    monkeypatch.setattr("apps.documents.services.get_document_storage", lambda: storage)

    response = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("stale-after-storage.pdf", pdf_bytes())},
        token,
    )

    assert_error(response, 409, "draft_conflict")
    draft.refresh_from_db()
    assert draft.version == 2
    assert apps.get_model("documents.ApplicationDocument").objects.count() == 0
    assert storage.iter_keys() == []


@pytest.mark.django_db
def test_replacement_loses_to_delete_after_storage_and_compensates_new_object(
    vacancy, fake_storage, monkeypatch, django_capture_on_commit_callbacks
):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    credential = created.cookies["applyflow_draft"].value
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    first = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("active.pdf", pdf_bytes())},
        token,
    )
    assert first.status_code == 201
    old_document = apps.get_model("documents.ApplicationDocument").objects.get()

    import apps.documents.services as services

    original_save = fake_storage.save
    deletion_triggered = False

    def save_then_delete(key, source):
        nonlocal deletion_triggered
        original_save(key, source)
        if not deletion_triggered:
            deletion_triggered = True
            services.delete_active_draft_cv(
                draft=draft,
                credential=credential,
                expected_version=2,
            )

    monkeypatch.setattr(fake_storage, "save", save_then_delete)

    with django_capture_on_commit_callbacks(execute=True):
        response = multipart_put(
            client,
            document_path(draft.pk),
            {"file": upload_file("replacement-loser.pdf", pdf_bytes())},
            token,
            version=2,
        )

    assert_error(response, 409, "draft_conflict")
    old_document.refresh_from_db()
    draft.refresh_from_db()
    assert draft.version == 3
    assert old_document.deleted_at is not None
    assert old_document.storage_deleted_at is not None
    assert (
        apps.get_model("documents.ApplicationDocument")
        .objects.filter(deleted_at__isnull=True)
        .count()
        == 0
    )
    assert fake_storage.iter_keys() == []


@pytest.mark.django_db
def test_abandonment_retires_active_document_and_clears_cookie(
    vacancy, fake_storage, django_capture_on_commit_callbacks
):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    upload = multipart_put(
        client,
        document_path(draft.pk),
        {"file": upload_file("abandon.pdf", pdf_bytes())},
        token,
    )
    assert upload.status_code == 201
    document = apps.get_model("documents.ApplicationDocument").objects.get()

    with django_capture_on_commit_callbacks(execute=True):
        response = client.delete(
            f"/api/v1/application-drafts/{draft.pk}/",
            HTTP_X_CSRFTOKEN=token,
            HTTP_IF_MATCH='"draft-2"',
        )

    assert response.status_code == 204
    assert int(response.cookies["applyflow_draft"]["max-age"]) == 0
    draft.refresh_from_db()
    document.refresh_from_db()
    assert draft.status == draft.Status.ABANDONED
    assert draft.version == 3
    assert document.deleted_at is not None
    assert document.original_name_display == ""
    assert document.storage_deleted_at is not None
    assert not fake_storage.exists(document.storage_key)


@pytest.mark.django_db
def test_no_public_document_route_or_internal_metadata_exposure():
    from config.api_urls import urlpatterns

    route_text = "\n".join(str(pattern.pattern) for pattern in urlpatterns)
    assert "documents/cv" in route_text
    assert "download" not in route_text
    assert "media" not in route_text
    assert "FileResponse" not in route_text
