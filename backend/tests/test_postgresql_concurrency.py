import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from threading import Barrier, Event, Lock

import pytest
from django.apps import apps
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import Client
from django.test.client import MULTIPART_CONTENT, encode_multipart
from django.utils import timezone
from pypdf import PdfWriter

from apps.applications.cleanup import (
    CleanupSummary,
    cleanup_application_drafts,
    delete_pending_document_storage,
    hard_delete_draft_shell,
    process_orphan_storage_objects,
    transition_expired_draft,
)
from apps.documents.storage import FakeDocumentStorage
from apps.documents.storage_keys import draft_cv_storage_key

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.postgres]


@dataclass(frozen=True)
class HttpWorkerResult:
    name: str
    pid: int
    status_code: int
    payload: dict | None = None


class ThreadSafeFakeStorage(FakeDocumentStorage):
    def __init__(self):
        super().__init__()
        self._guard = Lock()
        self.saved_keys: list[str] = []
        self.deleted_keys: list[str] = []
        self.save_barrier: Barrier | None = None

    def arm_save_barrier(self, parties: int) -> None:
        self.save_barrier = Barrier(parties)

    def save(self, key, source):
        with self._guard:
            super().save(key, source)
            self.saved_keys.append(key)
        if self.save_barrier is not None:
            self.save_barrier.wait(timeout=10)

    def delete(self, key):
        with self._guard:
            super().delete(key)
            self.deleted_keys.append(key)

    def exists(self, key):
        with self._guard:
            return super().exists(key)

    def iter_keys(self, prefix=None, *, older_than=None, limit=None):
        with self._guard:
            return super().iter_keys(prefix=prefix, older_than=older_than, limit=limit)

    def set_stored_at(self, key, stored_at):
        with self._guard:
            return super().set_stored_at(key, stored_at)


class MetadataRestoringStorage(ThreadSafeFakeStorage):
    def __init__(self, document_id):
        super().__init__()
        self.document_id = document_id
        self.restore_pid: int | None = None

    def delete(self, key):
        super().delete(key)

        def restore_document():
            close_old_connections()
            try:
                self.restore_pid = postgres_backend_pid()
                apps.get_model("documents.ApplicationDocument").objects.filter(
                    pk=self.document_id
                ).update(deleted_at=None, original_name_display="restored.pdf")
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(restore_document).result(timeout=10)


def postgres_backend_pid() -> int:
    with connection.cursor() as cursor:
        cursor.execute("select pg_backend_pid()")
        return int(cursor.fetchone()[0])


def make_vacancy(slug: str | None = None):
    Vacancy = apps.get_model("vacancies.Vacancy")
    unique_slug = slug or f"postgres-verification-{uuid.uuid4().hex[:12]}"
    return Vacancy.objects.create(
        slug=unique_slug,
        title="PostgreSQL Verification Engineer",
        summary="Build reliable candidate services.",
        description="A fictional vacancy used for PostgreSQL verification tests.",
        location="Tashkent, Uzbekistan",
        work_format=Vacancy.WorkFormat.HYBRID,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        status=Vacancy.Status.PUBLISHED,
        published_at=timezone.now(),
    )


def make_draft(vacancy, **overrides):
    ApplicationDraft = apps.get_model("applications.ApplicationDraft")
    payload = {
        "vacancy": vacancy,
        "secret_hash": f"fictional-secret-hash-{uuid.uuid4()}",
        "expires_at": timezone.now() + timedelta(days=7),
    }
    payload.update(overrides)
    draft = ApplicationDraft.objects.create(**payload)
    if "created_at" in overrides or "last_activity_at" in overrides:
        ApplicationDraft.objects.filter(pk=draft.pk).update(
            created_at=overrides.get("created_at", draft.created_at),
            last_activity_at=overrides.get("last_activity_at", draft.last_activity_at),
        )
        draft.refresh_from_db()
    return draft


