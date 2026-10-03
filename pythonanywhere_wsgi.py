# This file contains the PythonAnywhere WSGI configuration for EthioJobPortal.
# Copy and paste this code into your PythonAnywhere WSGI configuration file:
# /var/www/wubante_pythonanywhere_com_wsgi.py

import os
import sys

# Add project directory to sys.path
path = '/home/wubante/Django-online-Job-Portal-system'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables if needed
os.environ['DJANGO_SETTINGS_MODULE'] = 'jobs.settings'

# Import WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
