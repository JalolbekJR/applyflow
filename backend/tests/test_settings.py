import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.settings import (
    APPROVED_DRAFT_COOKIE_PATH,
    database_config,
    draft_cookie_secure,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROBE_ENV_NAMES = (
    "DRAFT_COOKIE_NAME",
    "DRAFT_COOKIE_PATH",
    "DRAFT_COOKIE_SECURE",
    "DRAFT_INACTIVITY_SECONDS",
    "DRAFT_ABSOLUTE_SECONDS",
    "DRAFT_CREATION_COOKIE_NAME",
    "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
)
PROBE_CODE = """
import json
from config import settings as s

print(
    json.dumps(
        {
            "draft_cookie_name": s.DRAFT_COOKIE_NAME,
            "draft_cookie_path": s.DRAFT_COOKIE_PATH,
            "draft_cookie_secure": s.DRAFT_COOKIE_SECURE,
            "draft_inactivity_seconds": int(s.DRAFT_INACTIVITY_LIFETIME.total_seconds()),
            "draft_absolute_seconds": int(s.DRAFT_ABSOLUTE_LIFETIME.total_seconds()),
            "draft_creation_cookie_name": s.DRAFT_CREATION_COOKIE_NAME,
            "draft_creation_key_lifetime_seconds": int(
                s.DRAFT_CREATION_KEY_LIFETIME.total_seconds()
            ),
        }
    )
)
""".strip()
LEXICAL_INVALID_VALUES = [
    "60_0",
    "+60",
    " 60",
    "60 ",
    "  +60  ",
    "6 0",
    "60.0",
    "6e1",
    "0x3c",
    "0b111100",
    "0o74",
    "1,000",
    "١٢٣",
    "１２３",
    "",
]
OVERSIZED_DIGIT_STRING = "9" * 10000
INACTIVITY_MESSAGE = (
    "DRAFT_INACTIVITY_SECONDS must be an ASCII decimal integer between 60 and 604800 seconds."
)
ABSOLUTE_MESSAGE = (
    "DRAFT_ABSOLUTE_SECONDS must be an ASCII decimal integer between 60 and 2592000 seconds."
)
CREATION_KEY_MESSAGE = (
    "DRAFT_CREATION_KEY_LIFETIME_SECONDS must be an ASCII decimal integer "
    "between 30 and 900 seconds."
)


def test_postgresql_database_url_is_parsed_without_exposing_it():
    config = database_config("postgresql://applyflow:fictional%21@db.example.test:5433/applyflow")
    assert config == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "applyflow",
        "USER": "applyflow",
        "PASSWORD": "fictional!",
        "HOST": "db.example.test",
        "PORT": 5433,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }


def test_incomplete_or_non_postgresql_database_url_is_rejected():
    with pytest.raises(ImproperlyConfigured):
        database_config("mysql://localhost/applyflow")
    with pytest.raises(ImproperlyConfigured):
        database_config("postgresql://localhost")


def test_drf_defaults_to_staff_only_for_future_endpoints():
    assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAdminUser"
    ]


def test_draft_settings_use_approved_defaults_and_only_allow_local_insecure_cookie():
    assert settings.DRAFT_COOKIE_NAME == "applyflow_draft"
    assert settings.DRAFT_COOKIE_PATH == APPROVED_DRAFT_COOKIE_PATH
    assert settings.DRAFT_INACTIVITY_LIFETIME == timedelta(days=7)
    assert settings.DRAFT_ABSOLUTE_LIFETIME == timedelta(days=30)
    assert settings.DRAFT_CREATION_COOKIE_NAME == "applyflow_draft_creation"
    assert settings.DRAFT_CREATION_KEY_LIFETIME == timedelta(minutes=10)
    assert draft_cookie_secure("development", configured=False) is False
    assert draft_cookie_secure("development", configured=True) is True
    assert draft_cookie_secure("staging", configured=False) is True
    assert draft_cookie_secure("production", configured=False) is True


