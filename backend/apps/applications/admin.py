from django.contrib import admin

from .models import Application, ApplicationDraft, DraftExperienceEntry


@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vacancy",
        "status",
        "version",
        "last_activity_at",
        "expires_at",
    )
    list_filter = ("status", "vacancy")
    search_fields = ("id", "vacancy__slug")
    exclude = ("secret_hash", "creation_key_digest")
    readonly_fields = (
        "id",
        "version",
        "last_activity_at",
        "credential_revoked_at",
        "created_at",
        "updated_at",
        "submitted_at",
    )


@admin.register(DraftExperienceEntry)
class DraftExperienceEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "draft",
        "position",
        "organization",
        "role_title",
        "start_month",
        "end_month",
        "is_current",
        "updated_at",
    )
    list_filter = ("is_current",)
    search_fields = ("id", "draft__id")
    readonly_fields = (
        "id",
        "draft",
        "organization",
        "role_title",
        "start_month",
        "end_month",
        "is_current",
        "summary",
        "position",
        "created_at",
        "updated_at",
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_reference",
        "vacancy",
        "status",
        "submitted_at",
        "updated_at",
    )
    list_filter = ("status", "vacancy")
    search_fields = ("application_reference", "vacancy__slug")
    exclude = ("status_lookup_secret_hash",)
    readonly_fields = (
        "id",
        "vacancy",
        "full_name",
        "email",
        "email_normalized",
        "phone",
        "portfolio_url",
        "preferred_contact_method",
        "experience_level",
        "skills",
        "optional_message",
        "consent_version",
        "application_reference",
        "consented_at",
        "submitted_at",
        "created_at",
        "updated_at",
    )