def make_clean_terminal_draft(vacancy, *, status="expired"):
    now = timezone.now()
    draft = make_draft(
        vacancy,
        status=status,
        expires_at=now - timedelta(days=1),
        full_name="",
        email="",
        email_normalized="",
        phone="",
        portfolio_url="",
        preferred_contact_method="",
        experience_level="",
        skills=[],
        optional_message="",
        consent_acknowledged=False,
        consent_version="",
        credential_revoked_at=now,
    )
    return draft


def make_application(vacancy, *, reference: str | None = None, email="avery@example.test"):
    now = timezone.now()
    return apps.get_model("applications.Application").objects.create(
        vacancy=vacancy,
        full_name="Avery Example",
        email=email,
        email_normalized=email.casefold(),
        consent_version="phase-3-postgres-test",
        consented_at=now,
        application_reference=reference or f"AF-PG-{uuid.uuid4().hex[:8].upper()}",
        status_lookup_secret_hash=f"fictional-status-hash-{uuid.uuid4()}",
        submitted_at=now,
    )


def make_document(*, draft=None, application=None, storage=None, deleted=False, key=None):
    document_id = uuid.uuid4()
    if key is None:
        owner_id = draft.pk if draft is not None else uuid.uuid4()
        key = draft_cv_storage_key(owner_id, document_id)
    if storage is not None:
        storage.save(key, io.BytesIO(b"private-pdf-bytes"))
    return apps.get_model("documents.ApplicationDocument").objects.create(
        id=document_id,
        draft=draft,
        application=application,
        original_name_display="" if deleted else "avery-example-cv.pdf",
        storage_key=key,
        detected_content_type="application/pdf",
        size=17,
        sha256="a" * 64,
        deleted_at=timezone.now() if deleted else None,
    )


def make_experience(draft, **overrides):
    payload = {
        "draft": draft,
        "organization": "Example Studio",
        "role_title": "Frontend Developer",
        "start_month": date(2024, 1, 1),
        "end_month": None,
        "is_current": True,
        "summary": "Built accessible fictional product interfaces.",
        "position": 0,
    }
    payload.update(overrides)
    return apps.get_model("applications.DraftExperienceEntry").objects.create(**payload)


def pdf_bytes(page_count=1):
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def upload_file(name="avery-example-cv.pdf", content=None):
    return SimpleUploadedFile(name, content or pdf_bytes(), content_type="application/pdf")


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


def create_authorized_draft(vacancy):
    client, token = csrf_client()
    response = create_draft(client, vacancy, token)
    assert response.status_code == 201
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    return client, token, draft, response.cookies["applyflow_draft"].value


def clone_authorized_client(csrftoken: str, credential: str):
    client = Client(enforce_csrf_checks=True)
    client.cookies["csrftoken"] = csrftoken
    client.cookies["applyflow_draft"] = credential
    return client


