from django.urls import path

from apps.applications.views import (
    ActiveDraftView,
    CandidatePatchView,
    DraftCollectionView,
    DraftDetailView,
    ExperiencePatchView,
)
from apps.vacancies.views import VacancyDetailView, VacancyListView

from .api_views import HealthView, csrf_bootstrap

app_name = "api_v1"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("csrf/", csrf_bootstrap, name="csrf"),
    path("application-drafts/", DraftCollectionView.as_view(), name="draft-collection"),
    path("application-drafts/active/", ActiveDraftView.as_view(), name="draft-active"),
    path(
        "application-drafts/<uuid:draft_id>/",
        DraftDetailView.as_view(),
        name="draft-detail",
    ),
    path(
        "application-drafts/<uuid:draft_id>/candidate/",
        CandidatePatchView.as_view(),
        name="draft-candidate",
    ),
    path(
        "application-drafts/<uuid:draft_id>/experience/",
        ExperiencePatchView.as_view(),
        name="draft-experience",
    ),
    path("vacancies/", VacancyListView.as_view(), name="vacancy-list"),
    path("vacancies/<slug:slug>/", VacancyDetailView.as_view(), name="vacancy-detail"),
]
