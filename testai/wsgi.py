"""
WSGI config for test_ai_demo project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testai.settings')
application = get_wsgi_application()
