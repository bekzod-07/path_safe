import os
from pathlib import Path

# Loyihaning asosiy papkasi
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-n@a&7s9wgq%a6r%tjeh@jbj-i#nbkvwk@huv9j*uus0!7&968b'

# Serverda ishlayotganda DEBUG=True bo'lishi xatolarni ko'rishga yordam beradi, 
# lekin hamma narsa tayyor bo'lgach False qilish kerak.
DEBUG = True

ALLOWED_HOSTS = ['api.kyotosushi.uz', 'www.api.kyotosushi.uz', '127.0.0.1', 'localhost']

# Swagger va API so'rovlari uchun CSRF ishonchli domenlar
CSRF_TRUSTED_ORIGINS = ['https://api.kyotosushi.uz', 'http://api.kyotosushi.uz']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Kutubxonalar
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    
    # Loyiha ilovalari
    'accounts',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database (SQLite serverda 'db.sqlite3' faylida saqlanadi)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Parol tekshiruvi
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Vaqt va til sozlamalari (O'zbekiston vaqti bilan)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Statik fayllar (CSS, JS, Images) - Ahost/cPanel uchun eng muhim qismi
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'