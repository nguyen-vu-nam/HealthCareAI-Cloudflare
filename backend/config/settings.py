import os

# Cloudflare Workers runtime bindings are available only in the deployed Worker.
try:
    from workers import env as cf_env
except Exception:
    cf_env = None

def setting(name, default=""):
    if cf_env is not None:
        try:
            value = getattr(cf_env, name)
            if value is not None:
                return str(value)
        except Exception:
            pass
    return os.getenv(name, default)

from pathlib import Path
from datetime import timedelta
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

IS_CLOUDFLARE = cf_env is not None
SECRET_KEY = setting("DJANGO_SECRET_KEY", "")
if IS_CLOUDFLARE and not SECRET_KEY:
    raise RuntimeError("Thiếu Cloudflare Secret DJANGO_SECRET_KEY.")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-change-this-secret"  # Chỉ dùng local; phải thay trong môi trường thật.

# Read AI configuration from Worker bindings/secrets in production, or environment/.env locally.
AI_API_BASE_URL = setting("AI_API_BASE_URL", "")
AI_API_KEY = setting("AI_API_KEY", "")
AI_MODEL = setting("AI_MODEL", "cohere/command-a-plus")
DEBUG = setting("DJANGO_DEBUG", "false" if IS_CLOUDFLARE else "true").lower() == "true"
_default_hosts = ".workers.dev" if IS_CLOUDFLARE else "127.0.0.1,localhost,0.0.0.0,*"
ALLOWED_HOSTS = [x.strip() for x in setting("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "rest_framework_simplejwt",
    "health",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if IS_CLOUDFLARE:
    DATABASES = {
        "default": {
            "ENGINE": "django_cf.db.backends.d1",
            "CLOUDFLARE_BINDING": "DB",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [x.strip() for x in setting("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
# Chỉ mở CORS toàn mạng trong chế độ phát triển LAN. Không dùng cấu hình này khi public Internet.
CORS_ALLOW_ALL_ORIGINS = DEBUG and setting("CORS_ALLOW_ALL_ORIGINS", "True").lower() == "true"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Production security defaults. The app is served from the same Worker origin.
if IS_CLOUDFLARE:
    CORS_ALLOW_ALL_ORIGINS = False
    SECURE_SSL_REDIRECT = False  # Cloudflare terminates HTTPS at the edge.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
