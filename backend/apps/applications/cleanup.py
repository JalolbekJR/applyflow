from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.documents.models import ApplicationDocument
from apps.documents.storage import DocumentStorageError, get_document_storage
from apps.documents.storage_keys import DRAFT_CV_STORAGE_PREFIX, validate_document_storage_key

from .models import ApplicationDraft, DraftExperienceEntry

DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000
DEFAULT_ORPHAN_GRACE_HOURS = 24
ORPHAN_STORAGE_PREFIX = f"{DRAFT_CV_STORAGE_PREFIX}/"

CANDIDATE_SCRUB_VALUES = {
    "full_name": "",
    "email": "",
    "email_normalized": "",
    "phone": "",
    "portfolio_url": "",
    "preferred_contact_method": "",
    "experience_level": "",
    "skills": [],
    "optional_message": "",
    "consent_acknowledged": False,
    "consent_version": "",
}

SUMMARY_FIELDS = (
    "mode",
    "batch_size",
    "orphan_grace_hours",
    "expired_drafts_selected",
    "expired_drafts_transitioned",
    "terminal_drafts_checked",
    "terminal_drafts_scrubbed",
    "pending_documents_selected",
    "pending_documents_deleted",
    "pending_documents_already_missing",
    "pending_document_failures",
    "orphan_objects_selected",
    "orphan_objects_deleted",
    "orphan_objects_skipped",
    "orphan_object_failures",
    "draft_shells_selected",
    "draft_shells_hard_deleted",
    "draft_shells_retained",
    "total_failures",
)


@dataclass
class CleanupSummary:
    mode: str
    batch_size: int
    orphan_grace_hours: int
    expired_drafts_selected: int = 0
    expired_drafts_transitioned: int = 0
    terminal_drafts_checked: int = 0
    terminal_drafts_scrubbed: int = 0
    pending_documents_selected: int = 0
    pending_documents_deleted: int = 0
    pending_documents_already_missing: int = 0
    pending_document_failures: int = 0
    orphan_objects_selected: int = 0
    orphan_objects_deleted: int = 0
    orphan_objects_skipped: int = 0
    orphan_object_failures: int = 0
    draft_shells_selected: int = 0
    draft_shells_hard_deleted: int = 0
    draft_shells_retained: int = 0

    @property
    def total_failures(self) -> int:
        return self.pending_document_failures + self.orphan_object_failures

    def lines(self) -> list[str]:
        return [f"{field}={getattr(self, field)}" for field in SUMMARY_FIELDS]


def cleanup_application_drafts(
    *,
    apply: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
    orphan_grace_hours: int = DEFAULT_ORPHAN_GRACE_HOURS,
    now=None,
):
    now = now or timezone.now()
    storage = get_document_storage()
    summary = CleanupSummary(
        mode="apply" if apply else "dry-run",
        batch_size=batch_size,
        orphan_grace_hours=orphan_grace_hours,
    )

    process_expired_active_drafts(summary, apply=apply, batch_size=batch_size, now=now)
    process_terminal_draft_shells(summary, apply=apply, batch_size=batch_size, now=now)
    process_pending_document_deletions(
        summary,
        apply=apply,
        batch_size=batch_size,
        now=now,
        storage=storage,
    )
    process_orphan_storage_objects(
        summary,
        apply=apply,
        batch_size=batch_size,
        orphan_grace_hours=orphan_grace_hours,
        storage=storage,
        now=now,
    )
    process_hard_delete_draft_shells(summary, apply=apply, batch_size=batch_size)
    return summary


def process_expired_active_drafts(
    summary: CleanupSummary,
    *,
    apply: bool,
    batch_size: int,
    now,
) -> None:
    draft_ids = list(
        ApplicationDraft.objects.filter(
            status=ApplicationDraft.Status.ACTIVE,
            expires_at__lte=now,
        )
        .order_by("created_at", "id")
        .values_list("pk", flat=True)[:batch_size]
    )
    summary.expired_drafts_selected = len(draft_ids)
    for draft_id in draft_ids:
        if apply:
            if transition_expired_draft(draft_id, now=now):
                summary.expired_drafts_transitioned += 1
            continue
        draft = ApplicationDraft.objects.select_related("vacancy").filter(pk=draft_id).first()
        if (
            draft is not None
            and draft.status == ApplicationDraft.Status.ACTIVE
            and not draft.ownership_is_revoked()
            and draft.is_expired(now=now)
        ):
            summary.expired_drafts_transitioned += 1


