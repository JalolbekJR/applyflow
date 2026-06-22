import pytest
from django.apps import apps
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def published_vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="frontend-developer",
        title="Frontend Developer",
        summary="Build accessible candidate-facing interfaces.",
        description="A fictional vacancy used for API tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


@pytest.fixture
def unpublished_vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="unpublished-role",
        title="Unpublished Role",
        summary="Not available through the public API.",
        description="A fictional unpublished vacancy.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="draft",
    )


@pytest.mark.django_db
def test_health_endpoint_returns_only_status(api_client):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_vacancy_endpoints_are_read_only_and_exclude_unpublished_records(
    api_client, published_vacancy, unpublished_vacancy
):
    response = api_client.get("/api/v1/vacancies/")
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == [published_vacancy.slug]
    mutation = api_client.post("/api/v1/vacancies/", {})
    assert mutation.status_code == 405
    assert mutation.json()["error"]["code"] == "method_not_allowed"


@pytest.mark.django_db
def test_published_vacancy_detail_returns_only_public_fields(api_client, published_vacancy):
    response = api_client.get(f"/api/v1/vacancies/{published_vacancy.slug}/")

    assert response.status_code == 200
    assert set(response.json()) == {
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
    }
    assert response.json()["slug"] == published_vacancy.slug


@pytest.mark.django_db
def test_unpublished_vacancy_detail_returns_generic_not_found_envelope(
    api_client, unpublished_vacancy
):
    response = api_client.get(f"/api/v1/vacancies/{unpublished_vacancy.slug}/")

    assert response.status_code == 404
    payload = response.json()
    assert set(payload) == {"error"}
    assert set(payload["error"]) == {"code", "message", "fields", "request_id"}
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "The requested resource was not found."
    assert payload["error"]["fields"] == {}
    assert isinstance(payload["error"]["request_id"], str)
    assert payload["error"]["request_id"]
    assert payload["error"]["request_id"].startswith("req_")

    serialized_payload = response.content.decode("utf-8")
    private_values = {
        unpublished_vacancy.slug,
        unpublished_vacancy.title,
        unpublished_vacancy.summary,
        unpublished_vacancy.description,
        unpublished_vacancy.location,
        unpublished_vacancy.work_format,
        unpublished_vacancy.employment_type,
        unpublished_vacancy.status,
    }

    for private_value in private_values:
        assert private_value not in serialized_payload


@pytest.mark.django_db
def test_api_errors_use_the_documented_envelope(api_client):
    response = api_client.get("/api/v1/vacancies/missing-role/")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "The requested resource was not found."
    assert payload["error"]["fields"] == {}
    assert payload["error"]["request_id"].startswith("req_")
