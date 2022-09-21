"""
Django settings for apphub project.

Generated by 'django-admin startproject' using Django 4.0.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path
from urllib.parse import urlparse

from util.reserved import reserved_names

try:
    import apphub.local_settings
except:  # noqa: E722
    pass


def get_env_value(key, default=None):
    # value = os.environ.get('APPHUB_' + key, None)
    value = os.environ.get(key, None)
    if value is not None:
        return value
    try:
        return getattr(apphub.local_settings, key, default)
    except:  # noqa: E722
        return default


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value(
    "SECRET_KEY",
    default="django-insecure-@&gp$u=3+j%te3+^d)4**8)csv5u^3u$(6g&$m8&t*ao61hc$e",
)
# gp$u=3+j%te3+
# **8)csv5u^3
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env_value("DEBUG_MODE", default=False)

EXTERNAL_WEB_URL = get_env_value("EXTERNAL_WEB_URL", default="http://localhost:8000")

EXTERNAL_API_URL = get_env_value("EXTERNAL_API_URL", default=EXTERNAL_WEB_URL + "/api")
if EXTERNAL_API_URL:
    ALLOWED_HOSTS = [urlparse(EXTERNAL_API_URL).hostname]
else:
    ALLOWED_HOSTS = []

API_URL_PREFIX = urlparse(EXTERNAL_API_URL).path
if API_URL_PREFIX and len(API_URL_PREFIX) > 0:
    API_URL_PREFIX = API_URL_PREFIX[1:]

# Application definition

INSTALLED_APPS = [
    "user.apps.UserConfig",
    "organization.apps.OrganizationConfig",
    "application.apps.ApplicationConfig",
    "distribute.apps.DistributeConfig",
    "system.apps.SystemConfig",
    "documentation.apps.DocumentationConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "apphub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "apphub.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES_ENGINE = get_env_value(
    "DATABASES_ENGINE", default="django.db.backends.sqlite3"
)
DATABASES = {
    "default": {
        "ENGINE": DATABASES_ENGINE,
    }
}
if DATABASES_ENGINE == "django.db.backends.sqlite3":
    DATABASES["default"]["NAME"] = get_env_value(
        "DATABASE_NAME", default=BASE_DIR / "db.sqlite3"
    )
else:
    DATABASES["default"]["NAME"] = get_env_value("DATABASE_NAME")
    DATABASES["default"]["HOST"] = get_env_value("DATABASE_HOST")
    DATABASES["default"]["PORT"] = get_env_value("DATABASE_PORT")
    DATABASES["default"]["USER"] = get_env_value("DATABASE_USER")
    DATABASES["default"]["PASSWORD"] = get_env_value("DATABASE_PASSWORD")

KEY_PREFIX = "apphub_"

# Email
EMAIL_HOST = get_env_value("EMAIL_HOST", "localhost")
EMAIL_PORT = int(get_env_value("EMAIL_PORT", 25))
EMAIL_USE_SSL = get_env_value("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = get_env_value("EMAIL_HOST_USER", "")
DEFAULT_FROM_EMAIL = get_env_value("DEFAULT_FROM_EMAIL", "webmaster@localhost")
EMAIL_HOST_PASSWORD = get_env_value("EMAIL_HOST_PASSWORD", "")
EMAIL_SUBJECT_PREFIX = "[" + get_env_value("APP_NAME", "AppHub") + "]"


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
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

DEFAULT_RENDERER_CLASSES = ("rest_framework.renderers.JSONRenderer",)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "user.authentication.BearerTokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": DEFAULT_RENDERER_CLASSES,
    "EXCEPTION_HANDLER": "util.exception.custom_exception_handler",
}

if EXTERNAL_WEB_URL:
    CSRF_COOKIE_DOMAIN = urlparse(EXTERNAL_WEB_URL).hostname

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = get_env_value("LANGUAGE_CODE", default="en-us")

TIME_ZONE = get_env_value("TIME_ZONE", default="America/Chicago")
USE_I18N = True

USE_TZ = True

FONT_FILE = get_env_value("FONT_FILE", "DejaVuSerif.ttf")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_ROOT = get_env_value("STATIC_ROOT", default="var/static/")
STATIC_URL = get_env_value("STATIC_URL", default=EXTERNAL_WEB_URL + "/static/")

MEDIA_ROOT = get_env_value("MEDIA_ROOT", default="var/media/")
MEDIA_URL = get_env_value("MEDIA_URL", default=EXTERNAL_WEB_URL + "/media/")

STATICFILES_STORAGE = get_env_value(
    "STATICFILES_STORAGE", "django.contrib.staticfiles.storage.StaticFilesStorage"
)
# DEFAULT_FILE_STORAGE = get_env_value('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage') # noqa: E501

STORAGE_TYPE = get_env_value('STORAGE_TYPE', 'LocalFileSystem')
STORAGE_MAP = {
    "LocalFileSystem": "storage.nginx.NginxPrivateFileStorage",
    "AlibabaCloudOSS": "storage.aliyun.AliyunOssMediaStorage",
    "AmazonAWSS3": "storage.s3.AWSS3MediaStorage"
}

DEFAULT_FILE_STORAGE = STORAGE_MAP.get(STORAGE_TYPE, "storage.nginx.NginxPrivateFileStorage")  # noqa: E501


if DEFAULT_FILE_STORAGE == "storage.aliyun.AliyunOssMediaStorage":
    ALIYUN_OSS_ACCESS_KEY_ID = get_env_value("ALIYUN_OSS_ACCESS_KEY_ID")
    ALIYUN_OSS_ACCESS_KEY_SECRET = get_env_value("ALIYUN_OSS_ACCESS_KEY_SECRET")
    ALIYUN_OSS_BUCKET_NAME = get_env_value("ALIYUN_OSS_BUCKET_NAME")
    ALIYUN_OSS_ENDPOINT = get_env_value("ALIYUN_OSS_ENDPOINT")
    ALIYUN_OSS_PUBLIC_READ = get_env_value("ALIYUN_OSS_PUBLIC_READ", False)
elif DEFAULT_FILE_STORAGE == "storage.s3.AWSS3MediaStorage":
    AWS_ACCESS_KEY_ID = get_env_value("AWS_STORAGE_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_env_value("AWS_STORAGE_SECRET_ACCESS_KEY")
    AWS_S3_REGION_NAME = get_env_value("AWS_STORAGE_REGION_NAME")
    AWS_STORAGE_BUCKET_NAME = get_env_value("AWS_STORAGE_BUCKET_NAME")
    AWS_STORAGE_PUBLIC_READ = get_env_value("AWS_STORAGE_PUBLIC_READ", False)
    if AWS_STORAGE_PUBLIC_READ:
        AWS_DEFAULT_ACL = "public-read"
    AWS_LOCATION = MEDIA_ROOT
    if not urlparse(MEDIA_URL).hostname.endswith(".s3.amazonaws.com"):
        AWS_S3_CUSTOM_DOMAIN = urlparse(MEDIA_URL).hostname
    AWS_CLOUDFRONT_KEY = get_env_value("AWS_CLOUDFRONT_KEY", "").encode('ascii')
    AWS_CLOUDFRONT_KEY_ID = get_env_value("AWS_CLOUDFRONT_KEY_ID", "")


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# User
SOCIAL_ACCOUNT = get_env_value("SOCIAL_ACCOUNT", default="")
if SOCIAL_ACCOUNT:
    SOCIAL_ACCOUNT_LIST = SOCIAL_ACCOUNT.split(",")
else:
    SOCIAL_ACCOUNT_LIST = []
if SOCIAL_ACCOUNT_LIST:
    SOCIALACCOUNT_PROVIDERS = {
        "custom_feishu": {
            "display_name": get_env_value("FEISHU_DISPLAY_NAME", "feishu"),
            "APP": {
                "client_id": get_env_value("FEISHU_APP_ID", ""),
                "secret": get_env_value("FEISHU_APP_SECRET", ""),
            },
        },
        "custom_slack": {
            "display_name": get_env_value("SLACK_DISPLAY_NAME", "slack"),
            "SCOPE": ["identity.basic", "openid", "email", "profile"],
            "APP": {
                "client_id": get_env_value("SLACK_CLIENT_ID", ""),
                "secret": get_env_value("SLACK_CLIENT_SECRET", ""),
            },
        },
        "custom_dingtalk": {
            "display_name": get_env_value("DINGTALK_DISPLAY_NAME", "dingtalk"),
            "SCOPE": ["openid"],
            "APP": {
                "client_id": get_env_value("DINGTALK_APP_KEY", ""),
                "secret": get_env_value("DINGTALK_APP_SECRET", ""),
            },
        },
        "custom_wecom": {
            "display_name": get_env_value("WECOM_DISPLAY_NAME", "wecom"),
            "SCOPE": ["snsapi_privateinfo"],
            "APP": {
                "client_id": get_env_value("WECOM_CORP_ID", ""),
                "secret": get_env_value("WECOM_APP_SECRET", ""),
            },
            "agent_id": get_env_value("WECOM_AGENT_ID", ""),
        },
        "custom_github": {
            "display_name": get_env_value("GITHUB_DISPLAY_NAME", "github"),
            "SCOPE": ["openid"],
            "APP": {
                "client_id": get_env_value("GITHUB_CLIENT_ID", ""),
                "secret": get_env_value("GITHUB_CLIENT_SECRET", ""),
            },
        },
        "custom_gitlab": {
            "display_name": get_env_value("GITLAB_DISPLAY_NAME", "gitlab"),
            "SCOPE": ["read_user"],
            "APP": {
                "client_id": get_env_value("GITLAB_CLIENT_ID", ""),
                "secret": get_env_value("GITLAB_CLIENT_SECRET", ""),
            },
            "GITLAB_URL": get_env_value("GITLAB_URL", "https://gitlab.com")
        }
    }

ACCOUNT_ADAPTER = "user.adapter.AppHubAccountAdapter"
SOCIALACCOUNT_ADAPTER = "user.adapter.AppHubSoialAccountAdapter"
REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "user.serializers.UserSerializer",
    "PASSWORD_CHANGE_SERIALIZER": "user.serializers.UserPasswordChangeSerializer",
    "PASSWORD_RESET_SERIALIZER": "user.serializers.UserPasswordResetSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER": "user.serializers.UserPasswordResetConfirmSerializer",  # noqa: E501
}
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "user.serializers.UserRegisterSerializer"
}
OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE = True
ENABLE_EMAIL_ACCOUNT = get_env_value("ENABLE_EMAIL_ACCOUNT", True)
if ENABLE_EMAIL_ACCOUNT:
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    ACCOUNT_EMAIL_DOMAIN = get_env_value("ACCOUNT_EMAIL_DOMAIN", "")
    ACCOUNT_AUTHENTICATION_METHOD = "username_email"

ACCOUNT_EMAIL_SUBJECT_PREFIX = "[" + get_env_value("APP_NAME", "AppHub") + "]"

ACCOUNT_USERNAME_BLACKLIST = reserved_names
if EXTERNAL_WEB_URL.startswith("https://"):
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
AUTH_USER_MODEL = "user.User"
AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]


SECURE_HSTS_SECONDS = 31536000
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
CSRF_COOKIE_SECURE = True
if EXTERNAL_WEB_URL.startswith("https://") and not DEBUG:
    SECURE_SSL_REDIRECT = True