def transition_expired_draft(draft_id, *, now) -> bool:
    with transaction.atomic():
        try:
            draft = (
                ApplicationDraft.objects.select_for_update()
                .select_related("vacancy")
                .get(pk=draft_id)
            )
        except ApplicationDraft.DoesNotExist:
            return False
        if draft.status != ApplicationDraft.Status.ACTIVE:
            return False
        if draft.ownership_is_revoked() or not draft.is_expired(now=now):
            return False
        prepare_terminal_draft(
            draft,
            status=ApplicationDraft.Status.EXPIRED,
            now=now,
            increment_version=True,
        )
        return True


def process_terminal_draft_shells(
    summary: CleanupSummary,
    *,
    apply: bool,
    batch_size: int,
    now,
) -> None:
    draft_ids = list(
        ApplicationDraft.objects.filter(status__in=terminal_statuses())
        .order_by("created_at", "id")
        .values_list("pk", flat=True)[:batch_size]
    )
    summary.terminal_drafts_checked = len(draft_ids)
    for draft_id in draft_ids:
        if apply:
            if scrub_terminal_draft(draft_id, now=now):
                summary.terminal_drafts_scrubbed += 1
            continue
        draft = ApplicationDraft.objects.filter(pk=draft_id).first()
        if draft is not None and terminal_cleanup_needed(draft):
            summary.terminal_drafts_scrubbed += 1


def scrub_terminal_draft(draft_id, *, now) -> bool:
    with transaction.atomic():
        try:
            draft = ApplicationDraft.objects.select_for_update().get(pk=draft_id)
        except ApplicationDraft.DoesNotExist:
            return False
        if draft.status not in terminal_statuses():
            return False
        return prepare_terminal_draft(draft, now=now, increment_version=False)


def prepare_terminal_draft(
    draft: ApplicationDraft,
    *,
    now,
    status: str | None = None,
    increment_version: bool = False,
) -> bool:
    changed_fields: list[str] = []
    if status is not None and draft.status != status:
        draft.status = status
        changed_fields.append("status")
        if increment_version:
            draft.version += 1
            changed_fields.append("version")
    if draft.credential_revoked_at is None:
        draft.credential_revoked_at = now
        changed_fields.append("credential_revoked_at")
    changed_fields.extend(scrub_candidate_fields(draft))
    if changed_fields:
        changed_fields.append("updated_at")
        draft.save(update_fields=changed_fields)

    entries_deleted = DraftExperienceEntry.objects.filter(draft=draft).delete()[0] > 0
    documents_updated = (
        ApplicationDocument.objects.filter(draft=draft, deleted_at__isnull=True).update(
            deleted_at=now,
            original_name_display="",
        )
        > 0
    )
    return bool(changed_fields or entries_deleted or documents_updated)


def scrub_candidate_fields(draft: ApplicationDraft) -> list[str]:
    changed_fields = []
    for field, scrubbed_value in CANDIDATE_SCRUB_VALUES.items():
        if getattr(draft, field) != scrubbed_value:
            setattr(
                draft,
                field,
                list(scrubbed_value) if isinstance(scrubbed_value, list) else scrubbed_value,
            )
            changed_fields.append(field)
    return changed_fields


def terminal_cleanup_needed(draft: ApplicationDraft) -> bool:
    if draft.status not in terminal_statuses():
        return False
    if draft.credential_revoked_at is None:
        return True
    if not candidate_fields_are_scrubbed(draft):
        return True
    if DraftExperienceEntry.objects.filter(draft=draft).exists():
        return True
    return ApplicationDocument.objects.filter(draft=draft, deleted_at__isnull=True).exists()


def candidate_fields_are_scrubbed(draft: ApplicationDraft) -> bool:
    return all(getattr(draft, field) == value for field, value in CANDIDATE_SCRUB_VALUES.items())


def process_pending_document_deletions(
    summary: CleanupSummary,
    *,
    apply: bool,
    batch_size: int,
    now,
    storage,
) -> None:
    document_ids = list(
        ApplicationDocument.objects.filter(
            deleted_at__isnull=False,
            storage_deleted_at__isnull=True,
        )
        .order_by("deleted_at", "uploaded_at", "id")
        .values_list("pk", flat=True)[:batch_size]
    )
    summary.pending_documents_selected = len(document_ids)
    if not apply:
        return

    for document_id in document_ids:
        try:
            result = delete_pending_document_storage(document_id, storage=storage, now=now)
        except Exception:
            summary.pending_document_failures += 1
            continue
        if result == "deleted":
            summary.pending_documents_deleted += 1
        elif result == "already_missing":
            summary.pending_documents_already_missing += 1
        elif result == "failed":
            summary.pending_document_failures += 1


def delete_pending_document_storage(document_id, *, storage, now) -> str:
    captured = capture_pending_document(document_id)
    if captured is None:
        return "stale"
    storage_key = captured
    try:
        existed_before = storage.exists(storage_key)
        storage.delete(storage_key)
    except DocumentStorageError:
        return "failed"

    if not record_document_storage_deleted(document_id, now=now):
        return "failed"
    return "deleted" if existed_before else "already_missing"


