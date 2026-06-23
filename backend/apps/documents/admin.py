from django.contrib import admin

from .models import ApplicationDocument


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "original_name_display",
        "draft",
        "application",
        "detected_content_type",
        "size",
        "uploaded_at",
        "deleted_at",
        "storage_deleted_at",
    )
    list_filter = ("detected_content_type", "deleted_at", "storage_deleted_at")
    search_fields = ("id", "draft__id", "application__application_reference")
    exclude = ("storage_key", "sha256")
    readonly_fields = (
        "id",
        "draft",
        "application",
        "original_name_display",
        "detected_content_type",
        "size",
        "uploaded_at",
        "deleted_at",
        "storage_deleted_at",
    )