def multipart_put(client, draft_id, payload, token, *, version):
    return client.put(
        f"/api/v1/application-drafts/{draft_id}/documents/cv/",
        encode_multipart("BoUnDaRyStRiNg", payload),
        content_type=MULTIPART_CONTENT,
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


def delete_cv(client, draft_id, token, *, version):
    return client.delete(
        f"/api/v1/application-drafts/{draft_id}/documents/cv/",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


def delete_draft(client, draft_id, token, *, version):
    return client.delete(
        f"/api/v1/application-drafts/{draft_id}/",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


def patch_candidate(client, draft_id, token, payload, *, version):
    return client.patch(
        f"/api/v1/application-drafts/{draft_id}/candidate/",
        payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


def assert_error(response, status_code: int, code: str):
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def run_workers(worker, *, count=2, timeout=20):
    with ThreadPoolExecutor(max_workers=count) as pool:
        futures = [pool.submit(worker, index) for index in range(count)]
        return [future.result(timeout=timeout) for future in futures]


def install_document_storage(monkeypatch, storage):
    monkeypatch.setattr("apps.documents.services.get_document_storage", lambda: storage)
    monkeypatch.setattr("apps.applications.cleanup.get_document_storage", lambda: storage)


def active_documents():
    return apps.get_model("documents.ApplicationDocument").objects.filter(deleted_at__isnull=True)


def assert_active_document_storage_is_present(storage):
    for document in active_documents():
        assert storage.exists(document.storage_key)


def assert_integrity_error(callback):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            callback()
    with connection.cursor() as cursor:
        cursor.execute("select 1")
        assert cursor.fetchone()[0] == 1


def test_postgresql_verification_uses_real_postgresql_test_database():
    with connection.cursor() as cursor:
        cursor.execute("select current_database(), current_setting('server_version')")
        database_name, server_version = cursor.fetchone()

    assert connection.vendor == "postgresql"
    assert database_name == settings.DATABASES["default"]["TEST"]["NAME"]
    assert database_name.startswith("test_")
    assert server_version


def test_simultaneous_draft_creation_uses_independent_connections_and_one_canonical_draft():
    vacancy = make_vacancy()
    bootstrap, token = csrf_client()
    csrf_cookie = bootstrap.cookies["csrftoken"].value
    creation_key = bootstrap.cookies["applyflow_draft_creation"].value
    barrier = Barrier(2)

    def send_request(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            client = Client(enforce_csrf_checks=True)
            client.cookies["csrftoken"] = csrf_cookie
            client.cookies["applyflow_draft_creation"] = creation_key
            barrier.wait(timeout=10)
            response = create_draft(client, vacancy, token)
            return HttpWorkerResult(
                name=f"creator-{index}",
                pid=pid,
                status_code=response.status_code,
                payload={
                    "draft_id": response.json()["draft"]["id"],
                    "credential": response.cookies["applyflow_draft"].value,
                },
            )
        finally:
            close_old_connections()

    results = run_workers(send_request)

    assert len({result.pid for result in results}) == 2
    assert sorted(result.status_code for result in results) == [200, 201]
    assert len({result.payload["draft_id"] for result in results if result.payload}) == 1
    assert len({result.payload["credential"] for result in results if result.payload}) == 1
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    assert draft.creation_key_digest != creation_key
    assert creation_key not in draft.secret_hash

    other_client, other_token = csrf_client()
    other_response = create_draft(other_client, vacancy, other_token)

    assert other_response.status_code == 201
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 2


def test_draft_row_lock_serializes_mutation_and_stale_loser_conflicts():
    vacancy = make_vacancy()
    client, token, draft, credential = create_authorized_draft(vacancy)
    csrf_cookie = client.cookies["csrftoken"].value
    worker_started = Event()
    worker_done = Event()

    def stale_patch(_index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            worker = clone_authorized_client(csrf_cookie, credential)
            worker_started.set()
            response = patch_candidate(
                worker,
                draft.pk,
                token,
                {"full_name": "Blocked Loser"},
                version=1,
            )
            worker_done.set()
            return HttpWorkerResult("stale-patch", pid, response.status_code, response.json())
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            main_pid = postgres_backend_pid()
            locked = (
                apps.get_model("applications.ApplicationDraft")
                .objects.select_for_update()
                .get(pk=draft.pk)
            )
            now = timezone.now()
            locked.full_name = "Committed Winner"
            locked.record_successful_mutation(now=now)
            locked.save(
                update_fields=[
                    "full_name",
                    "last_activity_at",
                    "expires_at",
                    "version",
                    "updated_at",
                ]
            )
            future = pool.submit(stale_patch, 0)
            assert worker_started.wait(timeout=10)
            assert worker_done.wait(timeout=0.2) is False
        result = future.result(timeout=10)

    assert main_pid != result.pid
    assert result.status_code == 409
    assert result.payload["error"]["code"] == "draft_conflict"
    draft.refresh_from_db()
    assert draft.full_name == "Committed Winner"
    assert draft.version == 2


def test_simultaneous_first_cv_uploads_leave_one_active_document_and_compensate_loser(
    monkeypatch,
):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    client, token, draft, credential = create_authorized_draft(vacancy)
    csrf_cookie = client.cookies["csrftoken"].value
    storage.arm_save_barrier(2)
    barrier = Barrier(2)

    def upload(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            worker = clone_authorized_client(csrf_cookie, credential)
            barrier.wait(timeout=10)
            response = multipart_put(
                worker,
                draft.pk,
                {"file": upload_file(f"first-{index}.pdf")},
                token,
                version=1,
            )
            payload = response.json() if response.status_code != 204 else None
            return HttpWorkerResult(f"upload-{index}", pid, response.status_code, payload)
        finally:
            close_old_connections()

    results = run_workers(upload)

    assert len({result.pid for result in results}) == 2
    assert sorted(result.status_code for result in results) == [201, 409]
    assert len(storage.saved_keys) == 2
    assert active_documents().count() == 1
    draft.refresh_from_db()
    assert draft.version == 2
    assert storage.iter_keys(prefix=f"drafts/{draft.pk}/") == [active_documents().get().storage_key]
    assert_active_document_storage_is_present(storage)


def test_simultaneous_cv_replacements_keep_one_committed_active_document(monkeypatch):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    client, token, draft, credential = create_authorized_draft(vacancy)
    csrf_cookie = client.cookies["csrftoken"].value
    first = multipart_put(
        client,
        draft.pk,
        {"file": upload_file("first.pdf")},
        token,
        version=1,
    )
    assert first.status_code == 201
    old_document = active_documents().get()
    storage.arm_save_barrier(2)
    barrier = Barrier(2)

    def replace(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            worker = clone_authorized_client(csrf_cookie, credential)
            barrier.wait(timeout=10)
            response = multipart_put(
                worker,
                draft.pk,
                {"file": upload_file(f"replacement-{index}.pdf")},
                token,
                version=2,
            )
            payload = response.json() if response.status_code != 204 else None
            return HttpWorkerResult(f"replace-{index}", pid, response.status_code, payload)
        finally:
            close_old_connections()

    results = run_workers(replace)

    assert len({result.pid for result in results}) == 2
    assert sorted(result.status_code for result in results) == [200, 409]
    assert active_documents().count() == 1
    active = active_documents().get()
    assert active.pk != old_document.pk
    old_document.refresh_from_db()
    assert old_document.deleted_at is not None
    assert old_document.storage_deleted_at is not None
    assert storage.iter_keys(prefix=f"drafts/{draft.pk}/") == [active.storage_key]
    assert_active_document_storage_is_present(storage)


def test_cv_replacement_and_delete_race_preserves_singleton_state(monkeypatch):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    client, token, draft, credential = create_authorized_draft(vacancy)
    csrf_cookie = client.cookies["csrftoken"].value
    first = multipart_put(
        client,
        draft.pk,
        {"file": upload_file("active.pdf")},
        token,
        version=1,
    )
    assert first.status_code == 201
    barrier = Barrier(2)

    def mutate(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            worker = clone_authorized_client(csrf_cookie, credential)
            barrier.wait(timeout=10)
            if index == 0:
                response = multipart_put(
                    worker,
                    draft.pk,
                    {"file": upload_file("replacement.pdf")},
                    token,
                    version=2,
                )
                name = "replace"
            else:
                response = delete_cv(worker, draft.pk, token, version=2)
                name = "delete"
            payload = response.json() if response.status_code != 204 else None
            return HttpWorkerResult(name, pid, response.status_code, payload)
        finally:
            close_old_connections()

    results = run_workers(mutate)

    assert len({result.pid for result in results}) == 2
    assert sorted(result.status_code for result in results) == [204, 409] or sorted(
        result.status_code for result in results
    ) == [200, 409]
    assert active_documents().count() in {0, 1}
    assert active_documents().count() == len(storage.iter_keys(prefix=f"drafts/{draft.pk}/"))
    assert_active_document_storage_is_present(storage)


def test_cv_replacement_and_abandonment_race_preserves_authorized_state(monkeypatch):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    client, token, draft, credential = create_authorized_draft(vacancy)
    csrf_cookie = client.cookies["csrftoken"].value
    first = multipart_put(
        client,
        draft.pk,
        {"file": upload_file("active.pdf")},
        token,
        version=1,
    )
    assert first.status_code == 201
    barrier = Barrier(2)

    def mutate(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            worker = clone_authorized_client(csrf_cookie, credential)
            barrier.wait(timeout=10)
            if index == 0:
                response = multipart_put(
                    worker,
                    draft.pk,
                    {"file": upload_file("replacement.pdf")},
                    token,
                    version=2,
                )
                name = "replace"
            else:
                response = delete_draft(worker, draft.pk, token, version=2)
                name = "abandon"
            payload = response.json() if response.status_code != 204 else None
            return HttpWorkerResult(name, pid, response.status_code, payload)
        finally:
            close_old_connections()

    results = run_workers(mutate)

    assert len({result.pid for result in results}) == 2
    status_codes = sorted(result.status_code for result in results)
    assert status_codes in ([200, 409], [204, 404])
    draft.refresh_from_db()
    if any(result.name == "abandon" and result.status_code == 204 for result in results):
        assert draft.status == draft.Status.ABANDONED
        assert active_documents().count() == 0
        assert storage.iter_keys(prefix=f"drafts/{draft.pk}/") == []
    else:
        assert draft.status == draft.Status.ACTIVE
        assert active_documents().count() == 1
        assert_active_document_storage_is_present(storage)


def test_active_document_partial_unique_index_rejects_concurrent_direct_inserts():
    vacancy = make_vacancy()
    draft = make_draft(vacancy)
    barrier = Barrier(2)

    def insert_document(index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            barrier.wait(timeout=10)
            try:
                with transaction.atomic():
                    make_document(
                        draft=draft,
                        key=draft_cv_storage_key(draft.pk, uuid.uuid4()),
                    )
                outcome = "created"
            except IntegrityError:
                outcome = "integrity_error"
            return {"pid": pid, "outcome": outcome}
        finally:
            close_old_connections()

    results = run_workers(insert_document)

    assert len({result["pid"] for result in results}) == 2
    assert sorted(result["outcome"] for result in results) == ["created", "integrity_error"]
    assert active_documents().count() == 1
    with connection.cursor() as cursor:
        cursor.execute("select 1")
        assert cursor.fetchone()[0] == 1


def test_postgresql_constraints_reject_invalid_database_states():
    vacancy = make_vacancy()
    draft = make_draft(vacancy, creation_key_digest="a" * 64)
    application = make_application(vacancy, reference="AF-PG-CONSTRAINT")
    make_experience(draft, position=0)
    make_document(draft=draft)
    make_document(application=application)

    assert_integrity_error(
        lambda: apps.get_model("vacancies.Vacancy").objects.create(
            slug=f"unpublished-{uuid.uuid4().hex}",
            title="Unpublished",
            summary="Invalid published vacancy.",
            description="A fictional invalid vacancy.",
            location="Tashkent, Uzbekistan",
            work_format="hybrid",
            employment_type="full_time",
            status="published",
            published_at=None,
        )
    )
    assert_integrity_error(
        lambda: apps.get_model("applications.ApplicationDraft").objects.create(
            vacancy=vacancy,
            secret_hash=f"fictional-secret-hash-{uuid.uuid4()}",
            status="submitted",
            submitted_at=None,
            expires_at=timezone.now() + timedelta(days=7),
        )
    )
    assert_integrity_error(
        lambda: apps.get_model("applications.ApplicationDraft").objects.create(
            vacancy=vacancy,
            secret_hash=f"fictional-secret-hash-{uuid.uuid4()}",
            creation_key_digest="a" * 64,
            expires_at=timezone.now() + timedelta(days=7),
        )
    )
    assert_integrity_error(
        lambda: make_application(
            vacancy,
            reference="AF-PG-CONSTRAINT",
            email="another@example.test",
        )
    )
    assert_integrity_error(
        lambda: make_application(
            vacancy,
            reference="AF-PG-OTHER",
            email="avery@example.test",
        )
    )
    assert_integrity_error(
        lambda: apps.get_model("documents.ApplicationDocument").objects.create(
            original_name_display="no-owner.pdf",
            storage_key=draft_cv_storage_key(uuid.uuid4(), uuid.uuid4()),
            detected_content_type="application/pdf",
            size=17,
            sha256="b" * 64,
        )
    )
    assert_integrity_error(
        lambda: make_document(
            draft=draft,
            application=application,
            key=draft_cv_storage_key(uuid.uuid4(), uuid.uuid4()),
        )
    )
    assert_integrity_error(
        lambda: make_document(
            draft=draft,
            key=draft_cv_storage_key(draft.pk, uuid.uuid4()),
        )
    )
    assert_integrity_error(
        lambda: make_document(
            application=application,
            key=draft_cv_storage_key(uuid.uuid4(), uuid.uuid4()),
        )
    )
    assert_integrity_error(
        lambda: apps.get_model("documents.ApplicationDocument").objects.create(
            draft=make_draft(vacancy),
            original_name_display="storage-deleted-without-logical-delete.pdf",
            storage_key=draft_cv_storage_key(uuid.uuid4(), uuid.uuid4()),
            detected_content_type="application/pdf",
            size=17,
            sha256="c" * 64,
            storage_deleted_at=timezone.now(),
        )
    )
    assert_integrity_error(lambda: make_experience(draft, position=0, organization="Collision"))
    assert_integrity_error(
        lambda: make_experience(
            draft,
            position=1,
            is_current=True,
            end_month=date(2024, 2, 1),
        )
    )


def test_cleanup_expired_selection_rechecks_renewed_draft_before_transition():
    vacancy = make_vacancy()
    now = timezone.now()
    draft = make_draft(
        vacancy,
        expires_at=now - timedelta(minutes=1),
        last_activity_at=now - timedelta(days=8),
    )
    selected = list(
        apps.get_model("applications.ApplicationDraft")
        .objects.filter(status="active", expires_at__lte=now)
        .values_list("pk", flat=True)
    )

    def renew_draft():
        close_old_connections()
        try:
            with transaction.atomic():
                locked = (
                    apps.get_model("applications.ApplicationDraft")
                    .objects.select_for_update()
                    .select_related("vacancy")
                    .get(pk=draft.pk)
                )
                locked.record_successful_mutation(now=now)
                locked.save(
                    update_fields=["last_activity_at", "expires_at", "version", "updated_at"]
                )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(renew_draft).result(timeout=10)

    assert selected == [draft.pk]
    assert transition_expired_draft(draft.pk, now=now) is False
    draft.refresh_from_db()
    assert draft.status == draft.Status.ACTIVE
    assert draft.credential_revoked_at is None
    assert draft.expires_at > now


def test_cleanup_pending_document_rechecks_metadata_after_storage_delete():
    vacancy = make_vacancy()
    draft = make_draft(vacancy)
    initial_storage = ThreadSafeFakeStorage()
    document = make_document(draft=draft, storage=initial_storage, deleted=True)
    storage = MetadataRestoringStorage(document.pk)
    with initial_storage.open(document.storage_key) as source:
        storage.save(document.storage_key, source)

    result = delete_pending_document_storage(
        document.pk,
        storage=storage,
        now=timezone.now(),
    )

    document.refresh_from_db()
    assert result == "failed"
    assert storage.restore_pid is not None
    assert document.deleted_at is None
    assert document.storage_deleted_at is None
    assert not storage.exists(document.storage_key)


def test_cleanup_hard_delete_rechecks_candidate_fields_after_selection():
    vacancy = make_vacancy()
    draft = make_clean_terminal_draft(vacancy)
    selected = list(
        apps.get_model("applications.ApplicationDraft")
        .objects.filter(status__in=("abandoned", "expired"))
        .values_list("pk", flat=True)
    )

    def restore_candidate_field():
        close_old_connections()
        try:
            apps.get_model("applications.ApplicationDraft").objects.filter(pk=draft.pk).update(
                full_name="Avery Restored"
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(restore_candidate_field).result(timeout=10)

    assert selected == [draft.pk]
    assert hard_delete_draft_shell(draft.pk) is False
    draft.refresh_from_db()
    assert draft.full_name == "Avery Restored"


def test_cleanup_orphan_recheck_retains_key_that_becomes_referenced(monkeypatch):
    import apps.applications.cleanup as cleanup

    vacancy = make_vacancy()
    draft = make_draft(vacancy)
    storage = ThreadSafeFakeStorage()
    orphan_key = draft_cv_storage_key(draft.pk, uuid.uuid4())
    storage.save(orphan_key, io.BytesIO(b"orphan-bytes"))
    storage.set_stored_at(orphan_key, timezone.now() - timedelta(hours=48))
    checks = 0
    original_check = cleanup.storage_key_is_referenced

    def becomes_referenced(key):
        nonlocal checks
        checks += 1
        if checks == 1:
            return False
        if (
            not apps.get_model("documents.ApplicationDocument")
            .objects.filter(storage_key=key)
            .exists()
        ):
            make_document(draft=draft, key=key)
        return original_check(key)

    monkeypatch.setattr(cleanup, "storage_key_is_referenced", becomes_referenced)
    summary = CleanupSummary(mode="apply", batch_size=10, orphan_grace_hours=24)

    process_orphan_storage_objects(
        summary,
        apply=True,
        batch_size=10,
        orphan_grace_hours=24,
        storage=storage,
        now=timezone.now(),
    )

    assert checks == 2
    assert summary.orphan_objects_selected == 1
    assert summary.orphan_objects_skipped == 1
    assert summary.orphan_objects_deleted == 0
    assert storage.exists(orphan_key)
    assert (
        apps.get_model("documents.ApplicationDocument")
        .objects.filter(storage_key=orphan_key)
        .exists()
    )


def test_overlapping_cleanup_runs_are_idempotent(monkeypatch):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    now = timezone.now()
    draft = make_draft(
        vacancy,
        expires_at=now - timedelta(days=1),
        last_activity_at=now - timedelta(days=8),
        full_name="Avery Cleanup",
        email="avery.cleanup@example.test",
    )
    make_document(draft=draft, storage=storage)
    barrier = Barrier(2)

    def run_cleanup(_index):
        close_old_connections()
        try:
            pid = postgres_backend_pid()
            barrier.wait(timeout=10)
            summary = cleanup_application_drafts(apply=True, batch_size=10, now=now)
            return {"pid": pid, "failures": summary.total_failures}
        finally:
            close_old_connections()

    results = run_workers(run_cleanup)

    assert len({result["pid"] for result in results}) == 2
    assert [result["failures"] for result in results] == [0, 0]
    draft_exists = apps.get_model("applications.ApplicationDraft").objects.filter(pk=draft.pk)
    assert not draft_exists.filter(status="active").exists()
    assert active_documents().count() == 0


def test_rollback_paths_keep_connections_usable_and_compensate_storage(monkeypatch):
    storage = ThreadSafeFakeStorage()
    install_document_storage(monkeypatch, storage)
    vacancy = make_vacancy()
    client, token, draft, _credential = create_authorized_draft(vacancy)

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            locked = (
                apps.get_model("applications.ApplicationDraft")
                .objects.select_for_update()
                .get(pk=draft.pk)
            )
            locked.full_name = "Rolled Back"
            locked.save(update_fields=["full_name", "updated_at"])
            raise RuntimeError("fictional rollback")
    draft.refresh_from_db()
    assert draft.full_name == ""

    first = multipart_put(
        client,
        draft.pk,
        {"file": upload_file("first.pdf")},
        token,
        version=1,
    )
    assert first.status_code == 201
    old_document = active_documents().get()

    import apps.documents.services as services

    def fail_create(*args, **kwargs):
        raise IntegrityError("fictional metadata write failure")

    monkeypatch.setattr(services.ApplicationDocument.objects, "create", fail_create)
    replacement = multipart_put(
        client,
        draft.pk,
        {"file": upload_file("replacement.pdf")},
        token,
        version=2,
    )

    assert_error(replacement, 503, "document_storage_unavailable")
    draft.refresh_from_db()
    old_document.refresh_from_db()
    assert draft.version == 2
    assert old_document.deleted_at is None
    assert old_document.storage_deleted_at is None
    assert active_documents().count() == 1
    assert storage.iter_keys(prefix=f"drafts/{draft.pk}/") == [old_document.storage_key]
    with connection.cursor() as cursor:
        cursor.execute("select 1")
        assert cursor.fetchone()[0] == 1
