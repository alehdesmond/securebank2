import os
from django.core.wsgi import get_wsgi_application  # ✅ This line is REQUIRED

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SecureBank.settings')

application = get_wsgi_application()

