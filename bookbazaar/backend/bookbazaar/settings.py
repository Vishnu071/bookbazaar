# settings.py — Django + MySQL (PyMySQL), Render-friendly + local dev

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Use PyMySQL instead of mysqlclient (works on Render no-Docker) ---
try:
    import pymysql  # pip install pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

# Optional: parse DATABASE_URL strings (mysql:// or postgres://)
try:
    import dj_database_url  # pip install dj-database-url
except Exception:
    dj_database_url = None

# -------------------------------------------------------------------
# Base paths & .env
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # local only; Render uses dashboard env vars

# -------------------------------------------------------------------
# Security / core
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-dev-secret")
DEBUG = os.getenv("DEBUG", "1").lower() in {"1", "true", "yes", "on"}

# ALLOWED_HOSTS in Render env (example):
# ALLOWED_HOSTS=bookbazaar-0jew.onrender.com,localhost,127.0.0.1
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

# CSRF trusted origins (full scheme). In Render:
# CSRF_TRUSTED_ORIGINS=https://bookbazaar-0jew.onrender.com
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# Honor Render proxy for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -------------------------------------------------------------------
# Apps
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",  # because DRF uses DjangoFilterBackend

    # Local apps
    "users",
    "products",
    "orders",
    "payments",
    "recommendations",
    "analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files in prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",       # keep before CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bookbazaar.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bookbazaar.wsgi.application"

# -------------------------------------------------------------------
# Database
# Priority: DATABASE_URL -> individual MySQL env vars -> local SQLite
# -------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and dj_database_url:
    # supports mysql://user:pass@host:3306/dbname  OR postgres://...
    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)
else:
    # individual MySQL pieces (optional)
    db_name = os.getenv("DATABASE_NAME")
    db_user = os.getenv("DATABASE_USER")
    db_pass = os.getenv("DATABASE_PASSWORD")
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT", "3306")
    if all([db_name, db_user, db_pass, db_host]):
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.mysql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_pass,
            "HOST": db_host,
            "PORT": db_port,
            "OPTIONS": {"charset": "utf8mb4"},
        }

# --- Normalize MySQL SSL option for PyMySQL (Railway/Render) ---
# If DATABASE_URL has ?ssl=true, dj-database-url sets OPTIONS={"ssl": True}
# PyMySQL expects a dict ({} or {"ca": "..."}), not a boolean.
try:
    db = DATABASES["default"]
    if db.get("ENGINE", "").endswith("mysql"):
        db.setdefault("OPTIONS", {})
        ssl_opt = db["OPTIONS"].get("ssl")
        if isinstance(ssl_opt, bool) and ssl_opt:
            db["OPTIONS"]["ssl"] = {}  # enable TLS with default context
except Exception:
    pass

# -------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"  # remove if not using a custom user model

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & Media
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static_collected"  # collectstatic output

# Only add extra static dir if it exists (prevents collectstatic warnings)
_extra_static = BASE_DIR / "staticfiles"
if _extra_static.exists():
    STATICFILES_DIRS = [ _extra_static ]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# WhiteNoise for hashed/cached assets
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------
# DRF & CORS
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# Dev: open CORS; Prod: set specific origins in env
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "1").lower() in {"1", "true", "yes", "on"}
# Or:
# CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS","").split(",") if o.strip()]

# -------------------------------------------------------------------
# Payments / Redis (optional)
# -------------------------------------------------------------------
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

# -------------------------------------------------------------------
# Security flags for production (can be relaxed in dev via env)
# -------------------------------------------------------------------
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1").lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1").lower() in {"1", "true", "yes", "on"}
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1").lower() in {"1", "true", "yes", "on"}

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
