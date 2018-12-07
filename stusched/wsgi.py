"""
WSGI config for stusched project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os, sys
import django
from django.core.wsgi import get_wsgi_application

sys.path.insert(0, '/var/www/stusched/stusched')
sys.path.insert(0, '/var/www/stusched')

pairs = (("DJANGO_SETTINGS_MODULE", "stusched.settings"),
         ('DJANGO_DEBUG', 'True'),
         ('APP_PATH', '/apps/sis'),
         ('STATIC_PATH', '/apps/static'),
         ('DJANGO_SECRET_KEY', 'change'),
         )
for pair in pairs:
    os.environ.setdefault(pair[0], pair[1])

django.setup(set_prefix=True)

application = get_wsgi_application()
