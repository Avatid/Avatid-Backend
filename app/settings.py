import io
import os
from urllib.parse import urlparse
import google.auth
import environ
from datetime import timedelta
from google.cloud import secretmanager
import json
import sentry_sdk
#from sentry_sdk.integrations.django import DjangoIntegration
from google.oauth2 import service_account

import base64
import json

from core.custom_logger import logger



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

def location(x):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), x)


env = environ.Env(DEBUG=(bool, False), ALLOWED_HOSTS=(list, ["*"]))
env.read_env()

PROJECT_NAME = os.environ.get("PROJECT_NAME")
VERSION = os.environ.get("VERSION", "LOCAL")


BACKEND_URL = os.environ.get("BACKEND_URL", "http://0.0.0.0")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
FRONTEND_VERIFY_EMAIL_URL = FRONTEND_URL + "/verify-email"

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS").split(",")

CLOUDRUN_SERVICE_URL = os.environ.get("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    ALLOWED_HOSTS = ["*"]
    
IS_DEVELOPMENT = bool(int(os.environ.get("IS_DEVELOPMENT", False)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.environ.get("DEBUG", False)))


try:
    _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default()
    if DEBUG:
        logger.info("Success auth by google", os.environ["GOOGLE_CLOUD_PROJECT"])
except google.auth.exceptions.DefaultCredentialsError:
    pass

def remove_comment_lines(payload):
    # Filter out comment lines
    lines = payload.split('\n')
    non_comment_lines = [line.strip() for line in lines if not line.strip().startswith('#')]
    return '\n'.join(non_comment_lines)


def get_secret(client, project_id, secret_name):
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")
    return payload


USE_SECRETS_MANAGER = bool(int(os.environ.get("USE_SECRETS_MANAGER", False)))

if USE_SECRETS_MANAGER:
    # Pull secrets from Secret Manager
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    client = secretmanager.SecretManagerServiceClient()
    settings_name = os.environ.get("SETTINGS_NAME", "django-settings")
    settings = get_secret(client, project_id, settings_name)
    settings = remove_comment_lines(settings) 
    if DEBUG:
        logger.info(settings, "settings loaded")
    env.read_env(io.StringIO(settings))
    service_account_name = os.environ.get("SERVICE_ACCOUNT", None)
    if service_account_name:
        secret_name = service_account_name + "-credentials"
        service_account_credentials = get_secret(client, project_id, secret_name)
        service_account_credentials = json.loads(service_account_credentials)
        GS_CREDENTIALS = service_account.Credentials.from_service_account_info(service_account_credentials)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "sdfm-bci^u39bw19op25fv@x)*zh7%!q!(@j3r1jez50--sdtd1w2132"
)

if DEBUG:
    ALLOWED_HOSTS += [
        "192.168.{}.{}".format(i, j) for i in range(256) for j in range(256)
    ]
    ALLOWED_HOSTS += ["127.0.0.1", "0.0.0.0"]

# Application definition

INSTALLED_APPS = [
    "user",
    
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "corsheaders",
    "hashids",
    "rest_framework",
    "drf_standardized_errors",  # Errors standardized
    "drf_spectacular",  # Swagger
    "drf_spectacular_sidecar",  # Swagger
    "nested_admin",
    "anymail",
    "django_filters",
    "leaflet",
    "core",
    "rest_framework_simplejwt.token_blacklist",
    "mail",
    "notifications",
    "shared",
    "sms",
    "onboarding",
    "business",
    "rating",
]
ANYMAIL = {
    'SENDGRID_API_KEY': os.environ.get('SENDGRID_KEY'),

    'ELASTIC_EMAIL_API_KEY': os.environ.get('ELASTIC_EMAIL_API_KEY'),
    'MANDRILL_API_KEY': os.environ.get('MANDRILL_API_KEY'),
}

DEFAULT_EMAIL_FROM = os.environ.get('DEFAULT_EMAIL_FROM')
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', "anymail.backends.sendgrid.EmailBackend")
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_USE_TLS = bool(int(os.environ.get('EMAIL_USE_TLS', True)))
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 527))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_POOL = os.environ.get('EMAIL_POOL')
UNSUBSCRIBE_EMAIL = os.environ.get('UNSUBSCRIBE_EMAIL', '')


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware must come after SessionMiddleware and before CommonMiddleware
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middlewares.CostumAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # "core.middlewares.LocaleTimeZoneMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

CORS_ORIGIN_WHITELIST = [
    "http://127.0.0.1:4200",
    "http://localhost:4200",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [location("templates")],
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

WSGI_APPLICATION = "wsgi.application"
X_FRAME_OPTIONS = "SAMEORIGIN"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPager",
    "PAGE_SIZE": 100,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Errors standardized
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    # Swagger schema
    "DEFAULT_SCHEMA_CLASS": "core.schema.CustomAutoSchema",
}

