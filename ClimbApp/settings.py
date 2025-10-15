from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- Dev defaults ----
DEBUG = True  # keep True for local dev
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-_replace_with_a_random_long_string_for_local_dev_"
)
ALLOWED_HOSTS: list[str] = []  # fine empty with DEBUG=True

# ---- Apps ----
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "routes",
]

# ---- Middleware ----
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ---- URLs / WSGI / ASGI (note the new project name) ----
ROOT_URLCONF = "ClimbApp.urls"
WSGI_APPLICATION = "ClimbApp.wsgi.application"
ASGI_APPLICATION = "ClimbApp.asgi.application"

# ---- Templates (global templates/ folder) ----
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # <— global templates
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

# ---- Database (SQLite for dev) ----
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---- Password validators (keep defaults or adjust as needed) ----
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---- I18N / TZ (use your prefs) ----
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---- Static (global static/ folder) ----
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ---- Auth redirects ----
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
