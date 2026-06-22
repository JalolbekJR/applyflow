from django.urls import path

from apps.vacancies.views import VacancyDetailView, VacancyListView

from .api_views import HealthView

app_name = "api_v1"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("vacancies/", VacancyListView.as_view(), name="vacancy-list"),
    path("vacancies/<slug:slug>/", VacancyDetailView.as_view(), name="vacancy-detail"),
]
