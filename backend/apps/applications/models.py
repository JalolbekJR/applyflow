import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.db.models import Q

from apps.vacancies.models import Vacancy
from apps.vacancies.validators import validate_string_list


class CandidateFields(models.Model):
    class ContactMethod(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"

    class ExperienceLevel(models.TextChoices):
        EARLY_CAREER = "early_career", "Early career"
        MID_LEVEL = "mid_level", "Mid-level"
        SENIOR = "senior", "Senior"

    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    email_normalized = models.CharField(max_length=254, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    portfolio_url = models.URLField(max_length=500, blank=True)
    preferred_contact_method = models.CharField(
        max_length=16, choices=ContactMethod.choices, blank=True
    )
    experience_level = models.CharField(max_length=24, choices=ExperienceLevel.choices, blank=True)
    skills = models.JSONField(default=list, validators=[validate_string_list])
    optional_message = models.TextField(max_length=1200, blank=True)
    consent_version = models.CharField(max_length=64, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.email_normalized = self.email.strip().casefold()
        return super().save(*args, **kwargs)


class ApplicationDraft(CandidateFields):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUBMITTED = "submitted", "Submitted"
        ABANDONED = "abandoned", "Abandoned"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.PROTECT, related_name="drafts")
    secret_hash = models.CharField(max_length=256, unique=True)
    consent_acknowledged = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=("status", "expires_at"), name="draft_expiry_idx")]
        constraints = [
            models.CheckConstraint(
                condition=(Q(status="submitted") & Q(submitted_at__isnull=False))
                | (~Q(status="submitted") & Q(submitted_at__isnull=True)),
                name="draft_submitted_at_matches_status",
            )
        ]

    def __str__(self) -> str:
        return f"Draft {self.pk}"

    def set_secret(self, raw_secret: str) -> None:
        self.secret_hash = make_password(raw_secret)

    def check_secret(self, raw_secret: str) -> bool:
        return check_password(raw_secret, self.secret_hash)


class Application(CandidateFields):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.PROTECT, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    application_reference = models.CharField(max_length=32, unique=True)
    status_lookup_secret_hash = models.CharField(max_length=256)
    consented_at = models.DateTimeField()
    submitted_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-submitted_at",)
        indexes = [models.Index(fields=("vacancy", "status"), name="application_review_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=("vacancy", "email_normalized"),
                name="uniq_application_vacancy_email",
            )
        ]

    def __str__(self) -> str:
        return self.application_reference

    def set_status_lookup_secret(self, raw_secret: str) -> None:
        self.status_lookup_secret_hash = make_password(raw_secret)

    def check_status_lookup_secret(self, raw_secret: str) -> bool:
        return check_password(raw_secret, self.status_lookup_secret_hash)
