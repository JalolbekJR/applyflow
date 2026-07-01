import io
import uuid
from datetime import date, timedelta
from io import StringIO

import pytest
from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.documents.storage import DocumentStorageOperationError, FakeDocumentStorage
from apps.documents.storage_keys import draft_cv_storage_key


@pytest.fixture
def vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug=f"cleanup-engineer-{uuid.uuid4()}",
        title="Cleanup Engineer",
        summary="Build private cleanup controls.",
        description="A fictional vacancy used for cleanup command tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


@pytest.fixture
def storage(monkeypatch):
    storage = TrackingFakeStorage()
    monkeypatch.setattr("apps.applications.cleanup.get_document_storage", lambda: storage)
    return storage


class TrackingFakeStorage(FakeDocumentStorage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.delete_calls = 0

    def delete(self, key: str) -> None:
        self.delete_calls += 1
        super().delete(key)


class ListingFailureStorage(TrackingFakeStorage):
    def iter_keys(self, prefix=None, *, older_than=None, limit=None):
        raise DocumentStorageOperationError("private path must stay hidden")


def symlink_supported(tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.write_text("fictional", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        return False
    return link.is_symlink()


def run_cleanup(*args, expect_error=False):
    stdout = StringIO()
    stderr = StringIO()
    error = None
    try:
        call_command("cleanup_application_drafts", *args, stdout=stdout, stderr=stderr)
    except CommandError as exc:
        error = exc
        if not expect_error:
            raise
    if expect_error and error is None:
        raise AssertionError("cleanup command was expected to fail")
    return stdout.getvalue(), stderr.getvalue(), error


def summary_values(output):
    values = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def make_draft(vacancy, *, now=None, expires_at=None, with_candidate=True, status="active"):
    now = now or timezone.now()
    ApplicationDraft = apps.get_model("applications.ApplicationDraft")
    payload = {
        "vacancy": vacancy,
        "secret_hash": make_password(str(uuid.uuid4())),
        "expires_at": expires_at or now + timedelta(days=7),
        "status": status,
    }
    if status == "submitted":
        payload["submitted_at"] = now
    if with_candidate:
        payload.update(
            {
                "full_name": "Avery Cleanup",
                "email": "avery.cleanup@example.test",
                "phone": "+998 90 000 00 00",
                "portfolio_url": "https://example.test/private",
                "preferred_contact_method": "email",
                "experience_level": "senior",
                "skills": ["Django", "privacy"],
                "optional_message": "Private cleanup message.",
                "consent_acknowledged": True,
                "consent_version": "phase-3-cleanup",
            }
        )
    draft = ApplicationDraft.objects.create(**payload)
    ApplicationDraft.objects.filter(pk=draft.pk).update(
        created_at=now,
        last_activity_at=now,
        expires_at=payload["expires_at"],
    )
    draft.refresh_from_db()
    return draft


def make_clean_terminal_draft(vacancy, *, status="abandoned", now=None):
    now = now or timezone.now()
    draft = make_draft(
        vacancy,
        now=now,
        expires_at=now - timedelta(days=1),
        with_candidate=False,
        status=status,
    )
    update_fields = ["status", "credential_revoked_at"]
    draft.status = status
    draft.credential_revoked_at = now
    if status == "submitted":
        draft.submitted_at = now
        update_fields.append("submitted_at")
    draft.save(update_fields=update_fields)
    return draft


def make_experience(draft):
    DraftExperienceEntry = apps.get_model("applications.DraftExperienceEntry")
    return DraftExperienceEntry.objects.create(
        draft=draft,
        organization="Private Fictional Employer",
        role_title="Staff Engineer",
        start_month=date(2023, 1, 1),
        end_month=None,
        is_current=True,
        summary="Private experience summary.",
        position=0,
    )


def make_document(draft, storage, *, deleted=False, store=True, uploaded_at=None):
    now = timezone.now()
    ApplicationDocument = apps.get_model("documents.ApplicationDocument")
    document_id = uuid.uuid4()
    storage_key = draft_cv_storage_key(draft.pk, document_id)
    if store:
        storage.save(storage_key, io.BytesIO(b"private-pdf-bytes"))
    document = ApplicationDocument.objects.create(
        id=document_id,
        draft=draft,
        original_name_display="" if deleted else "avery-cleanup-cv.pdf",
        storage_key=storage_key,
        detected_content_type="application/pdf",
        size=17,
        sha256="a" * 64,
        deleted_at=now - timedelta(hours=1) if deleted else None,
    )
    if uploaded_at is not None:
        ApplicationDocument.objects.filter(pk=document.pk).update(uploaded_at=uploaded_at)
        document.refresh_from_db()
    return document


def set_storage_age(storage, key, *, hours):
    storage.set_stored_at(key, timezone.now() - timedelta(hours=hours))


def assert_candidate_scrubbed(draft):
    assert draft.full_name == ""
    assert draft.email == ""
    assert draft.email_normalized == ""
    assert draft.phone == ""
    assert draft.portfolio_url == ""
    assert draft.preferred_contact_method == ""
    assert draft.experience_level == ""
    assert draft.skills == []
    assert draft.optional_message == ""
    assert draft.consent_acknowledged is False
    assert draft.consent_version == ""


def assert_output_is_private(output, *private_values):
    for value in private_values:
        if value:
            assert str(value) not in output


@pytest.mark.django_db
def test_default_dry_run_reports_aggregate_counts_and_mutates_nothing(vacancy, storage):
    now = timezone.now()
    draft = make_draft(vacancy, now=now - timedelta(days=8), expires_at=now - timedelta(days=1))
    original = {
        "status": draft.status,
        "credential_revoked_at": draft.credential_revoked_at,
        "version": draft.version,
        "last_activity_at": draft.last_activity_at,
        "expires_at": draft.expires_at,
    }
    entry = make_experience(draft)
    document = make_document(draft, storage)
    set_storage_age(storage, document.storage_key, hours=48)

    stdout, stderr, error = run_cleanup()

    draft.refresh_from_db()
    document.refresh_from_db()
    values = summary_values(stdout)
    assert error is None
    assert stderr == ""
    assert values["mode"] == "dry-run"
    assert values["batch_size"] == "100"
    assert values["orphan_grace_hours"] == "24"
    assert values["expired_drafts_selected"] == "1"
    assert values["total_failures"] == "0"
    assert draft.status == original["status"]
    assert draft.credential_revoked_at == original["credential_revoked_at"]
    assert draft.version == original["version"]
    assert draft.last_activity_at == original["last_activity_at"]
    assert draft.expires_at == original["expires_at"]
    assert draft.full_name == "Avery Cleanup"
    assert apps.get_model("applications.DraftExperienceEntry").objects.filter(pk=entry.pk).exists()
    assert document.deleted_at is None
    assert document.original_name_display == "avery-cleanup-cv.pdf"
    assert storage.exists(document.storage_key)
    assert storage.delete_calls == 0
    assert_output_is_private(
        stdout + stderr,
        draft.pk,
        document.pk,
        document.storage_key,
        document.original_name_display,
        draft.email,
        draft.phone,
        draft.optional_message,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "args",
    [
        ("--batch-size", "0"),
        ("--batch-size", "-1"),
        ("--batch-size", "not-an-integer"),
        ("--batch-size", "1001"),
        ("--orphan-grace-hours", "0"),
        ("--orphan-grace-hours", "-1"),
        ("--orphan-grace-hours", "not-an-integer"),
    ],
)
def test_invalid_command_options_exit_nonzero(args, storage):
    stdout, stderr, error = run_cleanup(*args, expect_error=True)

    assert error is not None
    assert stdout == ""
    assert "cleanup" not in stderr.lower()


@pytest.mark.django_db
def test_apply_expires_active_draft_scrubs_and_logically_deletes_without_renewal(
    vacancy,
    storage,
):
    now = timezone.now()
    draft = make_draft(vacancy, now=now - timedelta(days=8), expires_at=now - timedelta(days=1))
    original_activity = draft.last_activity_at
    original_expiry = draft.expires_at
    submitted = make_draft(
        vacancy,
        now=now - timedelta(days=8),
        expires_at=now - timedelta(days=1),
        with_candidate=True,
        status="submitted",
    )
    submitted.submitted_at = now
    submitted.save(update_fields=["submitted_at"])
    entry = make_experience(draft)
    document = make_document(draft, storage)
    storage.fail_on_delete = True

    stdout, stderr, error = run_cleanup("--apply", "--batch-size", "50", expect_error=True)

    draft.refresh_from_db()
    document.refresh_from_db()
    submitted.refresh_from_db()
    values = summary_values(stdout)
    assert error is not None
    assert values["mode"] == "apply"
    assert values["batch_size"] == "50"
    assert values["expired_drafts_selected"] == "1"
    assert values["expired_drafts_transitioned"] == "1"
    assert values["pending_document_failures"] == "1"
    assert values["total_failures"] == "1"
    assert draft.status == draft.Status.EXPIRED
    assert draft.credential_revoked_at is not None
    assert draft.last_activity_at == original_activity
    assert draft.expires_at == original_expiry
    assert draft.version == 2
    assert_candidate_scrubbed(draft)
    assert (
        not apps.get_model("applications.DraftExperienceEntry").objects.filter(pk=entry.pk).exists()
    )
    assert document.deleted_at is not None
    assert document.storage_deleted_at is None
    assert document.original_name_display == ""
    assert submitted.status == submitted.Status.SUBMITTED
    assert submitted.full_name == "Avery Cleanup"
    assert_output_is_private(
        stdout + stderr + str(error),
        draft.pk,
        document.pk,
        document.storage_key,
        "Avery Cleanup",
        "avery.cleanup@example.test",
        "Private cleanup message.",
    )

    first_revocation = draft.credential_revoked_at
    first_deleted_at = document.deleted_at
    stdout, _, _ = run_cleanup("--apply", expect_error=True)
    draft.refresh_from_db()
    document.refresh_from_db()
    assert draft.version == 2
    assert draft.credential_revoked_at == first_revocation
    assert document.deleted_at == first_deleted_at
    assert summary_values(stdout)["expired_drafts_transitioned"] == "0"


@pytest.mark.django_db
def test_expired_draft_selection_rechecks_renewed_draft_before_transition(
    vacancy,
    storage,
    monkeypatch,
):
    import apps.applications.cleanup as cleanup

    now = timezone.now()
    draft = make_draft(vacancy, now=now, expires_at=now - timedelta(minutes=1))
    original_transition = cleanup.transition_expired_draft

    def renew_before_lock(draft_id, *, now):
        if draft_id == draft.pk:
            ApplicationDraft = apps.get_model("applications.ApplicationDraft")
            ApplicationDraft.objects.filter(pk=draft_id).update(
                last_activity_at=now,
                expires_at=now + timedelta(days=1),
            )
        return original_transition(draft_id, now=now)

    monkeypatch.setattr(cleanup, "transition_expired_draft", renew_before_lock)

    stdout, stderr, error = run_cleanup("--apply")

    draft.refresh_from_db()
    values = summary_values(stdout)
    assert error is None
    assert stderr == ""
    assert values["expired_drafts_selected"] == "1"
    assert values["expired_drafts_transitioned"] == "0"
    assert draft.status == draft.Status.ACTIVE
    assert draft.credential_revoked_at is None
    assert draft.full_name == "Avery Cleanup"
    assert draft.version == 1


@pytest.mark.django_db
def test_pending_document_deletion_completes_missing_object_idempotently(vacancy, storage):
    draft = make_draft(vacancy, with_candidate=False)
    document = make_document(draft, storage, deleted=True, store=False)

    stdout, stderr, error = run_cleanup("--apply")

    document.refresh_from_db()
    values = summary_values(stdout)
    assert error is None
    assert stderr == ""
    assert values["pending_documents_selected"] == "1"
    assert values["pending_documents_already_missing"] == "1"
    assert values["pending_documents_deleted"] == "0"
    assert document.storage_deleted_at is not None
    assert apps.get_model("applications.ApplicationDraft").objects.filter(pk=draft.pk).exists()


@pytest.mark.django_db
def test_pending_document_failure_retries_and_then_allows_hard_delete(vacancy, storage):
    draft = make_clean_terminal_draft(vacancy, status="abandoned")
    document = make_document(draft, storage, deleted=True, store=True)
    storage.fail_on_delete = True

    stdout, _, error = run_cleanup("--apply", expect_error=True)

    document.refresh_from_db()
    values = summary_values(stdout)
    assert error is not None
    assert values["pending_document_failures"] == "1"
    assert values["draft_shells_retained"] == "1"
    assert document.storage_deleted_at is None
    assert storage.exists(document.storage_key)
    assert apps.get_model("applications.ApplicationDraft").objects.filter(pk=draft.pk).exists()

    storage.fail_on_delete = False
    stdout, stderr, error = run_cleanup("--apply")

    values = summary_values(stdout)
    assert error is None
    assert stderr == ""
    assert values["pending_documents_deleted"] == "1"
    assert values["draft_shells_hard_deleted"] == "1"
    assert not storage.exists(document.storage_key)
    assert not apps.get_model("applications.ApplicationDraft").objects.filter(pk=draft.pk).exists()


@pytest.mark.django_db
def test_storage_deleted_but_metadata_update_failure_finishes_on_next_run(
    vacancy,
    storage,
    monkeypatch,
):
    import apps.applications.cleanup as cleanup

    draft = make_draft(vacancy, with_candidate=False)
    document = make_document(draft, storage, deleted=True, store=True)
    original_record = cleanup.record_document_storage_deleted
    failed_once = False

    def fail_once(document_id, *, now):
        nonlocal failed_once
        if document_id == document.pk and not failed_once:
            failed_once = True
            raise RuntimeError("private path must stay hidden")
        return original_record(document_id, now=now)

    monkeypatch.setattr(cleanup, "record_document_storage_deleted", fail_once)

    stdout, stderr, error = run_cleanup("--apply", expect_error=True)

    document.refresh_from_db()
    assert error is not None
    assert summary_values(stdout)["pending_document_failures"] == "1"
    assert document.storage_deleted_at is None
    assert not storage.exists(document.storage_key)
    assert_output_is_private(stdout + stderr + str(error), document.storage_key, "private path")

    monkeypatch.setattr(cleanup, "record_document_storage_deleted", original_record)
    stdout, _, error = run_cleanup("--apply")
    document.refresh_from_db()
    assert error is None
    assert summary_values(stdout)["pending_documents_already_missing"] == "1"
    assert document.storage_deleted_at is not None


@pytest.mark.django_db
def test_orphan_reconciliation_respects_dry_run_grace_reference_and_batch(
    vacancy,
    storage,
):
    old_orphan = draft_cv_storage_key(
        uuid.UUID("00000000-0000-0000-0000-000000000001"),
        uuid.UUID("00000000-0000-0000-0000-000000000002"),
    )
    fresh_orphan = draft_cv_storage_key(
        uuid.UUID("ffffffff-ffff-ffff-ffff-fffffffffff1"),
        uuid.UUID("ffffffff-ffff-ffff-ffff-fffffffffff2"),
    )
    referenced_draft = make_draft(vacancy, with_candidate=False)
    referenced_document = make_document(referenced_draft, storage, store=True)
    for key in (old_orphan, fresh_orphan):
        storage.save(key, io.BytesIO(b"orphan-bytes"))
    set_storage_age(storage, old_orphan, hours=48)
    set_storage_age(storage, fresh_orphan, hours=1)
    set_storage_age(storage, referenced_document.storage_key, hours=48)

    stdout, _, error = run_cleanup("--batch-size", "1", "--orphan-grace-hours", "24")

    assert error is None
    assert summary_values(stdout)["mode"] == "dry-run"
    assert storage.exists(old_orphan)
    assert storage.exists(fresh_orphan)
    assert storage.exists(referenced_document.storage_key)
    assert storage.delete_calls == 0

    stdout, stderr, error = run_cleanup(
        "--apply",
        "--batch-size",
        "1",
        "--orphan-grace-hours",
        "24",
    )

    values = summary_values(stdout)
    assert error is None
    assert stderr == ""
    assert values["orphan_objects_selected"] == "1"
    assert values["orphan_objects_deleted"] == "1"
    assert not storage.exists(old_orphan)
    assert storage.exists(fresh_orphan)
    assert storage.exists(referenced_document.storage_key)
    assert_output_is_private(stdout, old_orphan, fresh_orphan, referenced_document.storage_key)


@pytest.mark.django_db
def test_logically_deleted_referenced_object_is_pending_not_orphan(vacancy, storage):
    draft = make_draft(vacancy, with_candidate=False)
    document = make_document(draft, storage, deleted=True, store=True)
    set_storage_age(storage, document.storage_key, hours=48)

    stdout, _, error = run_cleanup("--apply", "--orphan-grace-hours", "24")

    document.refresh_from_db()
    values = summary_values(stdout)
    assert error is None
    assert values["pending_documents_deleted"] == "1"
    assert values["orphan_objects_deleted"] == "0"
    assert document.storage_deleted_at is not None


@pytest.mark.django_db
def test_orphan_recheck_retains_object_that_becomes_referenced(vacancy, storage, monkeypatch):
    import apps.applications.cleanup as cleanup

    orphan_key = draft_cv_storage_key(uuid.uuid4(), uuid.uuid4())
    storage.save(orphan_key, io.BytesIO(b"orphan-bytes"))
    set_storage_age(storage, orphan_key, hours=48)
    seen_checks = 0

    def becomes_referenced(key):
        nonlocal seen_checks
        seen_checks += 1
        return seen_checks >= 2

    monkeypatch.setattr(cleanup, "storage_key_is_referenced", becomes_referenced)

    stdout, _, error = run_cleanup("--apply", "--orphan-grace-hours", "24")

    values = summary_values(stdout)
    assert error is None
    assert values["orphan_objects_selected"] == "1"
    assert values["orphan_objects_skipped"] == "1"
    assert values["orphan_objects_deleted"] == "0"
    assert storage.exists(orphan_key)


@pytest.mark.django_db
def test_provider_listing_uncertainty_retains_orphans_and_reports_apply_failure(
    monkeypatch,
):
    storage = ListingFailureStorage()
    key = draft_cv_storage_key(uuid.uuid4(), uuid.uuid4())
    storage.save(key, io.BytesIO(b"orphan-bytes"))
    set_storage_age(storage, key, hours=48)
    monkeypatch.setattr("apps.applications.cleanup.get_document_storage", lambda: storage)

    stdout, stderr, error = run_cleanup("--apply", expect_error=True)

    assert error is not None
    assert summary_values(stdout)["orphan_object_failures"] == "1"
    assert storage.exists(key)
    assert_output_is_private(stdout + stderr + str(error), key, "private path")


@pytest.mark.django_db
def test_dry_run_listing_uncertainty_returns_nonzero_without_deleting_orphan(
    monkeypatch,
):
    storage = ListingFailureStorage()
    key = draft_cv_storage_key(uuid.uuid4(), uuid.uuid4())
    storage.save(key, io.BytesIO(b"orphan-bytes"))
    set_storage_age(storage, key, hours=48)
    monkeypatch.setattr("apps.applications.cleanup.get_document_storage", lambda: storage)

    stdout, stderr, error = run_cleanup(expect_error=True)

    values = summary_values(stdout)
    assert error is not None
    assert values["mode"] == "dry-run"
    assert values["orphan_object_failures"] == "1"
    assert values["total_failures"] == "1"
    assert storage.exists(key)
    assert_output_is_private(stdout + stderr + str(error), key, "private path")


@pytest.mark.django_db
def test_hard_delete_only_removes_verified_terminal_shells(vacancy, storage):
    abandoned = make_clean_terminal_draft(vacancy, status="abandoned")
    expired = make_clean_terminal_draft(vacancy, status="expired")
    active = make_draft(vacancy, with_candidate=False)
    submitted = make_clean_terminal_draft(vacancy, status="submitted")
    pending = make_clean_terminal_draft(vacancy, status="expired")
    make_document(pending, storage, deleted=True, store=True)
    storage.fail_on_delete = True

    stdout, _, error = run_cleanup("--apply", expect_error=True)

    values = summary_values(stdout)
    assert error is not None
    assert values["draft_shells_hard_deleted"] == "2"
    assert values["draft_shells_retained"] == "1"
    ApplicationDraft = apps.get_model("applications.ApplicationDraft")
    assert not ApplicationDraft.objects.filter(pk=abandoned.pk).exists()
    assert not ApplicationDraft.objects.filter(pk=expired.pk).exists()
    assert ApplicationDraft.objects.filter(pk=active.pk).exists()
    assert ApplicationDraft.objects.filter(pk=submitted.pk).exists()
    assert ApplicationDraft.objects.filter(pk=pending.pk).exists()


@pytest.mark.django_db
def test_cleanup_orphan_reconciliation_does_not_follow_external_symlink(
    tmp_path,
    monkeypatch,
):
    if not symlink_supported(tmp_path):
        pytest.skip("filesystem symlink creation is unavailable")

    from apps.documents.storage import LocalPrivateDocumentStorage

    root = tmp_path / "private-documents"
    storage = LocalPrivateDocumentStorage(root)
    key = draft_cv_storage_key(uuid.uuid4(), uuid.uuid4())
    target = root.joinpath(*key.split("/"))
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"external-target")
    target.parent.mkdir(parents=True)
    target.symlink_to(outside)
    monkeypatch.setattr("apps.applications.cleanup.get_document_storage", lambda: storage)

    stdout, _, error = run_cleanup("--apply", "--orphan-grace-hours", "1")

    assert error is None
    assert summary_values(stdout)["orphan_objects_deleted"] == "0"
    assert outside.read_bytes() == b"external-target"
    assert target.is_symlink()
