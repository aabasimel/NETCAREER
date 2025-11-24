#!/bin/bash
set -e
cd /app/

# Run migrations only (no superuser creation for Celery)
/opt/venv/bin/python manage.py migrate --noinput

echo "Migrations completed for Celery"