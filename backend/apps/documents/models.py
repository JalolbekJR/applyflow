import uuid

from django.db import models
from django.db.models import Q

from apps.applications.models import Application, ApplicationDraft


class ApplicationDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(
        ApplicationDraft,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    original_name_display = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=500, unique=True)
    detected_content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-uploaded_at",)
        constraints = [
            models.CheckConstraint(
                condition=(Q(draft__isnull=False) & Q(application__isnull=True))
                | (Q(draft__isnull=True) & Q(application__isnull=False)),
                name="document_exactly_one_owner",
            ),
            models.UniqueConstraint(
                fields=("draft",),
                condition=Q(deleted_at__isnull=True),
                name="uniq_active_document_per_draft",
            ),
            models.UniqueConstraint(
                fields=("application",),
                condition=Q(deleted_at__isnull=True),
                name="uniq_active_document_per_application",
            ),
        ]

    def __str__(self) -> str:
        return self.original_name_display
