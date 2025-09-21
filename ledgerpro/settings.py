
import os
from datetime import timedelta
from pathlib import Path
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "5f6e057f0051410011b786af")
PLAID_SECRET = os.getenv("PLAID_SECRET", "7ee040c71df3da41872e0b6883e1c8")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")  # sandbox|development|production
PLAID_REDIRECT_URI = os.getenv("PLAID_REDIRECT_URI","http://localhost:5173/")  # optional
PLAID_WEBHOOK = os.getenv("PLAID_WEBHOOK")            # optional

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
    'finance','users','corsheaders'
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
