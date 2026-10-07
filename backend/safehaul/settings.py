"""
SafeHaul Kerala — Django settings.

Secrets are read from environment variables (or a .env file).
Copy backend/.env.example to backend/.env and fill in values.
Never commit .env to the repository.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# BASE_DIR is the backend/ directory (where manage.py lives).
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from backend/.env if it exists (silently ignored if absent).
load_dotenv(BASE_DIR / ".env")

# Repo root is one level above backend/.
REPO_ROOT = BASE_DIR.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-safehaul-dev-key-change-before-deploy",
)

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # SafeHaul apps (A owns)
    "safehaul.apps.SafehaulConfig",
    "risk.apps.RiskConfig",
    "routing.apps.RoutingConfig",
    "servicepoints.apps.ServicePointsConfig",
    # Stubs (teammates fill in)
    "weather.apps.WeatherConfig",
    "emergency.apps.EmergencyConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "safehaul.urls"

# ---------------------------------------------------------------------------
# Templates — serve from frontend/templates/
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [REPO_ROOT / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "safehaul.wsgi.application"
ASGI_APPLICATION = "safehaul.asgi.application"

# ---------------------------------------------------------------------------
# Database — SQLite for the MVP
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Static files — served from frontend/static/
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    REPO_ROOT / "frontend" / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target (deployment)

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    # No session/token auth needed for this demo API.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Data directory
# The loader tries DATA_DIR first, then falls back to the stand-in fixture.
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", str(REPO_ROOT / "data")))

# ---------------------------------------------------------------------------
# Default auto field
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging — show a warning when running on stand-in fixture data
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "safehaul": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "risk": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "routing": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "servicepoints": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
