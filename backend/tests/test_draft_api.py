import base64
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.apps import apps
from django.db import IntegrityError, close_old_connections, transaction
from django.test import Client, override_settings
from django.utils import timezone

from apps.applications.drafts import generate_credential


@pytest.fixture
def vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="backend-developer",
        title="Backend Developer",
        summary="Build reliable candidate services.",
        description="A fictional vacancy used for secure draft API tests.",
        location="Tashkent, Uzbekistan",
        work_format="hybrid",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


@pytest.fixture
def another_vacancy(db):
    Vacancy = apps.get_model("vacancies.Vacancy")
    return Vacancy.objects.create(
        slug="product-designer",
        title="Product Designer",
        summary="Design calm candidate experiences.",
        description="Another fictional vacancy used for conflict tests.",
        location="Tashkent, Uzbekistan",
        work_format="remote_friendly",
        employment_type="full_time",
        status="published",
        published_at=timezone.now(),
    )


def csrf_client():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/csrf/")
    return client, response.json()["csrf_token"]


def create_draft(client, vacancy, token):
    return client.post(
        "/api/v1/application-drafts/",
        {"vacancy_slug": vacancy.slug},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def assert_error(response, status, code):
    assert response.status_code == status
    payload = response.json()
    assert set(payload) == {"error"}
    assert set(payload["error"]) == {"code", "message", "fields", "request_id"}
    assert payload["error"]["code"] == code
    assert payload["error"]["fields"] == {}
    assert payload["error"]["request_id"].startswith("req_")
    assert response["X-Request-ID"] == payload["error"]["request_id"]
    assert response["Cache-Control"] == "no-store"


def assert_validation_error(response, *fields):
    assert response.status_code == 422
    payload = response.json()["error"]
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Check the highlighted fields."
    assert set(payload["fields"]) == set(fields)
    assert response["Cache-Control"] == "no-store"
    assert response["X-Request-ID"] == payload["request_id"]


def patch_draft(client, draft_id, section, payload, token, *, version=1):
    return client.patch(
        f"/api/v1/application-drafts/{draft_id}/{section}/",
        payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH=f'"draft-{version}"',
    )


@pytest.mark.django_db
def test_csrf_bootstrap_sets_masked_token_cookie_and_no_store_headers():
    client = Client(enforce_csrf_checks=True)

    response = client.get("/api/v1/csrf/")

    assert response.status_code == 200
    assert set(response.json()) == {"csrf_token"}
    assert len(response.json()["csrf_token"]) == 64
    assert "csrftoken" in response.cookies
    creation_cookie = response.cookies["applyflow_draft_creation"]
    assert creation_cookie["httponly"] is True
    assert creation_cookie["samesite"] == "Lax"
    assert creation_cookie["path"] == "/api/v1/application-drafts/"
    assert not creation_cookie["domain"]
    assert 0 < int(creation_cookie["max-age"]) <= 10 * 60
    assert len(base64.urlsafe_b64decode(f"{creation_cookie.value}=")) == 32
    assert creation_cookie.value not in response.content.decode()
    assert "no-store" in response["Cache-Control"]
    assert "Cookie" in response["Vary"]
    assert "applyflow_draft" not in response.content.decode()
    assert (
        client.post("/api/v1/csrf/", HTTP_X_CSRFTOKEN=response.json()["csrf_token"]).status_code
        == 405
    )


@pytest.mark.django_db
def test_unsafe_draft_requests_require_csrf_and_return_json_envelope(vacancy):
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        "/api/v1/application-drafts/",
        {"vacancy_slug": vacancy.slug},
        content_type="application/json",
    )

    assert_error(response, 403, "csrf_failed")
    assert response["Content-Type"].startswith("application/json")
    assert "DJANGO" not in response.content.decode()


@pytest.mark.django_db
def test_invalid_api_csrf_token_returns_json_envelope(vacancy):
    client, _ = csrf_client()

    response = client.post(
        "/api/v1/application-drafts/",
        {"vacancy_slug": vacancy.slug},
        content_type="application/json",
        HTTP_X_CSRFTOKEN="invalid-token",
    )

    assert_error(response, 403, "csrf_failed")
    assert response["Content-Type"].startswith("application/json")


@pytest.mark.django_db
def test_admin_csrf_failure_remains_django_html():
    response = Client(enforce_csrf_checks=True).post(
        "/admin/login/",
        {"username": "fictional-user", "password": "fictional-password"},
    )

    assert response.status_code == 403
    assert response["Content-Type"].startswith("text/html")
    assert b"csrf_failed" not in response.content


