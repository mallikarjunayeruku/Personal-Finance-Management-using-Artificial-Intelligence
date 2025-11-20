
import os
from datetime import timedelta
from pathlib import Path
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import environ, os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

PLAID_CLIENT_ID = env("PLAID_CLIENT_ID")
PLAID_SECRET = env("PLAID_SECRET")
PLAID_ENV = env("PLAID_ENV")  # sandbox|development|production
PLAID_REDIRECT_URI = env("PLAID_REDIRECT_URI")  # optional
PLAID_WEBHOOK = env("PLAID_WEBHOOK")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")

USE_CELERY = env.bool("USE_CELERY", default=True)

def database_from_url(url: str):
    # very small parser to avoid extra deps
    u = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": u.path.lstrip("/"),
        "USER": u.username,
        "PASSWORD": u.password,
        "HOST": u.hostname,
        "PORT": u.port or "5432",
    }

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-unsafe-secret-change-me')
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS','*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','rest_framework.authtoken','django_filters','drf_spectacular',
    'finance','users','corsheaders', 'drf_yasg'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware',
'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'ledgerpro.urls'

TEMPLATES = [{
    'BACKEND':'django.template.backends.django.DjangoTemplates',
    'DIRS':[BASE_DIR/'frontend'],
    'APP_DIRS':True,
    'OPTIONS':{'context_processors':[
        'django.template.context_processors.debug','django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']},
}]

WSGI_APPLICATION = 'ledgerpro.wsgi.application'
DATABASES = {
    "default": database_from_url(os.getenv("DATABASE_URL", "postgresql://arjun:arjun123@localhost:5432/financeai"))
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE='en-us'; TIME_ZONE='UTC'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; STATIC_ROOT=BASE_DIR/'staticfiles'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter','rest_framework.filters.OrderingFilter'],
    'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('ACCESS_MINUTES','60'))),
              'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('REFRESH_DAYS','7'))),
              'AUTH_HEADER_TYPES': ('Bearer',),}

SPECTACULAR_SETTINGS = {'TITLE':'LedgerPro API','DESCRIPTION':'REST API mirroring the provided GraphQL schema','VERSION':'1.0.0','SERVE_INCLUDE_SCHEMA':False}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
}