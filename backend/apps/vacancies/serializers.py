from rest_framework import serializers

from .models import Vacancy


class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = (
            "slug",
            "title",
            "summary",
            "description",
            "responsibilities",
            "requirements",
            "benefits",
            "location",
            "work_format",
            "employment_type",
            "status",
            "published_at",
            "closing_at",
        )
        read_only_fields = fields
