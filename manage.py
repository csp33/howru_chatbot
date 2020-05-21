#!/usr/bin/env python
import json
import sys

import django

ROUTES_FILE_PATH = '/etc/howru/cfg/routes.json'
with open(ROUTES_FILE_PATH) as routes_file:
    json_file = json.load(routes_file)
    NAME = json_file['name']
    USER = json_file['user']
    PWD = json_file['password']
    HOST = json_file['host']
    PORT = json_file['port']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': NAME,
        'USER': USER,
        'PASSWORD': PWD,
        'HOST': HOST,
        'PORT': PORT,
    }
}

INSTALLED_APPS = [
    'howru_models',
    'django.contrib.contenttypes',
    'django.contrib.auth'
]
from django.conf import settings

settings.configure(
    DATABASES=DATABASES,
    INSTALLED_APPS=INSTALLED_APPS,
    USE_TZ=True
)
django.setup()
if __name__ == "__main__":
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
