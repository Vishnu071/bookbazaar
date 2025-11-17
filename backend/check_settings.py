import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","bookbazaar.settings")
import django
django.setup()
from django.conf import settings
print("DEBUG=", settings.DEBUG)
print("STATIC_URL=", repr(settings.STATIC_URL))
print("STATIC_ROOT=", settings.STATIC_ROOT)
print("STATICFILES_DIRS=", settings.STATICFILES_DIRS)
print("INSTALLED_APPS contains staticfiles?", "django.contrib.staticfiles" in settings.INSTALLED_APPS)