def run_settings_probe(**overrides):
    environment = os.environ.copy()
    for name in PROBE_ENV_NAMES:
        environment.pop(name, None)
    environment.update(
        {
            "APP_ENV": "development",
            "DJANGO_SECRET_KEY": "fictional-settings-probe-secret",
            **overrides,
        }
    )
    return subprocess.run(
        [sys.executable, "-c", PROBE_CODE],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_settings_load_failed(result, expected_message: str):
    assert result.returncode != 0
    assert "django.core.exceptions.ImproperlyConfigured" in result.stderr
    assert expected_message in result.stderr


def parse_probe_output(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def assert_raw_input_not_echoed(stderr: str, name: str, value: str):
    if value:
        assert f"'{value}'" not in stderr
        assert f'"{value}"' not in stderr
    assert f"{name}=" not in stderr


def assert_invalid_duration_setting(name: str, value: str, expected_message: str, **overrides):
    result = run_settings_probe(**{name: value, **overrides})

    assert_settings_load_failed(result, expected_message)
    assert_raw_input_not_echoed(result.stderr, name, value)
    assert "ValueError" not in result.stderr
    assert "TypeError" not in result.stderr
    assert "OverflowError" not in result.stderr
    assert "Exceeds the limit" not in result.stderr


def test_draft_environment_values_are_loaded_under_canonical_names():
    result = run_settings_probe(
        DRAFT_COOKIE_NAME="fictional_draft_cookie",
        DRAFT_COOKIE_PATH=APPROVED_DRAFT_COOKIE_PATH,
        DRAFT_COOKIE_SECURE="true",
        DRAFT_INACTIVITY_SECONDS="101",
        DRAFT_ABSOLUTE_SECONDS="202",
        DRAFT_CREATION_COOKIE_NAME="fictional_creation_cookie",
        DRAFT_CREATION_KEY_LIFETIME_SECONDS="303",
    )

    payload = parse_probe_output(result)
    assert payload == {
        "draft_cookie_name": "fictional_draft_cookie",
        "draft_cookie_path": APPROVED_DRAFT_COOKIE_PATH,
        "draft_cookie_secure": True,
        "draft_inactivity_seconds": 101,
        "draft_absolute_seconds": 202,
        "draft_creation_cookie_name": "fictional_creation_cookie",
        "draft_creation_key_lifetime_seconds": 303,
    }


def test_canonical_draft_cookie_path_is_accepted_during_settings_load():
    result = run_settings_probe(DRAFT_COOKIE_PATH=APPROVED_DRAFT_COOKIE_PATH)

    payload = parse_probe_output(result)
    assert payload["draft_cookie_path"] == APPROVED_DRAFT_COOKIE_PATH


@pytest.mark.parametrize(
    "value",
    [
        "/",
        "not-a-cookie-path",
        "/api/",
        "/api/v1/",
        "/api/v1/application-drafts",
        "/api/v1/application-drafts/?x=1",
        "/api/v1/application-drafts/#fragment",
        "/api/v1/application-drafts/;bad",
        "\\api\\v1\\application-drafts\\",
        "https://example.test/api/v1/application-drafts/",
        "/api/v1/application-drafts/\tchild",
        "/api/v1/application-drafts/\x07",
    ],
)
def test_invalid_draft_cookie_paths_fail_during_settings_load(value):
    result = run_settings_probe(DRAFT_COOKIE_PATH=value)

    assert_settings_load_failed(
        result,
        "DRAFT_COOKIE_PATH must match the approved application drafts path.",
    )


@pytest.mark.parametrize(
    ("value", "expected_seconds"),
    [
        ("60", 60),
        ("604800", 604800),
    ],
)
def test_inactivity_duration_accepts_approved_bounds(value, expected_seconds):
    result = run_settings_probe(DRAFT_INACTIVITY_SECONDS=value)

    payload = parse_probe_output(result)
    assert payload["draft_inactivity_seconds"] == expected_seconds


def test_inactivity_duration_uses_the_approved_default():
    result = run_settings_probe()

    payload = parse_probe_output(result)
    assert payload["draft_inactivity_seconds"] == 604800


@pytest.mark.parametrize("value", LEXICAL_INVALID_VALUES + [OVERSIZED_DIGIT_STRING])
def test_invalid_inactivity_duration_lexical_forms_fail_during_settings_load(value):
    assert_invalid_duration_setting(
        "DRAFT_INACTIVITY_SECONDS",
        value,
        INACTIVITY_MESSAGE,
    )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "not-an-integer",
        "604801",
        str(10 * 365 * 24 * 60 * 60),
    ],
)
def test_invalid_inactivity_durations_fail_during_settings_load(value):
    assert_invalid_duration_setting(
        "DRAFT_INACTIVITY_SECONDS",
        value,
        INACTIVITY_MESSAGE,
    )


@pytest.mark.parametrize(
    ("value", "expected_seconds", "overrides"),
    [
        ("60", 60, {"DRAFT_INACTIVITY_SECONDS": "60"}),
        ("2592000", 2592000, {}),
    ],
)
def test_absolute_duration_accepts_approved_bounds(value, expected_seconds, overrides):
    result = run_settings_probe(DRAFT_ABSOLUTE_SECONDS=value, **overrides)

    payload = parse_probe_output(result)
    assert payload["draft_absolute_seconds"] == expected_seconds


def test_absolute_duration_uses_the_approved_default():
    result = run_settings_probe()

    payload = parse_probe_output(result)
    assert payload["draft_absolute_seconds"] == 2592000


