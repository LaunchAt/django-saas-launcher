from pathlib import Path

import environ

# Project root

BASE_DIR = Path(__file__).resolve().parent.parent


# environment

AWS_ENV = {
    'AWS_ACCESS_KEY_ID': (str, ''),
    'AWS_CLOUDWATCH_LOG_GROUP_NAME': (str, ''),
    'AWS_REGION_NAME': (str, ''),
    'AWS_S3_BUCKET_NAME': (str, ''),
    'AWS_SECRET_ACCESS_KEY': (str, ''),
}

env = environ.Env(
    DJANGO_CORS_ALLOWED_ORIGINS=(list, []),
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, []),
    DJANGO_DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
    DJANGO_DEBUG=(bool, False),
    DJANGO_LANGUAGE_CODE=(str, 'ja-jp'),
    DJANGO_MEDIA_URL=(str, 'media/'),
    DJANGO_READONLY_DATABASE_URL=(str, ''),
    DJANGO_SECRET_KEY=(str, ''),
    DJANGO_STATIC_URL=(str, 'static/'),
    DJANGO_TIME_ZONE=(str, 'Asia/Tokyo'),
    **AWS_ENV,
)

environ.Env.read_env(BASE_DIR / '.env')


# Core settings

SECRET_KEY = env('DJANGO_SECRET_KEY')

DEBUG = env('DJANGO_DEBUG')

ALLOWED_HOSTS = ['*']


# Application definition

THIRDPARTY_APPS = [
    'corsheaders',
    'django_filters',
    'django_hosts',
    'drf_spectacular',
    'rest_framework',
]

LOCAL_APPS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # sites
    'django.contrib.sitemaps',  # sitemaps
    *THIRDPARTY_APPS,
    *LOCAL_APPS,
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # gzip
    'django_hosts.middleware.HostsRequestMiddleware',  # django_hosts
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # locale
    'corsheaders.middleware.CorsMiddleware',  # corsheaders
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',  # django_hosts
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

DATABASES = {
    'default': env.db('DJANGO_DATABASE_URL'),
    'readonly': env.db(
        'DJANGO_READONLY_DATABASE_URL',
        default=env('DJANGO_DATABASE_URL'),
    ),
}

DATABASE_ROUTERS = ['launcher.backends.routers.ReadAndWriteRouter']


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
        ),
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = env('DJANGO_LANGUAGE_CODE')

TIME_ZONE = env('DJANGO_TIME_ZONE')

USE_TZ = True


# Locale

LOCALE_PATHS = [BASE_DIR / 'locale']


# Static files

STATIC_ROOT = 'static/'

STATIC_URL = env('DJANGO_STATIC_URL')

STATICFILES_STORAGE = 'launcher.backends.storage.AWSS3StaticStorage'


# media files

MEDIA_ROOT = 'media/'

MEDIA_URL = env('DJANGO_MEDIA_URL')

DEFAULT_FILE_STORAGE = 'launcher.backends.storage.AWSS3MediaStorage'


# Django site

SITE_ID = 1


# CSRF

CSRF_TRUSTED_ORIGINS = [*env.list('DJANGO_CSRF_TRUSTED_ORIGINS')]

CSRF_COOKIE_SECURE = True


# HTTPS

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True


# Django Hosts

DEFAULT_HOST = 'default'

ROOT_HOSTCONF = 'config.hosts'


# Django CORS headers

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [*env.list('DJANGO_CORS_ALLOWED_ORIGINS')]


# DRF spectacular

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django SaaS Launcher API v1',
    'DESCRIPTION': (
        'Django SaaS Launcher is a tool that is designed to launch a SaaS system.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# Logging
# launcher.backends.logging.AWSCloudWatchLogHandler
# When using a debug server, the logger may deadlock and not
# operate normally. However, there may be cases where you want to
# verify the behavior during development. In such cases, the best
# way to avoid deadlocks is to set `disable_existing_loggers` to
# `True` in the `LOGGING` configuration.
# See also:
# https://github.com/kislyuk/watchtower#example-django-logging-with-watchtower

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'default': {
            'format': '{asctime} [{levelname}] {pathname}:{lineno}\n{message}',
            'datefmt': '%Y/%m/%d %H:%M:%S',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'cloudwatch': {
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'launcher.backends.logging.AWSCloudWatchHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['cloudwatch', 'console'],
    },
}


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '120/minute',
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': (
        'rest_framework.negotiation.DefaultContentNegotiation'
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# AWS S3

AWS_S3 = {
    'BUCKET_NAME': env('AWS_S3_BUCKET_NAME'),
    'ACCESS_KEY_ID': env('AWS_ACCESS_KEY_ID'),
    'SECRET_ACCESS_KEY': env('AWS_SECRET_ACCESS_KEY'),
    'REGION_NAME': env('AWS_REGION_NAME'),
    'DEVELOPER_MODE': DEBUG,
}


# AWS CloudWatch

AWS_CLOUDWATCH = {
    'LOG_GROUP_NAME': env('AWS_CLOUDWATCH_LOG_GROUP_NAME'),
    'ACCESS_KEY_ID': env('AWS_ACCESS_KEY_ID'),
    'SECRET_ACCESS_KEY': env('AWS_SECRET_ACCESS_KEY'),
    'REGION_NAME': env('AWS_REGION_NAME'),
    'DEVELOPER_MODE': DEBUG,
}
