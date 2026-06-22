from datetime import timedelta

import pytest
from django.apps import apps
from django.contrib.auth.hashers import identify_hasher
from django.db import IntegrityError, transaction
from django.utils import timezone


def model(name: str):
    return apps.get_model(name)


@pytest.fixture
def vacancy(db):
    Vacancy = model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="frontend-developer",
        title="Frontend Developer",
        summary="Build accessible candidate-facing interfaces.",
        description="A fictional vacancy used for backend tests.",
        location="Tashkent, Uzbekistan",
        work_format=Vacancy.WorkFormat.HYBRID,
        employment_type=Vacancy.EmploymentType.FULL_TIME,
        status=Vacancy.Status.PUBLISHED,
        published_at=timezone.now(),
    )


@pytest.mark.django_db
def test_vacancy_uses_uuid_and_explicit_status(vacancy):
    assert vacancy.pk.version == 4
    assert vacancy.status == "published"
    assert {choice for choice, _ in vacancy.Status.choices} == {"draft", "published", "closed"}


@pytest.mark.django_db(transaction=True)
def test_vacancy_slug_is_unique(vacancy):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            model("vacancies.Vacancy").objects.create(
                slug=vacancy.slug,
                title="Duplicate",
                summary="Duplicate fictional vacancy.",
                description="Duplicate fictional vacancy.",
                location="Tashkent, Uzbekistan",
                work_format="hybrid",
                employment_type="full_time",
            )


