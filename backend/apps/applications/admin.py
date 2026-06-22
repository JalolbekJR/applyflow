from django.contrib import admin

from .models import Application, ApplicationDraft


@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "vacancy", "status", "expires_at", "updated_at")
    list_filter = ("status", "vacancy")
    search_fields = ("id", "vacancy__slug")
    exclude = ("secret_hash",)
    readonly_fields = ("id", "created_at", "updated_at", "submitted_at")


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
