import os, django, django.contrib.admin
os.environ.setdefault("DJANGO_SETTINGS_MODULE","bookbazaar.settings")
django.setup()

# where admin package lives
admin_pkg = django.contrib.admin.__path__[0]
print("admin package path:", admin_pkg)

# expected admin static path to check
expected = os.path.join(admin_pkg, "static", "admin", "css", "base.css")
print("expected admin css path:", expected)
print("exists on filesystem?:", os.path.exists(expected))
