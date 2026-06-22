import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.settings import database_config


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
