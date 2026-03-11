import os
import sys

# Loyihangiz joylashgan yo'lni ko'rsatish
sys.path.insert(0, os.path.dirname(__file__))

# Django sozlamalari (Loyiha nomini 'core' deb faraz qilamiz)
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Django applicationni ishga tushirish
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()