import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ROOT = BASE_DIR.parent.parent / "尼泊尔泥石流巨灾"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-demo-only-change-before-deployment")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"


def environment_list(name, defaults):
    raw_value = os.environ.get(name, "")
    if not raw_value.strip():
        return defaults
    return [item.strip() for item in raw_value.replace(";", ",").split(",") if item.strip()]


ALLOWED_HOSTS = environment_list("DJANGO_ALLOWED_HOSTS", ["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = environment_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_COOKIE_SECURE", "0") == "1"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE
USE_X_FORWARDED_HOST = os.environ.get("DJANGO_USE_X_FORWARDED_HOST", "0") == "1"
if os.environ.get("DJANGO_TRUST_PROXY_PROTO", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
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
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
