import sys
import os

# Add your project directory to the path
project_home = '/home/pmnw/skillswap'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'skillswap.settings'

# Import your WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()