# Errors standardized
DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True}


# ---------------- SWAGGER ---------------- #
SPECTACULAR_SETTINGS = {
    "TITLE": f"{PROJECT_NAME} API",
    "DESCRIPTION": f"API documentation for {PROJECT_NAME} app",
    # CONTACT: Optional: MAY contain 'name', 'url', 'email'
    "CONTACT": {
        "name": f"{PROJECT_NAME}",
        "url": f"{FRONTEND_URL}",
    },
    # LICENSE: Optional: MUST contain 'name', MAY contain URL
    "LICENSE": {},
    "SERVERS": [
        {"url": f"{BACKEND_URL}", "description": f"{VERSION}"},
    ],
    "VERSION": f"{VERSION}",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    # OTHER SETTINGS
    "SWAGGER_UI_SETTINGS": {
        "displayOperationId": True,
        "persistAuthorization": True,
        "filter": True,
        "tryItOutEnabled": True,
        "withCredentials": True,
    },
}
# COMMAND FOR CREATE SCHEMA
# docker-compose exec app python manage.py spectacular --color --file schema.yml

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=365),
    "UPDATE_LAST_LOGIN": True,
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # this is default
    "guardian.backends.ObjectPermissionBackend",
)


DATABASE_TYPE = os.environ.get("DATABASE", "postgresql")
# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
if os.environ.get("DATABASE_URL"):
    db = env.db()
    if DEBUG:
        logger.info(env.db(), "DATA_BASE_ACCESS")
else:
    db = {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "HOST": os.environ.get("DB_HOST"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASS"),
    }

DATABASES = {"default": db}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_L10N = True

USE_TZ = True

gettext = lambda s: s

LANGUAGES = [
    ('en', gettext('English')),
    ('sq', gettext('Albanian')),
]
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]
MODELTRANSLATION_LANGUAGES  = ('en', 'sq')
LOCALE_PATHS = [os.path.join(CURR_DIR, "locale")]

AUTH_USER_MODEL = "user.User"
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

GOOGLE_AUTH_BASE_URL = "https://www.googleapis.com/oauth2/v3/userinfo?alt=json"
FACEBOOK_AUTH_BASE_URL = "https://graph.facebook.com/v12.0/me/?fields=email,id,name"
APPLE_AUTH_BASE_URL = "?scope=name%20email%20sub"
INSTAGRAM_AUTH_BASE_URL = "https://graph.instagram.com/me?fields=id,email"

DEFAULT_FILE_STORAGE = os.environ.get("STORAGE")

if DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
    logger.info("Using local storage ... ")
    STATIC_URL = '/static/'
    STATICFILES_DIRS = (
        os.path.join(BASE_DIR, 'static'),
    )
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    MEDIA_URL = '/upload/images/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'static/upload/images')

else:
    logger.info("Using google storage ... ")
    # if not local, use google storage
    STATICFILES_STORAGE = os.environ.get("STATIC_STORAGE")
    GS_STATIC_BUCKET_NAME = os.environ.get("GS_STATIC_BUCKET_NAME")
    GS_MEDIA_BUCKET_NAME = os.environ.get("GS_MEDIA_BUCKET_NAME")

    MEDIA_URL = os.environ.get("STORAGE_PUBLIC_PATH").format(GS_MEDIA_BUCKET_NAME)
    MEDIA_ROOT = os.environ.get("STORAGE_MEDIA_ROOT")

    STATIC_URL = os.environ.get("STORAGE_PUBLIC_PATH").format(GS_STATIC_BUCKET_NAME)
    STATIC_ROOT = os.environ.get("STORAGE_STATIC_ROOT")


MAX_UPLOAD_SIZE = 5242880 * 50 

TIME_BEFORE_REMINDER_MINUTES = int(os.environ.get('TIME_BEFORE_REMINDER_MINUTES', 60))
IS_TEST = bool(int(os.environ.get('IS_TEST', False)))
CRON_TIME_1HR = int(os.environ.get('CRON_TIME_1HR', 10))  # in minutes
CRON_TIME_24HR = int(os.environ.get('CRON_TIME_24HR', 60))  # in minutes

if IS_TEST:
    CRON_TIME_1HR = 1
    CRON_TIME_24HR = 10

logger.info(f"CRON_TIME_1HR: {CRON_TIME_1HR}, CRON_TIME_24HR: {CRON_TIME_24HR}")


# --------- CELERY TASKS SCHEDULE --------- #
CELERY_BEAT_SCHEDULE = {
    # 'celery_test_task': {
    #     'task': 'celery_test_task',
    #     'schedule': timedelta(minutes=1),
    # },
    # Use the registered Celery task name, not the Python function name
    'send_reminder_notification': {
        'task': 'send_reminder_notification',
        'schedule': timedelta(minutes=CRON_TIME_1HR),
    },
    'send_reminder_notification_daily': {
        'task': 'send_reminder_notification_daily',
        'schedule': timedelta(minutes=CRON_TIME_24HR),
    },
}

