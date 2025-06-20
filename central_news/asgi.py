"""
ASGI config for central_news project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from decouple import config  # <-- Add this line

# Set the Google credentials path securely
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config("GOOGLE_APPLICATION_CREDENTIALS")

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "central_news.settings")

application = get_asgi_application()