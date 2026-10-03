#!/bin/bash
# EthioJobPortal PythonAnywhere Deployment & Reload Script

echo "=== Starting EthioJobPortal Deployment ==="

# 1. Navigate to project root
cd /home/wubante/Django-online-Job-Portal-system

# 2. Pull latest code from GitHub
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Pulling latest code from Git..."
    git pull origin master
fi

# 3. Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --run-syncdb

# 4. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 5. Reload PythonAnywhere Web App
echo "Reloading PythonAnywhere Web App..."
touch /var/www/wubante_pythonanywhere_com_wsgi.py

echo "=== Deployment & Reload Complete! ==="