# ------------- CELERY TASKS -------------- #
CELERY_TASK_ROUTES = {
    # Celery health check / example task
    'celery_test_task': {'queue': 'main-queue'},
    "send_verify_email": {"queue": "main-queue"},
    "send_password_reset_request_email": {"queue": "main-queue"},
    "send_fire_push": {"queue": "main-queue"},
    
    "send_booked_notification": {"queue": "main-queue"},
    "send_booked_mail": {"queue": "main-queue"},
    "send_canceled_notification": {"queue": "main-queue"},
    "send_canceled_mail": {"queue": "main-queue"},
    "send_booking_updated_notification": {"queue": "main-queue"},
    "send_booking_updated_mail": {"queue": "main-queue"},
    "send_apply_notification": {"queue": "main-queue"},
    "send_apply_email": {"queue": "main-queue"},
    "send_apply_response_notification": {"queue": "main-queue"},
    "send_apply_response_email": {"queue": "main-queue"},
    "send_apply_response_notification_to_freelancer": {"queue": "main-queue"},

    "send_reminder_notification": {"queue": "main-queue"},
    "send_reminder_notification_daily": {"queue": "main-queue"},
}


# ----------------- SENTRY ---------------- #
# SENTRY_DSN = os.environ.get("SENTRY_DSN")
# sentry_sdk.init(
#     dsn=SENTRY_DSN,
#     integrations=[DjangoIntegration()],
#     traces_sample_rate=1.0,
#     send_default_pii=True,
# )

# ----------------- REDIS ----------------- #
REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_SERVER = os.environ.get("REDIS_SERVER")
REDIS_APP_DB = os.environ.get("REDIS_APP_DB")
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_SERVER}/{REDIS_APP_DB}"
RESET_TOKEN_LENGTH = 5
RESET_CODE_EXPIRE = 3600

# ---------------- TWILIO ----------------- #
# TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
# TWILIO_SERVICE_UID = os.environ.get("TWILIO_SERVICE_UID")

# ---------------- EMAILS ----------------- #
# SENDGRID_KEY = os.environ.get("SENDGRID_KEY")
# DEFAULT_EMAIL_FROM = os.environ.get("DEFAULT_EMAIL_FROM")


DEFAULT_DISTANCE_BORDER = os.environ.get("DEFAULT_DISTANCE_BORDER", 1000) # 1 km by default

MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD", None)


FIRE_BASE_CRED_BASE64 = os.environ.get("FIRE_BASE_CRED_BASE64", "")
CHATS_COLLECTION_NAME = os.environ.get("CHATS_COLLECTION_NAME", "chats")
FIRE_BASE_CRED_JSON = {}

try:
    FIRE_BASE_CRED_JSON = json.loads(base64.b64decode(FIRE_BASE_CRED_BASE64).decode("utf-8"))
except Exception as e:
    logger.info("FIRE_BASE_CRED_BASE64 is not valid json")
    logger.error(e)

DEFAULT_DISTANCE_BORDER = int(os.environ.get("DEFAULT_DISTANCE_BORDER", 1000))  # 1 km by default

# SUBSCRIPTIONS
APPLE_SECRET_SHARED_KEY = os.environ.get('APPLE_SECRET_SHARED_KEY')
GOOGLE_STORE_PRIVATE_KEY_PATH = os.environ.get('GOOGLE_STORE_PRIVATE_KEY_PATH')
FAKE_PAYMENT = bool(int(os.environ.get('FAKE_PAYMENT', False)))

GMAPS_API_KEY = os.environ.get('GMAPS_API_KEY', '')

TWILIO_SERVICE_UID = os.environ.get('TWILIO_SERVICE_UID', '')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')

IGNORE_TWILIO_CODE_CHECK = bool(int(os.environ.get('IGNORE_TWILIO_CODE_CHECK', False)))


APP_DEEP_LINK = os.environ.get('APP_DEEP_LINK', 'https://dua-flavor.web.app/booking?bookingUid=')

DEVICE_ID_HEADER = os.environ.get('DEVICE_ID_HEADER', 'X-Device-ID')
DEVICE_MIDDLEWARE_IGNORED_PATHS = [
    '/api/user/auth/logout/all/',

    '/api/user/auth/refresh/',
    '/api/user/auth/email/',

    '/api/user/registration/email/',

    '/api/user/auth/google/',
    '/api/user/auth/apple/',
    '/api/user/auth/facebook/',
    '/api/user/auth/instagram/',

    '/api/email/verify/submit/',

    '/api/sms/verify/submit/',
    '/api/sms/verify/request/',
    '/api/sms/verify/request/only/',
    '/api/sms/verify/submit/only/',
]
