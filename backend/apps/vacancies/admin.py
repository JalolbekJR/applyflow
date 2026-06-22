from django.contrib import admin

from .models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "location", "work_format", "published_at", "updated_at")
    list_filter = ("status", "work_format", "employment_type")
    search_fields = ("title", "slug", "location")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
