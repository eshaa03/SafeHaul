"""
SafeHaul Kerala — standalone Django settings for the frontend app.

PURPOSE: lets Member B run and test the frontend in isolation while
A's backend skeleton is not yet on main. This is NOT the production
settings file. A will create backend/safehaul/settings.py and
incorporate the relevant TEMPLATES and STATICFILES_DIRS entries from here.

Usage:
    cd SafeHaul
    pip install django
    python frontend_project/manage.py runserver
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root (SafeHaul/)

SECRET_KEY = 'dev-only-not-a-secret-b1-standalone'  # not for production

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    # No auth/admin needed for the standalone frontend demo.
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'frontend_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