@pytest.mark.django_db
@override_settings(DRAFT_COOKIE_SECURE=True)
def test_create_sets_bounded_host_only_secure_cookie_and_public_response(vacancy):
    client, token = csrf_client()

    response = create_draft(client, vacancy, token)

    assert response.status_code == 201
    assert response["ETag"] == '"draft-1"'
    assert response["Cache-Control"] == "no-store"
    cookie = response.cookies["applyflow_draft"]
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/api/v1/application-drafts/"
    assert not cookie["domain"]
    assert 0 < int(cookie["max-age"]) <= 7 * 24 * 60 * 60

    payload = response.json()
    assert set(payload) == {"draft"}
    assert payload["draft"]["vacancy"] == {
        "slug": vacancy.slug,
        "title": vacancy.title,
    }
    serialized = response.content.decode()
    raw_credential = cookie.value
    secret = raw_credential.rsplit(".", 1)[1]
    assert raw_credential not in serialized
    assert secret not in serialized
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    assert raw_credential not in draft.secret_hash
    assert secret not in draft.secret_hash


@pytest.mark.django_db
@override_settings(DRAFT_COOKIE_SECURE=False)
def test_explicit_local_http_mode_can_set_insecure_ownership_cookie(vacancy):
    client, token = csrf_client()

    response = create_draft(client, vacancy, token)

    assert response.status_code == 201
    assert response.cookies["applyflow_draft"]["secure"] == ""


@pytest.mark.django_db
def test_active_get_has_no_create_side_effect_and_valid_read_does_not_renew(vacancy):
    client, token = csrf_client()
    empty_response = client.get("/api/v1/application-drafts/active/")
    assert empty_response.status_code == 204
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 0

    create_response = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    original_activity = draft.last_activity_at
    original_expiry = draft.expires_at

    response = client.get("/api/v1/application-drafts/active/")

    assert response.status_code == 200
    assert response["ETag"] == create_response["ETag"]
    assert "applyflow_draft" not in response.cookies
    draft.refresh_from_db()
    assert draft.last_activity_at == original_activity
    assert draft.expires_at == original_expiry


@pytest.mark.django_db
def test_same_vacancy_is_idempotent_and_other_vacancy_conflicts(vacancy, another_vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)

    resumed = create_draft(client, vacancy, token)
    conflict = create_draft(client, another_vacancy, token)

    assert created.status_code == 201
    assert resumed.status_code == 200
    assert resumed["ETag"] == created["ETag"]
    assert "applyflow_draft" not in resumed.cookies
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 1
    assert_error(conflict, 409, "active_draft_conflict")
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 1


@pytest.mark.django_db
def test_lost_create_response_replays_same_draft_and_ownership(vacancy):
    client, token = csrf_client()
    csrf_cookie = client.cookies["csrftoken"].value
    creation_key = client.cookies["applyflow_draft_creation"].value

    created = create_draft(client, vacancy, token)
    created_credential = created.cookies["applyflow_draft"].value
    created_id = created.json()["draft"]["id"]
    replay_client = Client(enforce_csrf_checks=True)
    replay_client.cookies["csrftoken"] = csrf_cookie
    replay_client.cookies["applyflow_draft_creation"] = creation_key

    replayed = create_draft(replay_client, vacancy, token)

    assert created.status_code == 201
    assert replayed.status_code == 200
    assert replayed.json()["draft"]["id"] == created_id
    assert replayed.cookies["applyflow_draft"].value == created_credential
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    assert draft.creation_key_digest != creation_key
    assert len(draft.creation_key_digest) == 64
    assert creation_key not in draft.secret_hash


@pytest.mark.django_db
def test_same_creation_key_cannot_reassign_draft_to_another_vacancy(vacancy, another_vacancy):
    client, token = csrf_client()
    csrf_cookie = client.cookies["csrftoken"].value
    creation_key = client.cookies["applyflow_draft_creation"].value
    created = create_draft(client, vacancy, token)
    replay_client = Client(enforce_csrf_checks=True)
    replay_client.cookies["csrftoken"] = csrf_cookie
    replay_client.cookies["applyflow_draft_creation"] = creation_key

    conflict = create_draft(replay_client, another_vacancy, token)

    assert_error(conflict, 409, "active_draft_conflict")
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    assert draft.vacancy_id == vacancy.pk
    assert conflict.cookies["applyflow_draft"].value == created.cookies["applyflow_draft"].value


