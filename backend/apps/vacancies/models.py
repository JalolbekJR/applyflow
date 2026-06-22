import uuid

from django.db import models
from django.db.models import Q

from .validators import validate_string_list


class Vacancy(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    class WorkFormat(models.TextChoices):
        HYBRID = "hybrid", "Hybrid"
        REMOTE_FRIENDLY = "remote_friendly", "Remote-friendly"
        ON_SITE = "on_site", "On-site"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500)
    description = models.TextField()
    responsibilities = models.JSONField(default=list, validators=[validate_string_list])
    requirements = models.JSONField(default=list, validators=[validate_string_list])
    benefits = models.JSONField(default=list, validators=[validate_string_list])
    location = models.CharField(max_length=160)
    work_format = models.CharField(max_length=32, choices=WorkFormat.choices)
    employment_type = models.CharField(max_length=32, choices=EmploymentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    closing_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)
        indexes = [models.Index(fields=("status", "closing_at"), name="vacancy_public_idx")]
        constraints = [
            models.CheckConstraint(
                condition=~Q(status="published") | Q(published_at__isnull=False),
                name="vacancy_published_at_required",
            )
        ]

    def __str__(self) -> str:
        return self.title
