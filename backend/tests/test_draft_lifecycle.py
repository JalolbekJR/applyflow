import base64
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import override_settings
from django.utils import timezone

from apps.applications.drafts import (
    CredentialError,
    generate_credential,
    parse_credential,
    verify_credential,
)


@pytest.fixture
def vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="security-engineer",
        title="Security Engineer",
        summary="Build defensive product controls.",
        description="A fictional vacancy used for draft lifecycle tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


def create_draft(vacancy, *, now=None):
    now = now or timezone.now()
    ApplicationDraft = apps.get_model("applications.ApplicationDraft")
    draft = ApplicationDraft.objects.create(
        vacancy=vacancy,
        secret_hash=make_password(str(uuid.uuid4())),
        expires_at=now + timedelta(days=7),
    )
    ApplicationDraft.objects.filter(pk=draft.pk).update(
        created_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(days=7),
    )
    draft.refresh_from_db()
    return draft


def create_experience_entry(draft, **overrides):
    DraftExperienceEntry = apps.get_model("applications.DraftExperienceEntry")
    payload = {
        "draft": draft,
        "organization": "Example Studio",
        "role_title": "Frontend Developer",
        "start_month": date(2024, 1, 1),
        "end_month": None,
        "is_current": True,
        "summary": "Built calm fictional candidate journeys.",
        "position": 0,
    }
    payload.update(overrides)
    return DraftExperienceEntry.objects.create(**payload)


@pytest.mark.django_db
@override_settings(
    DRAFT_INACTIVITY_LIFETIME=timedelta(days=7),
    DRAFT_ABSOLUTE_LIFETIME=timedelta(days=30),
)
def test_effective_expiry_uses_inactivity_absolute_and_vacancy_deadline(vacancy):
    start = timezone.now() - timedelta(days=29)
    vacancy.closing_at = start + timedelta(hours=12)
    vacancy.save(update_fields=["closing_at"])
    draft = create_draft(vacancy, now=start)

    assert draft.absolute_expires_at() == start + timedelta(days=30)
    assert draft.effective_expiry_at(last_activity_at=start) == start + timedelta(hours=12)


@pytest.mark.django_db
@override_settings(
    DRAFT_INACTIVITY_LIFETIME=timedelta(days=7),
    DRAFT_ABSOLUTE_LIFETIME=timedelta(days=30),
)
def test_lifecycle_boundaries_and_reads_do_not_renew_activity(vacancy):
    start = timezone.now() - timedelta(days=8)
    draft = create_draft(vacancy, now=start)
    original_activity = draft.last_activity_at
    original_expiry = draft.expires_at

    assert draft.is_expired(now=start + timedelta(days=7)) is True
    assert draft.is_active(now=start + timedelta(days=7)) is False
    draft.refresh_from_db()
    assert draft.last_activity_at == original_activity
    assert draft.expires_at == original_expiry


@pytest.mark.django_db
@override_settings(
    DRAFT_INACTIVITY_LIFETIME=timedelta(days=7),
    DRAFT_ABSOLUTE_LIFETIME=timedelta(days=30),
)
def test_successful_mutation_renews_activity_with_caps_and_increments_once(vacancy):
    start = timezone.now() - timedelta(days=29)
    vacancy.closing_at = start + timedelta(days=30, hours=12)
    vacancy.save(update_fields=["closing_at"])
    draft = create_draft(vacancy, now=start)
    mutation_time = start + timedelta(days=29)

    draft.record_successful_mutation(now=mutation_time)
    draft.save(update_fields=["last_activity_at", "expires_at", "version", "updated_at"])
    draft.refresh_from_db()

    assert draft.last_activity_at == mutation_time
    assert draft.expires_at == start + timedelta(days=30)
    assert draft.version == 2


@pytest.mark.django_db
@override_settings(
    DRAFT_INACTIVITY_LIFETIME=timedelta(days=7),
    DRAFT_ABSOLUTE_LIFETIME=timedelta(days=30),
)
def test_successful_mutation_cannot_extend_past_vacancy_deadline(vacancy):
    start = timezone.now() - timedelta(days=2)
    vacancy.closing_at = start + timedelta(days=3)
    vacancy.save(update_fields=["closing_at"])
    draft = create_draft(vacancy, now=start)

    draft.record_successful_mutation(now=start + timedelta(days=2))

    assert draft.expires_at == vacancy.closing_at


@pytest.mark.django_db
def test_abandonment_revokes_credential_and_increments_once(vacancy):
    draft = create_draft(vacancy)
    entry = create_experience_entry(draft)
    now = timezone.now()

    draft.abandon(now=now)

    assert draft.status == draft.Status.ABANDONED
    assert draft.credential_revoked_at == now
    assert draft.last_activity_at == now
    assert draft.version == 2
    assert draft.is_active(now=now) is False
    assert (
        not apps.get_model("applications.DraftExperienceEntry").objects.filter(pk=entry.pk).exists()
    )


@pytest.mark.django_db
def test_draft_experience_entry_has_uuid_identity_ordering_and_cascade(vacancy):
    draft = create_draft(vacancy)
    first = create_experience_entry(draft, position=1, organization="Second", role_title="Later")
    second = create_experience_entry(
        draft,
        position=0,
        organization="First",
        role_title="Earlier",
        start_month=date(2023, 1, 1),
    )
    DraftExperienceEntry = apps.get_model("applications.DraftExperienceEntry")

    ordered = list(DraftExperienceEntry.objects.filter(draft=draft))

    assert isinstance(first.pk, uuid.UUID)
    assert isinstance(second.pk, uuid.UUID)
    assert ordered == [second, first]

    draft.delete()
    assert DraftExperienceEntry.objects.count() == 0


