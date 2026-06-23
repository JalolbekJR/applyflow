import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = BASE_DIR.parent
APPROVED_DRAFT_COOKIE_PATH = "/api/v1/application-drafts/"
DRAFT_COOKIE_PATH_ERROR = "DRAFT_COOKIE_PATH must match the approved application drafts path."
DOCUMENT_STORAGE_BACKENDS = {"local_private"}
DEFAULT_DOCUMENT_PRIVATE_ROOT = BASE_DIR / ".private-documents"
DOCUMENT_STORAGE_BACKEND_ERROR = "DOCUMENT_STORAGE_BACKEND must be exactly one of: local_private."
DOCUMENT_PRIVATE_ROOT_ERROR = "DOCUMENT_PRIVATE_ROOT must be an absolute private directory path."


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def env_bounded_positive_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    message = f"{name} must be an ASCII decimal integer between {minimum} and {maximum} seconds."
    raw_value = os.getenv(name)
    if raw_value is None:
        parsed = default
        if parsed < minimum or parsed > maximum:
            raise ImproperlyConfigured(message)
        return parsed
    if not isinstance(raw_value, str):
        raise ImproperlyConfigured(message)
    if not raw_value.isascii() or not raw_value.isdigit():
        raise ImproperlyConfigured(message)
    if len(raw_value) > len(str(maximum)):
        raise ImproperlyConfigured(message)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ImproperlyConfigured(message) from exc
    if parsed < minimum or parsed > maximum:
        raise ImproperlyConfigured(message)
    return parsed


def validate_draft_cookie_path(value: object) -> str:
    if not isinstance(value, str):
        raise ImproperlyConfigured(DRAFT_COOKIE_PATH_ERROR)
    if value != APPROVED_DRAFT_COOKIE_PATH:
        raise ImproperlyConfigured(DRAFT_COOKIE_PATH_ERROR)
    if (
        not value.startswith("/")
        or not value.endswith("/")
        or value == "/"
        or any(character.isspace() for character in value)
        or any(character in value for character in ("?", "#", ";", "\\"))
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "://" in value
    ):
        raise ImproperlyConfigured(DRAFT_COOKIE_PATH_ERROR)
    return value


def validate_document_storage_backend(value: object) -> str:
    if not isinstance(value, str) or value not in DOCUMENT_STORAGE_BACKENDS:
        raise ImproperlyConfigured(DOCUMENT_STORAGE_BACKEND_ERROR)
    return value


def validate_document_private_root(value: object | None, *, app_env: str) -> Path:
    if value is None:
        if app_env != "development":
            raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)
        candidate = DEFAULT_DOCUMENT_PRIVATE_ROOT
    else:
        if not isinstance(value, str) or not value:
            raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)
        if any(
            character == "\x00" or ord(character) < 32 or ord(character) == 127
            for character in value
        ):
            raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)
        candidate = Path(value)
        if not candidate.is_absolute():
            raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)

    resolved = candidate.resolve(strict=False)
    if resolved.anchor == str(resolved):
        raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)
    repository_root = REPOSITORY_ROOT.resolve(strict=False)
    if resolved == repository_root:
        raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)

    public_roots = [
        BASE_DIR / "static",
        BASE_DIR / "staticfiles",
        BASE_DIR / "media",
        REPOSITORY_ROOT / "static",
        REPOSITORY_ROOT / "staticfiles",
        REPOSITORY_ROOT / "media",
        REPOSITORY_ROOT / "frontend" / "public",
        REPOSITORY_ROOT / "frontend" / "app" / "public",
    ]
    for public_root in public_roots:
        resolved_public_root = public_root.resolve(strict=False)
        if resolved == resolved_public_root or resolved.is_relative_to(resolved_public_root):
            raise ImproperlyConfigured(DOCUMENT_PRIVATE_ROOT_ERROR)
    return resolved


def draft_cookie_secure(app_env: str, *, configured: bool) -> bool:
    return app_env != "development" or configured


def database_config(url: str | None) -> dict[str, object]:
    if not url:
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}

    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.path.strip("/"):
        raise ImproperlyConfigured("DATABASE_URL must be a complete PostgreSQL URL.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }


APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = env_bool("DJANGO_DEBUG", APP_ENV == "development")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if APP_ENV != "development":
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is required outside development.")
    SECRET_KEY = "development-only-not-for-shared-environments"

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,testserver" if APP_ENV == "development" else "",
)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required outside development.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.vacancies",
    "apps.applications",
    "apps.documents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
CSRF_FAILURE_VIEW = "config.api_errors.csrf_failure"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if APP_ENV != "development" and not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL is required outside development.")
DATABASES = {"default": database_config(DATABASE_URL)}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 0
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

DRAFT_COOKIE_NAME = os.getenv("DRAFT_COOKIE_NAME", "applyflow_draft")
DRAFT_COOKIE_PATH = validate_draft_cookie_path(
    os.getenv("DRAFT_COOKIE_PATH", APPROVED_DRAFT_COOKIE_PATH)
)
DRAFT_CREATION_COOKIE_NAME = os.getenv("DRAFT_CREATION_COOKIE_NAME", "applyflow_draft_creation")
DRAFT_COOKIE_SECURE = draft_cookie_secure(
    APP_ENV, configured=env_bool("DRAFT_COOKIE_SECURE", False)
)
DRAFT_INACTIVITY_SECONDS = env_bounded_positive_int(
    "DRAFT_INACTIVITY_SECONDS",
    7 * 24 * 60 * 60,
    minimum=60,
    maximum=7 * 24 * 60 * 60,
)
DRAFT_ABSOLUTE_SECONDS = env_bounded_positive_int(
    "DRAFT_ABSOLUTE_SECONDS",
    30 * 24 * 60 * 60,
    minimum=60,
    maximum=30 * 24 * 60 * 60,
)
if DRAFT_ABSOLUTE_SECONDS < DRAFT_INACTIVITY_SECONDS:
    raise ImproperlyConfigured(
        "DRAFT_ABSOLUTE_SECONDS must be greater than or equal to DRAFT_INACTIVITY_SECONDS."
    )
DRAFT_CREATION_KEY_LIFETIME_SECONDS = env_bounded_positive_int(
    "DRAFT_CREATION_KEY_LIFETIME_SECONDS",
    10 * 60,
    minimum=30,
    maximum=15 * 60,
)
DRAFT_INACTIVITY_LIFETIME = timedelta(seconds=DRAFT_INACTIVITY_SECONDS)
DRAFT_ABSOLUTE_LIFETIME = timedelta(seconds=DRAFT_ABSOLUTE_SECONDS)
DRAFT_CREATION_KEY_LIFETIME = timedelta(seconds=DRAFT_CREATION_KEY_LIFETIME_SECONDS)

DOCUMENT_STORAGE_BACKEND = validate_document_storage_backend(
    os.getenv("DOCUMENT_STORAGE_BACKEND", "local_private")
)
DOCUMENT_PRIVATE_ROOT = validate_document_private_root(
    os.getenv("DOCUMENT_PRIVATE_ROOT"),
    app_env=APP_ENV,
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "config.api_errors.exception_handler",
}