def capture_pending_document(document_id) -> str | None:
    with transaction.atomic():
        try:
            document = ApplicationDocument.objects.select_for_update().get(pk=document_id)
        except ApplicationDocument.DoesNotExist:
            return None
        if document.deleted_at is None:
            return None
        if document.storage_deleted_at is not None:
            return None
        return validate_document_storage_key(document.storage_key)


def record_document_storage_deleted(document_id, *, now) -> bool:
    with transaction.atomic():
        try:
            document = ApplicationDocument.objects.select_for_update().get(pk=document_id)
        except ApplicationDocument.DoesNotExist:
            return True
        if document.storage_deleted_at is not None:
            return True
        if document.deleted_at is None:
            return False
        document.storage_deleted_at = now
        document.save(update_fields=["storage_deleted_at"])
    return True


def process_orphan_storage_objects(
    summary: CleanupSummary,
    *,
    apply: bool,
    batch_size: int,
    orphan_grace_hours: int,
    storage,
    now,
) -> None:
    cutoff = now - timedelta(hours=orphan_grace_hours)
    try:
        keys = storage.iter_keys(
            prefix=ORPHAN_STORAGE_PREFIX,
            older_than=cutoff,
            limit=batch_size,
        )
    except DocumentStorageError:
        summary.orphan_object_failures += 1
        return

    summary.orphan_objects_selected = len(keys)
    for key in keys:
        try:
            if storage_key_is_referenced(key):
                summary.orphan_objects_skipped += 1
                continue
            if not apply:
                continue
            if storage_key_is_referenced(key):
                summary.orphan_objects_skipped += 1
                continue
            if not storage_key_is_still_older_than(storage, key, cutoff):
                summary.orphan_objects_skipped += 1
                continue
            storage.delete(key)
            summary.orphan_objects_deleted += 1
        except DocumentStorageError:
            summary.orphan_object_failures += 1


def storage_key_is_referenced(key: str) -> bool:
    return ApplicationDocument.objects.filter(storage_key=key).exists()


def storage_key_is_still_older_than(storage, key: str, cutoff) -> bool:
    prefix = storage_prefix_for_key(key)
    keys = storage.iter_keys(prefix=prefix, older_than=cutoff, limit=MAX_BATCH_SIZE)
    return key in keys


def storage_prefix_for_key(key: str) -> str:
    validated_key = validate_document_storage_key(key)
    namespace, draft_id, _document_name = validated_key.split("/")
    return f"{namespace}/{draft_id}/"


def process_hard_delete_draft_shells(
    summary: CleanupSummary,
    *,
    apply: bool,
    batch_size: int,
) -> None:
    draft_ids = list(
        ApplicationDraft.objects.filter(status__in=terminal_statuses())
        .order_by("created_at", "id")
        .values_list("pk", flat=True)[:batch_size]
    )
    summary.draft_shells_selected = len(draft_ids)
    for draft_id in draft_ids:
        if apply:
            if hard_delete_draft_shell(draft_id):
                summary.draft_shells_hard_deleted += 1
            else:
                summary.draft_shells_retained += 1
            continue
        if hard_delete_ready(draft_id):
            summary.draft_shells_hard_deleted += 1
        else:
            summary.draft_shells_retained += 1


def hard_delete_draft_shell(draft_id) -> bool:
    with transaction.atomic():
        try:
            draft = ApplicationDraft.objects.select_for_update().get(pk=draft_id)
        except ApplicationDraft.DoesNotExist:
            return False
        if not hard_delete_ready_for_locked_draft(draft):
            return False
        draft.delete()
        return True


def hard_delete_ready(draft_id) -> bool:
    draft = ApplicationDraft.objects.filter(pk=draft_id).first()
    if draft is None:
        return False
    return hard_delete_ready_for_locked_draft(draft)


def hard_delete_ready_for_locked_draft(draft: ApplicationDraft) -> bool:
    if draft.status not in terminal_statuses():
        return False
    if draft.credential_revoked_at is None:
        return False
    if not candidate_fields_are_scrubbed(draft):
        return False
    if DraftExperienceEntry.objects.filter(draft=draft).exists():
        return False
    if ApplicationDocument.objects.filter(draft=draft, deleted_at__isnull=True).exists():
        return False
    return not ApplicationDocument.objects.filter(
        draft=draft,
        deleted_at__isnull=False,
        storage_deleted_at__isnull=True,
    ).exists()


def terminal_statuses() -> tuple[str, str]:
    return (ApplicationDraft.Status.ABANDONED, ApplicationDraft.Status.EXPIRED)
