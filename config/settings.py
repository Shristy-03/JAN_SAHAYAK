"""Environment-driven Django settings for JAN SAHAYAK."""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Return an environment variable parsed as a boolean."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def required_env(name: str) -> str:
    """Return a required environment variable or fail clearly at startup."""
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"The {name} environment variable must be configured.")
    return value


SECRET_KEY = required_env("SECRET_KEY")
DEBUG = env_bool("DEBUG")
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'departments',
    'complaints',
    'dashboard',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.map_tiles',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASE_CONN_MAX_AGE = int(os.getenv('DATABASE_CONN_MAX_AGE', '60'))
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()

if DATABASE_URL:
    # Render supplies this from the linked managed PostgreSQL instance.
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=DATABASE_CONN_MAX_AGE,
            conn_health_checks=True,
        )
    }
else:
    # Preserve local PostgreSQL configuration without committing credentials.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': required_env('DATABASE_NAME'),
            'USER': required_env('DATABASE_USER'),
            'PASSWORD': required_env('DATABASE_PASSWORD'),
            'HOST': required_env('DATABASE_HOST'),
            'PORT': required_env('DATABASE_PORT'),
            'CONN_MAX_AGE': DATABASE_CONN_MAX_AGE,
            'CONN_HEALTH_CHECKS': True,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT') or BASE_DIR / 'media')
USE_S3_MEDIA = env_bool('USE_S3_MEDIA')
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage' if USE_S3_MEDIA else 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

if USE_S3_MEDIA:
    # S3-compatible object storage keeps user uploads durable and available to
    # all application instances. The bucket's public-read delivery endpoint
    # must be configured by the production storage provider.
    AWS_ACCESS_KEY_ID = required_env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = required_env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = required_env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME') or None
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL') or None
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN') or None
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
elif not DEBUG:
    raise ImproperlyConfigured(
        'Production deployments must set USE_S3_MEDIA=True and configure S3-compatible media storage.'
    )

# Esri's ArcGIS Online World Street Map is the no-key local-development
# default. Production deployments can configure an approved provider endpoint
# and its exact attribution through environment variables without changing
# Leaflet templates.
DEFAULT_MAP_TILE_URL = (
    'https://server.arcgisonline.com/ArcGIS/rest/services/'
    'World_Street_Map/MapServer/tile/{z}/{y}/{x}'
)
DEFAULT_MAP_TILE_ATTRIBUTION = (
    'Tiles &copy; <a href="https://www.esri.com/">Esri</a> — Sources: Esri, HERE, Garmin, USGS, '
    'Intermap, INCREMENT P, NRCan, Esri Japan, METI, Esri China (Hong Kong), Esri Korea, '
    'Esri (Thailand), NGCC, &copy; OpenStreetMap contributors, and the GIS User Community'
)
MAP_TILE_URL = (os.getenv('MAP_TILE_URL') or DEFAULT_MAP_TILE_URL).strip()
MAP_TILE_ATTRIBUTION = (os.getenv('MAP_TILE_ATTRIBUTION') or DEFAULT_MAP_TILE_ATTRIBUTION).strip()
MAP_TILE_MAX_ZOOM = int(os.getenv('MAP_TILE_MAX_ZOOM') or '19')

# Render terminates HTTPS before forwarding requests to Django.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0' if DEBUG else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', default=not DEBUG)

# The console backend keeps local verification flows usable without exposing or
# requiring SMTP credentials. Phase 10 will add the notification service.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND') or (
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@jansahayak.local')

AUTHENTICATION_BACKENDS = ['accounts.backends.EmailOrUsernameModelBackend']
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profile'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'