@pytest.mark.django_db
def test_draft_experience_entry_constraints_protect_position_and_current_end_consistency(vacancy):
    draft = create_draft(vacancy)
    create_experience_entry(draft, position=0)
    with pytest.raises(IntegrityError), transaction.atomic():
        create_experience_entry(draft, position=0, organization="Collision")

    with pytest.raises(IntegrityError), transaction.atomic():
        create_experience_entry(
            draft,
            position=1,
            is_current=True,
            end_month=date(2024, 2, 1),
        )

    with pytest.raises(IntegrityError), transaction.atomic():
        create_experience_entry(
            draft,
            position=1,
            is_current=False,
            end_month=None,
        )


@pytest.mark.django_db(transaction=True)
def test_draft_experience_entry_migration_is_reversible_and_drift_free():
    previous = [("applications", "0002_applicationdraft_credential_revoked_at_and_more")]
    current = [("applications", "0003_draftexperienceentry")]
    executor = MigrationExecutor(connection)

    executor.migrate(previous)
    state = executor.loader.project_state(previous).apps
    with pytest.raises(LookupError):
        state.get_model("applications", "DraftExperienceEntry")

    executor.loader.build_graph()
    executor.migrate(current)
    state = executor.loader.project_state(current).apps
    DraftExperienceEntry = state.get_model("applications", "DraftExperienceEntry")
    constraint_names = {constraint.name for constraint in DraftExperienceEntry._meta.constraints}
    index_names = {index.name for index in DraftExperienceEntry._meta.indexes}
    assert constraint_names == {
        "uniq_draft_experience_position",
        "draft_exp_current_end_consistent",
    }
    assert index_names == {"draft_exp_entry_order_idx"}

    executor.loader.build_graph()
    executor.migrate(previous)
    state = executor.loader.project_state(previous).apps
    with pytest.raises(LookupError):
        state.get_model("applications", "DraftExperienceEntry")

    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db
def test_generated_credential_is_256_bit_urlsafe_and_only_hash_is_persisted(vacancy):
    draft = create_draft(vacancy)

    credential = generate_credential(draft)
    draft.save(update_fields=["secret_hash"])
    parsed = parse_credential(credential)
    draft.refresh_from_db()

    assert credential.startswith(f"v1.{draft.pk}.")
    assert parsed.draft_id == draft.pk
    assert len(parsed.secret) == 43
    assert len(base64.urlsafe_b64decode(f"{parsed.secret}=")) == 32
    assert "=" not in parsed.secret
    assert parsed.secret not in draft.secret_hash
    assert credential not in draft.secret_hash
    assert identify_hasher(draft.secret_hash).algorithm
    assert verify_credential(credential).pk == draft.pk


@pytest.mark.django_db
@pytest.mark.parametrize(
    "credential",
    [
        "",
        "v2.00000000-0000-4000-8000-000000000000.secret",
        "v1.not-a-uuid.secret",
        "v1.00000000-0000-4000-8000-000000000000.",
        "v1.00000000-0000-4000-8000-000000000000.bad secret",
        f"v1.00000000-0000-4000-8000-000000000000.{'x' * 44}",
    ],
)
def test_malformed_credentials_are_rejected_generically(credential):
    with pytest.raises(CredentialError):
        parse_credential(credential)


@pytest.mark.django_db
def test_wrong_cross_draft_and_revoked_credentials_are_rejected(vacancy):
    first = create_draft(vacancy)
    second = create_draft(vacancy)
    first_credential = generate_credential(first)
    second_credential = generate_credential(second)
    first.save(update_fields=["secret_hash"])
    second.save(update_fields=["secret_hash"])

    first_secret = parse_credential(first_credential).secret
    cross_draft = f"v1.{second.pk}.{first_secret}"
    with pytest.raises(CredentialError):
        verify_credential(cross_draft)

    first.credential_revoked_at = timezone.now()
    first.save(update_fields=["credential_revoked_at"])
    with pytest.raises(CredentialError):
        verify_credential(first_credential)

    assert verify_credential(second_credential).pk == second.pk


@pytest.mark.django_db
def test_missing_draft_uses_exactly_one_dummy_password_check():
    credential = f"v1.{uuid.uuid4()}.{'x' * 43}"

    with patch("apps.applications.models.check_password", return_value=False) as password_check:
        with pytest.raises(CredentialError):
            verify_credential(credential)

    password_check.assert_called_once()
    assert password_check.call_args.args[0] == "x" * 43


@pytest.mark.django_db
def test_existing_draft_wrong_secret_uses_exactly_one_real_password_check(vacancy):
    draft = create_draft(vacancy)
    credential = f"v1.{draft.pk}.{'x' * 43}"

    with patch("apps.applications.models.check_password", return_value=False) as password_check:
        with pytest.raises(CredentialError):
            verify_credential(credential)

    password_check.assert_called_once_with("x" * 43, draft.secret_hash)


@pytest.mark.django_db
@pytest.mark.parametrize("terminal_status", ["abandoned", "expired", "submitted"])
def test_terminal_drafts_are_unavailable_to_credentials(vacancy, terminal_status):
    draft = create_draft(vacancy)
    credential = generate_credential(draft)
    draft.status = terminal_status
    if terminal_status == "submitted":
        draft.submitted_at = timezone.now()
        draft.save(update_fields=["secret_hash", "status", "submitted_at"])
    else:
        draft.save(update_fields=["secret_hash", "status"])

    with pytest.raises(CredentialError):
        verify_credential(credential)
