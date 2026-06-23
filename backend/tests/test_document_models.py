from datetime import timedelta

import pytest
from django.apps import apps
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


def model(name: str):
    return apps.get_model(name)


@pytest.fixture
def vacancy(db):
    Vacancy = model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="document-engineer",
        title="Document Engineer",
        summary="Build private document flows.",
        description="A fictional vacancy used for document metadata tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


def draft_for(vacancy):
    return model("applications.ApplicationDraft").objects.create(
        vacancy=vacancy,
        secret_hash="fictional-document-draft-hash",
        expires_at=timezone.now() + timedelta(days=7),
    )


def document_metadata(draft, **overrides):
    payload = {
        "draft": draft,
        "original_name_display": "avery-example-cv.pdf",
        "storage_key": "drafts/11111111-2222-4333-8444-555555555555/"
        "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee.pdf",
        "detected_content_type": "application/pdf",
        "size": 1024,
        "sha256": "a" * 64,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db(transaction=True)
def test_document_checksum_cleanup_constraint_and_history(vacancy):
    ApplicationDocument = model("documents.ApplicationDocument")
    draft = draft_for(vacancy)
    active = ApplicationDocument.objects.create(**document_metadata(draft))
    history = ApplicationDocument.objects.create(
        **document_metadata(
            draft,
            storage_key="drafts/11111111-2222-4333-8444-555555555555/"
            "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff.pdf",
            deleted_at=timezone.now(),
            storage_deleted_at=timezone.now(),
        )
    )

    assert active.sha256 == "a" * 64
    assert history.storage_deleted_at is not None
    with pytest.raises(IntegrityError), transaction.atomic():
        ApplicationDocument.objects.create(
            **document_metadata(
                draft,
                storage_key="drafts/11111111-2222-4333-8444-555555555555/"
                "cccccccc-dddd-4eee-8fff-000000000000.pdf",
                storage_deleted_at=timezone.now(),
            )
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        ApplicationDocument.objects.create(
            **document_metadata(
                draft,
                storage_key="drafts/11111111-2222-4333-8444-555555555555/"
                "dddddddd-eeee-4fff-8000-111111111111.pdf",
            )
        )


@pytest.mark.django_db(transaction=True)
def test_document_migration_forward_reverse_reapply():
    previous = [("documents", "0001_initial")]
    current = [("documents", "0002_applicationdocument_sha256_and_more")]
    executor = MigrationExecutor(connection)

    executor.migrate(previous)
    state = executor.loader.project_state(previous).apps
    ApplicationDocument = state.get_model("documents", "ApplicationDocument")
    assert not any(field.name == "sha256" for field in ApplicationDocument._meta.fields)

    executor.loader.build_graph()
    executor.migrate(current)
    state = executor.loader.project_state(current).apps
    ApplicationDocument = state.get_model("documents", "ApplicationDocument")
    field_names = {field.name for field in ApplicationDocument._meta.fields}
    assert {"sha256", "storage_deleted_at"} <= field_names
    assert {index.name for index in ApplicationDocument._meta.indexes} == {"doc_cleanup_idx"}
    assert "doc_storage_deleted_requires_deleted" in {
        constraint.name for constraint in ApplicationDocument._meta.constraints
    }

    executor.loader.build_graph()
    executor.migrate(previous)
    state = executor.loader.project_state(previous).apps
    ApplicationDocument = state.get_model("documents", "ApplicationDocument")
    assert not any(field.name == "sha256" for field in ApplicationDocument._meta.fields)

    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())
