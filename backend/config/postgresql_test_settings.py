import os
import re

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .settings import database_config

POSTGRES_TEST_GUARD = "APPLYFLOW_POSTGRES_TESTS"
POSTGRES_TEST_DATABASE_NAME = "APPLYFLOW_POSTGRES_TEST_DATABASE_NAME"
POSTGRES_TEST_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
POSTGRES_TEST_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_postgres_test_database_name(value: str | None, *, base_name: str) -> str:
    message = (
        f"{POSTGRES_TEST_DATABASE_NAME} must start with test_, use only ASCII letters, "
        "digits, and underscores, and differ from the configured database name."
    )
    if not isinstance(value, str) or not value:
        raise ImproperlyConfigured(message)
    if value != value.strip() or not POSTGRES_TEST_NAME_RE.fullmatch(value):
        raise ImproperlyConfigured(message)
    if not value.startswith("test_") or value == base_name:
        raise ImproperlyConfigured(message)
    lowered = value.lower()
    if lowered in {"postgres", "template0", "template1", "applyflow"}:
        raise ImproperlyConfigured(message)
    if "production" in lowered or lowered.startswith("prod_") or lowered.endswith("_prod"):
        raise ImproperlyConfigured(message)
    return value


def validate_postgres_test_connection(config: dict[str, object]) -> None:
    if config.get("ENGINE") != "django.db.backends.postgresql":
        raise ImproperlyConfigured("PostgreSQL verification requires a PostgreSQL DATABASE_URL.")
    host = str(config.get("HOST") or "")
    if host not in POSTGRES_TEST_HOSTS:
        raise ImproperlyConfigured("PostgreSQL verification must use a loopback PostgreSQL host.")


if os.getenv(POSTGRES_TEST_GUARD) != "1":
    raise ImproperlyConfigured(
        f"Set {POSTGRES_TEST_GUARD}=1 to use the PostgreSQL verification settings."
    )

_database_url = os.getenv("DATABASE_URL")
if not _database_url:
    raise ImproperlyConfigured("DATABASE_URL is required for PostgreSQL verification.")

_postgres_config = database_config(_database_url)
validate_postgres_test_connection(_postgres_config)
_test_database_name = validate_postgres_test_database_name(
    os.getenv(POSTGRES_TEST_DATABASE_NAME, "test_applyflow_postgres_verification"),
    base_name=str(_postgres_config["NAME"]),
)
_postgres_config["CONN_MAX_AGE"] = 0
_postgres_config["CONN_HEALTH_CHECKS"] = False
_postgres_config["TEST"] = {"NAME": _test_database_name}
_postgres_config["OPTIONS"] = {
    "options": "-c lock_timeout=5000 -c statement_timeout=30000",
}

DATABASES = {"default": _postgres_config}
