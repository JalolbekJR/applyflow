import pytest
from django.db import connection


def pytest_runtest_setup(item):
    if "postgres" not in item.keywords:
        return
    if connection.vendor != "postgresql":
        pytest.skip(
            "PostgreSQL-only test requires DJANGO_SETTINGS_MODULE="
            "config.postgresql_test_settings, APPLYFLOW_POSTGRES_TESTS=1, and a "
            "PostgreSQL DATABASE_URL."
        )