@pytest.mark.django_db
def test_different_creation_keys_are_not_globally_blocked(vacancy):
    first, first_token = csrf_client()
    second, second_token = csrf_client()

    first_response = create_draft(first, vacancy, first_token)
    second_response = create_draft(second, vacancy, second_token)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_simultaneous_initial_requests_share_durable_creation_boundary(vacancy):
    bootstrap, token = csrf_client()
    csrf_cookie = bootstrap.cookies["csrftoken"].value
    creation_key = bootstrap.cookies["applyflow_draft_creation"].value
    barrier = Barrier(2)

    def send_request():
        close_old_connections()
        client = Client(enforce_csrf_checks=True)
        client.cookies["csrftoken"] = csrf_cookie
        client.cookies["applyflow_draft_creation"] = creation_key
        barrier.wait(timeout=5)
        response = create_draft(client, vacancy, token)
        result = (
            response.status_code,
            response.json()["draft"]["id"],
            response.cookies["applyflow_draft"].value,
        )
        close_old_connections()
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: send_request(), range(2)))

    assert sorted(status for status, _, _ in results) == [200, 201]
    assert len({draft_id for _, draft_id, _ in results}) == 1
    assert len({credential for _, _, credential in results}) == 1
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 1


@pytest.mark.django_db
def test_creation_digest_has_database_uniqueness_and_never_stores_raw_key(vacancy):
    Draft = apps.get_model("applications.ApplicationDraft")
    first = Draft.objects.create(
        vacancy=vacancy,
        secret_hash="first-fictional-hash",
        creation_key_digest="a" * 64,
        expires_at=timezone.now() + timedelta(days=7),
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Draft.objects.create(
            vacancy=vacancy,
            secret_hash="second-fictional-hash",
            creation_key_digest=first.creation_key_digest,
            expires_at=timezone.now() + timedelta(days=7),
        )


@pytest.mark.django_db
@override_settings(DRAFT_COOKIE_SECURE=True)
def test_invalid_cookie_is_generic_cleared_and_never_creates(vacancy):
    client, token = csrf_client()
    client.cookies["applyflow_draft"] = "v1.not-a-uuid.invalid"

    active = client.get("/api/v1/application-drafts/active/")
    client.cookies["applyflow_draft"] = "v1.not-a-uuid.invalid"
    create = create_draft(client, vacancy, token)

    for response in (active, create):
        assert_error(response, 404, "draft_unavailable")
        cleared = response.cookies["applyflow_draft"]
        assert int(cleared["max-age"]) == 0
        assert cleared["path"] == "/api/v1/application-drafts/"
        assert cleared["secure"] is True
        assert cleared["httponly"] is True
        assert cleared["samesite"] == "Lax"
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 0


@pytest.mark.django_db
def test_invalid_cookie_is_resolved_before_unavailable_vacancy_lookup():
    client, token = csrf_client()
    client.cookies["applyflow_draft"] = "v1.not-a-uuid.invalid"

    response = client.post(
        "/api/v1/application-drafts/",
        {"vacancy_slug": "missing-vacancy"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert_error(response, 404, "draft_unavailable")
    assert int(response.cookies["applyflow_draft"]["max-age"]) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("valid_first", [True, False])
def test_duplicate_cookie_order_cannot_override_one_valid_credential(vacancy, valid_first):
    owner, token = csrf_client()
    created = create_draft(owner, vacancy, token)
    valid = created.cookies["applyflow_draft"].value
    invalid = f"v1.{uuid.uuid4()}.{'x' * 43}"
    values = (valid, invalid) if valid_first else (invalid, valid)
    raw_cookie = "; ".join(f"applyflow_draft={value}" for value in values)

    response = Client().get(
        "/api/v1/application-drafts/active/",
        HTTP_COOKIE=raw_cookie,
    )

    assert response.status_code == 200
    assert response.json()["draft"]["id"] == str(
        apps.get_model("applications.ApplicationDraft").objects.get().pk
    )


@pytest.mark.django_db
def test_two_valid_duplicate_credentials_are_ambiguous_and_clear_all_api_paths(
    vacancy, another_vacancy
):
    first = apps.get_model("applications.ApplicationDraft")(
        vacancy=vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    first_credential = generate_credential(first)
    first.save()
    second = apps.get_model("applications.ApplicationDraft")(
        vacancy=another_vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    second_credential = generate_credential(second)
    second.save()
    raw_cookie = f"applyflow_draft={first_credential}; applyflow_draft={second_credential}"

    response = Client().get(
        "/api/v1/application-drafts/active/",
        HTTP_COOKIE=raw_cookie,
    )

    assert_error(response, 404, "draft_unavailable")
    serialized = response.content.decode()
    assert first_credential not in serialized
    assert second_credential not in serialized
    cleared_paths = {
        morsel["path"]
        for morsel in response.cookies.values()
        if morsel.key == "applyflow_draft" and int(morsel["max-age"]) == 0
    }
    assert cleared_paths == {
        "/",
        "/api/",
        "/api/v1/",
        "/api/v1/application-drafts/",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "raw_suffix",
    [
        "; malformed-cookie-segment",
        "; applyflow_draft=x; applyflow_draft=x; applyflow_draft=x; applyflow_draft=x",
    ],
)
def test_malformed_or_excessive_raw_ownership_cookies_fail_generically(vacancy, raw_suffix):
    owner, token = csrf_client()
    created = create_draft(owner, vacancy, token)
    credential = created.cookies["applyflow_draft"].value

    response = Client().get(
        "/api/v1/application-drafts/active/",
        HTTP_COOKIE=f"applyflow_draft={credential}{raw_suffix}",
    )

    assert_error(response, 404, "draft_unavailable")
    assert credential not in response.content.decode()


@pytest.mark.django_db
def test_ambiguous_ownership_recovery_can_bootstrap_and_create_again(vacancy, another_vacancy):
    first = apps.get_model("applications.ApplicationDraft")(
        vacancy=vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    first_credential = generate_credential(first)
    first.save()
    second = apps.get_model("applications.ApplicationDraft")(
        vacancy=another_vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    second_credential = generate_credential(second)
    second.save()

    ambiguous = Client().get(
        "/api/v1/application-drafts/active/",
        HTTP_COOKIE=(f"applyflow_draft={first_credential}; applyflow_draft={second_credential}"),
    )
    recovered_client, token = csrf_client()
    recovered = create_draft(recovered_client, vacancy, token)

    assert_error(ambiguous, 404, "draft_unavailable")
    assert recovered.status_code == 201
    assert apps.get_model("applications.ApplicationDraft").objects.count() == 3


@pytest.mark.django_db
@pytest.mark.parametrize("unavailable", ["wrong", "revoked", "abandoned", "expired", "submitted"])
def test_unavailable_credentials_share_one_generic_response(vacancy, unavailable):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    if unavailable == "wrong":
        value = client.cookies["applyflow_draft"].value
        client.cookies["applyflow_draft"] = f"{value.rsplit('.', 1)[0]}.{'x' * 43}"
    elif unavailable == "revoked":
        draft.credential_revoked_at = timezone.now()
        draft.save(update_fields=["credential_revoked_at"])
    elif unavailable == "abandoned":
        draft.status = draft.Status.ABANDONED
        draft.save(update_fields=["status"])
    elif unavailable == "submitted":
        draft.status = draft.Status.SUBMITTED
        draft.submitted_at = timezone.now()
        draft.save(update_fields=["status", "submitted_at"])
    else:
        draft.expires_at = timezone.now() - timedelta(seconds=1)
        draft.save(update_fields=["expires_at"])

    response = client.get("/api/v1/application-drafts/active/")

    assert created.status_code == 201
    assert_error(response, 404, "draft_unavailable")
    assert str(draft.pk) not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("if_match", "status", "code"),
    [
        (None, 428, "draft_version_required"),
        ("draft-1", 428, "draft_version_required"),
        ('"draft-2"', 409, "draft_conflict"),
    ],
)
def test_abandonment_requires_current_well_formed_version(vacancy, if_match, status, code):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    kwargs = {"HTTP_X_CSRFTOKEN": token}
    if if_match is not None:
        kwargs["HTTP_IF_MATCH"] = if_match

    response = client.delete(f"/api/v1/application-drafts/{draft.pk}/", **kwargs)

    assert_error(response, status, code)
    draft.refresh_from_db()
    assert draft.status == draft.Status.ACTIVE
    assert draft.version == 1


@pytest.mark.django_db
def test_successful_abandonment_revokes_increments_clears_and_repeat_is_generic(vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = client.delete(
        f"/api/v1/application-drafts/{draft.pk}/",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert response.status_code == 204
    assert int(response.cookies["applyflow_draft"]["max-age"]) == 0
    assert response.cookies["applyflow_draft"]["path"] == "/api/v1/application-drafts/"
    draft.refresh_from_db()
    assert draft.status == draft.Status.ABANDONED
    assert draft.credential_revoked_at is not None
    assert draft.version == 2

    repeat = client.delete(
        f"/api/v1/application-drafts/{draft.pk}/",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-2"',
    )
    assert_error(repeat, 404, "draft_unavailable")


@pytest.mark.django_db
def test_cross_draft_credential_cannot_abandon_target(vacancy, another_vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    first = apps.get_model("applications.ApplicationDraft").objects.get()
    second = apps.get_model("applications.ApplicationDraft")(
        vacancy=another_vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    second_credential = generate_credential(second)
    second.save()
    client.cookies["applyflow_draft"] = second_credential

    response = client.delete(
        f"/api/v1/application-drafts/{first.pk}/",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_error(response, 404, "draft_unavailable")
    first.refresh_from_db()
    assert first.status == first.Status.ACTIVE


@pytest.mark.django_db
def test_abandonment_without_csrf_is_rejected_before_mutation(vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = client.delete(f"/api/v1/application-drafts/{draft.pk}/", HTTP_IF_MATCH='"draft-1"')

    assert_error(response, 403, "csrf_failed")
    draft.refresh_from_db()
    assert draft.status == draft.Status.ACTIVE


@pytest.mark.django_db
def test_candidate_patch_partially_updates_and_returns_complete_aggregate(vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft_id = created.json()["draft"]["id"]

    response = patch_draft(
        client,
        draft_id,
        "candidate",
        {"full_name": "  Zoë Example  "},
        token,
    )

    assert response.status_code == 200
    assert response["ETag"] == '"draft-2"'
    assert response["Cache-Control"] == "no-store"
    assert response.json()["draft"]["candidate"] == {
        "full_name": "Zoë Example",
        "email": "",
        "phone": "",
        "portfolio_url": "",
        "preferred_contact_method": "",
    }


@pytest.mark.django_db
def test_experience_patch_normalizes_skills_and_preserves_first_seen_order(vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft_id = created.json()["draft"]["id"]

    response = patch_draft(
        client,
        draft_id,
        "experience",
        {"skills": ["  Vue 3 ", "TypeScript", "vue 3", "Доступность"]},
        token,
    )

    assert response.status_code == 200
    assert response["ETag"] == '"draft-2"'
    assert response.json()["draft"]["experience"]["skills"] == [
        "Vue 3",
        "TypeScript",
        "Доступность",
    ]


@pytest.mark.django_db
def test_candidate_patch_updates_email_normalization_and_omits_private_field(vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft_id = created.json()["draft"]["id"]

    response = patch_draft(
        client,
        draft_id,
        "candidate",
        {
            "email": "  FICTIONAL.CANDIDATE@EXAMPLE.TEST  ",
            "phone": "+998 (90) 123-45-67",
            "preferred_contact_method": "phone",
            "portfolio_url": "http://portfolio.example.test/profile",
        },
        token,
    )

    assert response.status_code == 200
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    assert draft.email == "FICTIONAL.CANDIDATE@EXAMPLE.TEST"
    assert draft.email_normalized == "fictional.candidate@example.test"
    assert "email_normalized" not in response.content.decode()
    assert response.json()["draft"]["candidate"]["full_name"] == ""


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
@pytest.mark.parametrize(
    ("payload", "field"),
    [({}, "non_field_errors"), ({"unexpected": "value"}, "unexpected"), ([], "non_field_errors")],
)
def test_patch_requires_nonempty_json_object_with_known_fields(vacancy, section, payload, field):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = client.patch(
        f"/api/v1/application-drafts/{draft.pk}/{section}/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_validation_error(response, field)
    draft.refresh_from_db()
    assert draft.version == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"full_name": None}, "full_name"),
        ({"full_name": "x" * 201}, "full_name"),
        ({"full_name": "Fictional\x00 Name"}, "full_name"),
        ({"email": "not-an-email"}, "email"),
        ({"email": None}, "email"),
        ({"phone": "letters-only"}, "phone"),
        ({"portfolio_url": "ftp://example.test/profile"}, "portfolio_url"),
        ({"portfolio_url": "not a url"}, "portfolio_url"),
        ({"portfolio_url": "https://example.test/\nheader"}, "portfolio_url"),
        ({"preferred_contact_method": "postal"}, "preferred_contact_method"),
        ({"preferred_contact_method": "phone"}, "phone"),
    ],
)
def test_candidate_patch_rejects_invalid_fields_without_writing(vacancy, payload, field):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    original = (draft.full_name, draft.email, draft.phone, draft.version, draft.last_activity_at)

    response = patch_draft(client, draft.pk, "candidate", payload, token)

    assert_validation_error(response, field)
    assert "applyflow_draft" not in response.cookies
    draft.refresh_from_db()
    assert (
        draft.full_name,
        draft.email,
        draft.phone,
        draft.version,
        draft.last_activity_at,
    ) == original


@pytest.mark.django_db
def test_candidate_phone_preference_uses_merged_state_atomically(vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    accepted = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"phone": "+44 20 7946 0958", "preferred_contact_method": "phone"},
        token,
    )
    rejected = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"phone": ""},
        token,
        version=2,
    )

    assert accepted.status_code == 200
    assert_validation_error(rejected, "phone")
    draft.refresh_from_db()
    assert draft.phone == "+44 20 7946 0958"
    assert draft.preferred_contact_method == "phone"
    assert draft.version == 2


@pytest.mark.django_db
def test_candidate_patch_accepts_documented_boundaries(vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    long_url = "https://example.test/" + ("a" * (500 - len("https://example.test/")))

    response = patch_draft(
        client,
        draft.pk,
        "candidate",
        {
            "full_name": "名" * 200,
            "phone": "+" + ("1" * 29),
            "portfolio_url": long_url,
        },
        token,
    )

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["", "early_career", "mid_level", "senior"])
def test_experience_patch_accepts_approved_levels_and_clearing(vacancy, value):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = patch_draft(client, draft.pk, "experience", {"experience_level": value}, token)

    assert response.status_code == 200
    assert response.json()["draft"]["experience"]["experience_level"] == value


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"experience_level": "expert"}, "experience_level"),
        ({"skills": "Python"}, "skills"),
        ({"skills": ["valid", 7]}, "skills"),
        ({"skills": ["  "]}, "skills"),
        ({"skills": ["x" * 81]}, "skills"),
        ({"skills": ["safe\x00value"]}, "skills"),
        ({"skills": [str(index) for index in range(13)]}, "skills"),
        ({"optional_message": "x" * 1201}, "optional_message"),
        ({"optional_message": "unsafe\x00message"}, "optional_message"),
        ({"consent_version": "x" * 65}, "consent_version"),
        ({"consent_version": "unsafe\nversion"}, "consent_version"),
    ],
)
def test_experience_patch_rejects_invalid_fields_without_writing(vacancy, payload, field):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    original = (draft.skills, draft.optional_message, draft.version, draft.last_activity_at)

    response = patch_draft(client, draft.pk, "experience", payload, token)

    assert_validation_error(response, field)
    assert "applyflow_draft" not in response.cookies
    draft.refresh_from_db()
    assert (draft.skills, draft.optional_message, draft.version, draft.last_activity_at) == original


@pytest.mark.django_db
@pytest.mark.parametrize("value", [1, 0, "true", "false", None])
def test_consent_acknowledgement_requires_real_json_boolean(vacancy, value):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    response = patch_draft(
        client,
        draft.pk,
        "experience",
        {"consent_acknowledged": value},
        token,
    )

    assert_validation_error(response, "consent_acknowledged")


@pytest.mark.django_db
def test_experience_patch_supports_clearing_and_text_boundaries(vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()

    first = patch_draft(
        client,
        draft.pk,
        "experience",
        {
            "skills": ["x" * 80, "アクセシビリティ"],
            "optional_message": "Line one\nLine two" + ("x" * (1200 - 17)),
            "consent_acknowledged": True,
            "consent_version": "privacy-v1",
        },
        token,
    )
    cleared = patch_draft(
        client,
        draft.pk,
        "experience",
        {"skills": [], "optional_message": "", "experience_level": ""},
        token,
        version=2,
    )

    assert first.status_code == 200
    assert cleared.status_code == 200
    assert cleared.json()["draft"]["experience"]["skills"] == []
    assert cleared.json()["draft"]["experience"]["optional_message"] == ""


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
def test_patch_requires_csrf_and_rejects_unsupported_methods(vacancy, section):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    path = f"/api/v1/application-drafts/{draft.pk}/{section}/"

    csrf_failure = client.patch(
        path,
        {"full_name": "Fictional"} if section == "candidate" else {"skills": []},
        content_type="application/json",
        HTTP_IF_MATCH='"draft-1"',
    )
    assert_error(csrf_failure, 403, "csrf_failed")
    for method in ("get", "post", "put", "delete"):
        response = getattr(client, method)(path, HTTP_X_CSRFTOKEN=token)
        assert response.status_code == 405
        assert response["Cache-Control"] == "no-store"
        payload = response.json()["error"]
        assert response["X-Request-ID"] == payload["request_id"]


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
def test_patch_requires_current_ownership_and_version(vacancy, section):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    payload = {"full_name": "Fictional"} if section == "candidate" else {"skills": []}
    path = f"/api/v1/application-drafts/{draft.pk}/{section}/"

    missing_version = client.patch(
        path,
        payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    malformed_version = client.patch(
        path,
        payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH="draft-1",
    )
    stale_version = patch_draft(client, draft.pk, section, payload, token, version=2)
    client.cookies.pop("applyflow_draft")
    missing_ownership = patch_draft(client, draft.pk, section, payload, token)

    assert_error(missing_version, 428, "draft_version_required")
    assert_error(malformed_version, 428, "draft_version_required")
    assert_error(stale_version, 409, "draft_conflict")
    assert_error(missing_ownership, 404, "draft_unavailable")
    draft.refresh_from_db()
    assert draft.version == 1


@pytest.mark.django_db
def test_cross_draft_patch_is_generic_and_changes_neither_draft(vacancy, another_vacancy):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    first = apps.get_model("applications.ApplicationDraft").objects.get()
    second = apps.get_model("applications.ApplicationDraft")(
        vacancy=another_vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    second_credential = generate_credential(second)
    second.save()
    client.cookies["applyflow_draft"] = second_credential

    response = patch_draft(
        client,
        first.pk,
        "candidate",
        {"full_name": "Must Not Persist"},
        token,
    )

    assert_error(response, 404, "draft_unavailable")
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.full_name == second.full_name == ""
    assert first.version == second.version == 1


@pytest.mark.django_db
@override_settings(DRAFT_COOKIE_SECURE=True)
def test_successful_patch_renews_lifecycle_and_same_verified_cookie_only(vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    credential = created.cookies["applyflow_draft"].value
    original_activity = draft.last_activity_at

    response = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"full_name": "Avery Example"},
        token,
    )

    draft.refresh_from_db()
    cookie = response.cookies["applyflow_draft"]
    assert response.status_code == 200
    assert cookie.value == credential
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/api/v1/application-drafts/"
    assert not cookie["domain"]
    assert draft.version == 2
    assert draft.last_activity_at > original_activity
    assert draft.expires_at == draft.effective_expiry_at()


@pytest.mark.django_db
def test_duplicate_cookie_patch_renews_only_uniquely_verified_credential(vacancy):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    credential = created.cookies["applyflow_draft"].value
    csrf_cookie = client.cookies["csrftoken"].value

    response = client.patch(
        f"/api/v1/application-drafts/{draft.pk}/experience/",
        {"skills": ["Python"]},
        content_type="application/json",
        HTTP_COOKIE=(
            f"csrftoken={csrf_cookie}; applyflow_draft=invalid; applyflow_draft={credential}"
        ),
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert response.status_code == 200
    assert response.cookies["applyflow_draft"].value == credential


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
def test_patch_accepts_json_only(vacancy, section):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    payload = {"full_name": "Fictional Candidate"} if section == "candidate" else {"skills": []}

    response = client.patch(
        f"/api/v1/application-drafts/{draft.pk}/{section}/",
        payload,
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert response.status_code == 415
    assert response["Cache-Control"] == "no-store"
    assert response["X-Request-ID"] == response.json()["error"]["request_id"]
    draft.refresh_from_db()
    assert draft.full_name == ""
    assert draft.skills == []
    assert draft.version == 1


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
@pytest.mark.parametrize(
    "unavailable",
    ["malformed", "wrong", "revoked", "expired", "abandoned", "submitted"],
)
def test_patch_unavailable_credentials_are_generic_and_do_not_write(vacancy, section, unavailable):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    payload = (
        {"full_name": "Must Not Persist"}
        if section == "candidate"
        else {"skills": ["PrivateSkill"]}
    )
    if unavailable == "malformed":
        client.cookies["applyflow_draft"] = "malformed"
    elif unavailable == "wrong":
        client.cookies["applyflow_draft"] = f"v1.{draft.pk}.{'a' * 43}"
    elif unavailable == "revoked":
        draft.credential_revoked_at = timezone.now()
        draft.save(update_fields=["credential_revoked_at"])
    elif unavailable == "expired":
        draft.expires_at = timezone.now() - timedelta(seconds=1)
        draft.save(update_fields=["expires_at"])
    elif unavailable == "abandoned":
        draft.status = draft.Status.ABANDONED
        draft.save(update_fields=["status"])
    else:
        draft.status = draft.Status.SUBMITTED
        draft.submitted_at = timezone.now()
        draft.save(update_fields=["status", "submitted_at"])

    response = patch_draft(
        client,
        draft.pk,
        section,
        payload,
        token,
    )

    assert_error(response, 404, "draft_unavailable")
    assert int(response.cookies["applyflow_draft"]["max-age"]) == 0
    draft.refresh_from_db()
    assert draft.full_name == ""
    assert draft.skills == []
    assert draft.version == 1


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
def test_two_valid_patch_credentials_are_ambiguous_and_authorize_neither(
    vacancy, another_vacancy, section
):
    client, token = csrf_client()
    first_response = create_draft(client, vacancy, token)
    first = apps.get_model("applications.ApplicationDraft").objects.get()
    first_credential = first_response.cookies["applyflow_draft"].value
    second = apps.get_model("applications.ApplicationDraft")(
        vacancy=another_vacancy,
        expires_at=timezone.now() + timedelta(days=7),
    )
    second_credential = generate_credential(second)
    second.save()
    csrf_cookie = client.cookies["csrftoken"].value

    response = client.patch(
        f"/api/v1/application-drafts/{first.pk}/{section}/",
        {"full_name": "Must Not Persist"}
        if section == "candidate"
        else {"skills": ["PrivateSkill"]},
        content_type="application/json",
        HTTP_COOKIE=(
            f"csrftoken={csrf_cookie}; applyflow_draft={first_credential}; "
            f"applyflow_draft={second_credential}"
        ),
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_error(response, 404, "draft_unavailable")
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.full_name == second.full_name == ""
    assert first.skills == second.skills == []
    assert first.version == second.version == 1


@pytest.mark.django_db
@pytest.mark.parametrize("section", ["candidate", "experience"])
def test_excessive_patch_ownership_cookies_fail_generically(vacancy, section):
    client, token = csrf_client()
    created = create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    credential = created.cookies["applyflow_draft"].value
    csrf_cookie = client.cookies["csrftoken"].value
    raw_cookie = (
        f"csrftoken={csrf_cookie}; applyflow_draft={credential}; "
        "applyflow_draft=x; applyflow_draft=x; applyflow_draft=x; applyflow_draft=x"
    )

    response = client.patch(
        f"/api/v1/application-drafts/{draft.pk}/{section}/",
        {"full_name": "Must Not Persist"}
        if section == "candidate"
        else {"skills": ["PrivateSkill"]},
        content_type="application/json",
        HTTP_COOKIE=raw_cookie,
        HTTP_X_CSRFTOKEN=token,
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_error(response, 404, "draft_unavailable")
    assert credential not in response.content.decode()
    draft.refresh_from_db()
    assert draft.full_name == ""
    assert draft.skills == []
    assert draft.version == 1


@pytest.mark.django_db
def test_successful_patch_logs_exclude_candidate_and_experience_values(vacancy, caplog):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    candidate_value = "Private Fictional Candidate"
    experience_value = "PrivateSkillValue"

    candidate_response = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"full_name": candidate_value},
        token,
    )
    experience_response = patch_draft(
        client,
        draft.pk,
        "experience",
        {"skills": [experience_value], "optional_message": "Private message value"},
        token,
        version=2,
    )

    assert candidate_response.status_code == 200
    assert experience_response.status_code == 200
    assert candidate_value not in caplog.text
    assert experience_value not in caplog.text
    assert "Private message value" not in caplog.text


@pytest.mark.django_db
def test_patch_failure_responses_and_logs_exclude_candidate_values(vacancy, caplog):
    client, token = csrf_client()
    create_draft(client, vacancy, token)
    draft = apps.get_model("applications.ApplicationDraft").objects.get()
    private_value = "private-fictional-value@@example.test"

    validation_error = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"email": private_value},
        token,
    )
    stale_conflict = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"full_name": "Private Stale Name"},
        token,
        version=2,
    )
    client.cookies.pop("applyflow_draft")
    authorization_failure = patch_draft(
        client,
        draft.pk,
        "candidate",
        {"full_name": "Private Authorization Name"},
        token,
    )
    csrf_failure = client.patch(
        f"/api/v1/application-drafts/{draft.pk}/candidate/",
        {"full_name": "Private CSRF Name"},
        content_type="application/json",
        HTTP_IF_MATCH='"draft-1"',
    )

    assert_validation_error(validation_error, "email")
    assert_error(stale_conflict, 409, "draft_conflict")
    assert_error(authorization_failure, 404, "draft_unavailable")
    assert_error(csrf_failure, 403, "csrf_failed")
    for value in (
        private_value,
        "Private Stale Name",
        "Private Authorization Name",
        "Private CSRF Name",
    ):
        assert value not in validation_error.content.decode()
        assert value not in stale_conflict.content.decode()
        assert value not in authorization_failure.content.decode()
        assert value not in csrf_failure.content.decode()
        assert value not in caplog.text
