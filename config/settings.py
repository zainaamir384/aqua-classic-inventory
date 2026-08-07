"""Django settings for Aqua Classic Water Filters."""

import os
import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qsl

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    import environ
    env = environ.Env(
        DEBUG=(bool, False),
        SECRET_KEY=(str, "django-insecure-change-me"),
        ALLOWED_HOSTS=(list, ["*"]),
        DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    )
    if (BASE_DIR / ".env").exists():
        environ.Env.read_env(BASE_DIR / ".env")
except ImportError:
    class env:
        @staticmethod
        def str(key, default=""):
            return os.environ.get(key, default)
        @staticmethod
        def bool(key, default=False):
            val = os.environ.get(key, str(default))
            return str(val).lower() in ("true", "1", "yes")
        @staticmethod
        def int(key, default=0):
            try:
                return int(os.environ.get(key, str(default)))
            except Exception:
                return default
        @staticmethod
        def list(key, default=None):
            val = os.environ.get(key, "")
            return [x.strip() for x in val.split(",")] if val else (default or ["*"])

SECRET_KEY = os.environ.get("SECRET_KEY", "aqua-classic-vercel-demo-secret-key-2026")
DEBUG = os.environ.get("DEBUG", "1").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "accounts",
    "catalog",
    "inventory",
    "suppliers",
    "sales",
    "services",
    "dashboard",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Pure SQLite Database Configuration (Demo Environment)
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
tmp_db = Path("/tmp/db.sqlite3") if IS_VERCEL else BASE_DIR / "db.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": tmp_db,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
WHITENOISE_USE_FINDERS = True

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "zainaamir516@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "xxjf qvyz jmgr cxqe")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Aqua Classic Water Filters <zainaamir516@gmail.com>")

# Session Configuration (Signed Cookies for Vercel Serverless Persistence)
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 604800  # Keep session active for 7 days
