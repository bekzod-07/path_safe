import os
from pathlib import Path

# Loyihaning asosiy papkasi
BASE_DIR = Path(__file__).resolve().parent.parent

# DIQQAT: Production'da buni o'zgartirish va maxfiy saqlash kerak!
SECRET_KEY = 'django-insecure-n@a&7s9wgq%a6r%tjeh@jbj-i#nbkvwk@huv9j*uus0!7&968b'

# SERVERDA HAR DOIM FALSE QILING
DEBUG = False

# Faqat ruxsat berilgan domenlar
ALLOWED_HOSTS = ['api.kyotosushi.uz', 'www.api.kyotosushi.uz']

# --- HTTPS VA XAVFSIZLIK SOZLAMALARI ---
# cPanel/Ahost/Nginx kabi proxy serverlar orqali HTTPS'ni aniqlash
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    # Barcha HTTP so'rovlarni HTTPS ga majburiy yo'naltirish
    SECURE_SSL_REDIRECT = True
    # Cookie fayllarni faqat xavfsiz ulanish orqali yuborish
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS - Brauzerga faqat HTTPS ishlatishni buyurish
    SECURE_HSTS_SECONDS = 31536000  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Xavfsizlik sarlavhalari
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
else:
    # Lokal rivojlantirish (development) uchun
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Ishonchli manbalar (CSRF xatolarini oldini olish uchun)
CSRF_TRUSTED_ORIGINS = [
    'https://api.kyotosushi.uz',
    'https://www.api.kyotosushi.uz'
]

# Ilovalar
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

# REST Framework sozlamalari: Faqat login qilganlarga ruxsat
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication', 
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Maxsus foydalanuvchi modeli
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

# Ma'lumotlar bazasi
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Parol tekshiruvi
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# Til va vaqt (O'zbekiston)
LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True 

# Statik va Media fayllar
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'