@pytest.mark.parametrize("value", LEXICAL_INVALID_VALUES + [OVERSIZED_DIGIT_STRING])
def test_invalid_absolute_duration_lexical_forms_fail_during_settings_load(value):
    overrides = {"DRAFT_INACTIVITY_SECONDS": "60"} if value == "60_0" else {}
    assert_invalid_duration_setting(
        "DRAFT_ABSOLUTE_SECONDS",
        value,
        ABSOLUTE_MESSAGE,
        **overrides,
    )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "malformed",
        "2592001",
    ],
)
def test_invalid_absolute_durations_fail_during_settings_load(value):
    assert_invalid_duration_setting(
        "DRAFT_ABSOLUTE_SECONDS",
        value,
        ABSOLUTE_MESSAGE,
    )


def test_absolute_duration_must_not_be_lower_than_inactivity_duration():
    result = run_settings_probe(
        DRAFT_INACTIVITY_SECONDS="3600",
        DRAFT_ABSOLUTE_SECONDS="3599",
    )

    assert_settings_load_failed(
        result,
        "DRAFT_ABSOLUTE_SECONDS must be greater than or equal to DRAFT_INACTIVITY_SECONDS.",
    )


@pytest.mark.parametrize(
    ("value", "expected_seconds"),
    [
        ("30", 30),
        ("600", 600),
        ("900", 900),
    ],
)
def test_creation_key_lifetime_accepts_approved_bounds_and_default(value, expected_seconds):
    result = run_settings_probe(DRAFT_CREATION_KEY_LIFETIME_SECONDS=value)

    payload = parse_probe_output(result)
    assert payload["draft_creation_key_lifetime_seconds"] == expected_seconds


@pytest.mark.parametrize("value", LEXICAL_INVALID_VALUES + [OVERSIZED_DIGIT_STRING])
def test_invalid_creation_key_lifetime_lexical_forms_fail_during_settings_load(value):
    assert_invalid_duration_setting(
        "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
        value,
        CREATION_KEY_MESSAGE,
    )


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "901",
    ],
)
def test_invalid_creation_key_lifetime_fails_during_settings_load(value):
    assert_invalid_duration_setting(
        "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
        value,
        CREATION_KEY_MESSAGE,
    )


@pytest.mark.parametrize(
    ("name", "valid_value", "invalid_values", "expected_message", "overrides"),
    [
        (
            "DRAFT_INACTIVITY_SECONDS",
            "600",
            ["60_0", "+60", "  +60  ", "١٢٣", OVERSIZED_DIGIT_STRING],
            INACTIVITY_MESSAGE,
            {},
        ),
        (
            "DRAFT_ABSOLUTE_SECONDS",
            "600",
            ["60_0", "+60", " 60", "１２３", OVERSIZED_DIGIT_STRING],
            ABSOLUTE_MESSAGE,
            {"DRAFT_INACTIVITY_SECONDS": "60"},
        ),
        (
            "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
            "600",
            ["60_0", "+60", "60 ", "١٢٣", OVERSIZED_DIGIT_STRING],
            CREATION_KEY_MESSAGE,
            {},
        ),
    ],
)
def test_direct_duration_import_diagnostics(
    name, valid_value, invalid_values, expected_message, overrides
):
    success = run_settings_probe(**{name: valid_value, **overrides})
    payload = parse_probe_output(success)

    output_field = {
        "DRAFT_INACTIVITY_SECONDS": "draft_inactivity_seconds",
        "DRAFT_ABSOLUTE_SECONDS": "draft_absolute_seconds",
        "DRAFT_CREATION_KEY_LIFETIME_SECONDS": "draft_creation_key_lifetime_seconds",
    }[name]
    assert payload[output_field] == int(valid_value)

    for invalid_value in invalid_values:
        assert_invalid_duration_setting(
            name,
            invalid_value,
            expected_message,
            **overrides,
        )


def test_environment_examples_use_only_canonical_slice_one_names():
    env_example = (BACKEND_ROOT / ".env.example").read_text(encoding="utf-8")
    infrastructure = (BACKEND_ROOT.parent / "docs" / "infrastructure-plan.md").read_text(
        encoding="utf-8"
    )
    combined = f"{env_example}\n{infrastructure}"
    canonical_names = {
        "DRAFT_COOKIE_NAME",
        "DRAFT_COOKIE_PATH",
        "DRAFT_COOKIE_SECURE",
        "DRAFT_INACTIVITY_SECONDS",
        "DRAFT_ABSOLUTE_SECONDS",
        "DRAFT_CREATION_COOKIE_NAME",
        "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
    }

    assert all(name in env_example for name in canonical_names)
    assert all(name in infrastructure for name in canonical_names)
    assert "DRAFT_TTL_SECONDS" not in combined
    assert "DRAFT_ABSOLUTE_TTL_SECONDS" not in combined