@pytest.mark.django_db
def test_draft_hashes_credentials_and_never_stores_the_raw_value(vacancy):
    ApplicationDraft = model("applications.ApplicationDraft")
    draft = ApplicationDraft(
        vacancy=vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    draft.set_secret("draft-secret-fictional-value")
    draft.save()

    assert draft.secret_hash != "draft-secret-fictional-value"
    assert draft.check_secret("draft-secret-fictional-value") is True
    assert draft.check_secret("wrong-value") is False


@pytest.mark.django_db
def test_draft_and_submitted_application_are_separate_records(vacancy):
    ApplicationDraft = model("applications.ApplicationDraft")
    Application = model("applications.Application")
    draft = ApplicationDraft.objects.create(
        vacancy=vacancy,
        secret_hash="test-hash",
        full_name="Avery Example",
        email="avery@example.test",
        email_normalized="avery@example.test",
        expires_at=timezone.now() + timedelta(days=7),
    )
    application = Application.objects.create(
        vacancy=vacancy,
        full_name=draft.full_name,
        email=draft.email,
        email_normalized=draft.email_normalized,
        consent_version="test-v1",
        consented_at=timezone.now(),
        application_reference="AF-TEST-0001",
        status_lookup_secret_hash="test-hash",
        submitted_at=timezone.now(),
    )

    assert draft.pk != application.pk
    assert draft.status == ApplicationDraft.Status.ACTIVE
    assert application.status == Application.Status.SUBMITTED


@pytest.mark.django_db(transaction=True)
def test_application_reference_and_vacancy_email_pair_are_unique(vacancy):
    Application = model("applications.Application")
    values = {
        "vacancy": vacancy,
        "full_name": "Avery Example",
        "email": "avery@example.test",
        "email_normalized": "avery@example.test",
        "consent_version": "test-v1",
        "consented_at": timezone.now(),
        "status_lookup_secret_hash": "test-hash",
        "submitted_at": timezone.now(),
    }
    Application.objects.create(application_reference="AF-TEST-0001", **values)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Application.objects.create(application_reference="AF-TEST-0002", **values)


@pytest.mark.django_db(transaction=True)
def test_application_public_reference_is_unique_independently_of_vacancy_email(vacancy):
    Application = model("applications.Application")
    now = timezone.now()
    Application.objects.create(
        vacancy=vacancy,
        full_name="Avery Example",
        email="avery@example.test",
        consent_version="test-v1",
        consented_at=now,
        application_reference="AF-TEST-UNIQUE",
        status_lookup_secret_hash="first-test-hash",
        submitted_at=now,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Application.objects.create(
                vacancy=vacancy,
                full_name="Jordan Example",
                email="jordan@example.test",
                consent_version="test-v1",
                consented_at=now,
                application_reference="AF-TEST-UNIQUE",
                status_lookup_secret_hash="second-test-hash",
                submitted_at=now,
            )


@pytest.mark.django_db
def test_application_status_secret_is_hashed_and_verifies_after_reload(vacancy):
    Application = model("applications.Application")
    raw_secret = "status-secret-fictional-value"
    application = Application(
        vacancy=vacancy,
        full_name="Avery Example",
        email="avery@example.test",
        consent_version="test-v1",
        consented_at=timezone.now(),
        application_reference="AF-TEST-STATUS",
        submitted_at=timezone.now(),
    )
    application.set_status_lookup_secret(raw_secret)
    application.save()
    application.refresh_from_db()

    assert application.status_lookup_secret_hash != raw_secret
    assert identify_hasher(application.status_lookup_secret_hash).algorithm
    assert application.check_status_lookup_secret(raw_secret) is True
    assert application.check_status_lookup_secret("wrong-value") is False


@pytest.mark.django_db
def test_application_status_choices_are_limited(vacancy):
    Application = model("applications.Application")
    assert {choice for choice, _ in Application.Status.choices} == {
        "submitted",
        "under_review",
        "closed",
    }


@pytest.mark.django_db(transaction=True)
def test_document_metadata_requires_exactly_one_owner(vacancy):
    ApplicationDraft = model("applications.ApplicationDraft")
    Application = model("applications.Application")
    ApplicationDocument = model("documents.ApplicationDocument")
    draft = ApplicationDraft.objects.create(
        vacancy=vacancy,
        secret_hash="draft-hash",
        expires_at=timezone.now() + timedelta(days=7),
    )
    application = Application.objects.create(
        vacancy=vacancy,
        full_name="Avery Example",
        email="avery@example.test",
        email_normalized="avery@example.test",
        consent_version="test-v1",
        consented_at=timezone.now(),
        application_reference="AF-TEST-0003",
        status_lookup_secret_hash="status-hash",
        submitted_at=timezone.now(),
    )
    metadata = {
        "original_name_display": "avery-example-cv.pdf",
        "storage_key": "documents/fictional-key.pdf",
        "detected_content_type": "application/pdf",
        "size": 1024,
    }

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ApplicationDocument.objects.create(**metadata)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ApplicationDocument.objects.create(draft=draft, application=application, **metadata)


@pytest.mark.django_db(transaction=True)
def test_draft_allows_only_one_active_document_but_keeps_inactive_history(vacancy):
    ApplicationDraft = model("applications.ApplicationDraft")
    ApplicationDocument = model("documents.ApplicationDocument")
    draft = ApplicationDraft.objects.create(
        vacancy=vacancy,
        secret_hash="draft-active-document-hash",
        expires_at=timezone.now() + timedelta(days=7),
    )
    metadata = {
        "draft": draft,
        "original_name_display": "avery-example-cv.pdf",
        "detected_content_type": "application/pdf",
        "size": 1024,
    }
    ApplicationDocument.objects.create(
        storage_key="documents/draft-active.pdf",
        **metadata,
    )
    ApplicationDocument.objects.create(
        storage_key="documents/draft-history.pdf",
        deleted_at=timezone.now(),
        **metadata,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ApplicationDocument.objects.create(
                storage_key="documents/draft-second-active.pdf",
                **metadata,
            )


@pytest.mark.django_db(transaction=True)
def test_application_allows_only_one_active_document_but_keeps_inactive_history(vacancy):
    Application = model("applications.Application")
    ApplicationDocument = model("documents.ApplicationDocument")
    now = timezone.now()
    application = Application.objects.create(
        vacancy=vacancy,
        full_name="Avery Example",
        email="avery@example.test",
        consent_version="test-v1",
        consented_at=now,
        application_reference="AF-TEST-DOCUMENT",
        status_lookup_secret_hash="application-document-test-hash",
        submitted_at=now,
    )
    metadata = {
        "application": application,
        "original_name_display": "avery-example-cv.pdf",
        "detected_content_type": "application/pdf",
        "size": 1024,
    }
    ApplicationDocument.objects.create(
        storage_key="documents/application-active.pdf",
        **metadata,
    )
    ApplicationDocument.objects.create(
        storage_key="documents/application-history.pdf",
        deleted_at=timezone.now(),
        **metadata,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ApplicationDocument.objects.create(
                storage_key="documents/application-second-active.pdf",
                **metadata,
            )
