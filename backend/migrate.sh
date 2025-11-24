#!/bin/bash

set -e
set -x

cd /app/

# Migrate
/opt/venv/bin/python manage.py migrate --noinput

# Create superuser
/opt/venv/bin/python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); \
    email='${DJANGO_SUPERUSER_EMAIL}'; password='${DJANGO_SUPERUSER_PASSWORD}'; \
    User.objects.filter(email=email).exists() or User.objects.create_superuser(email=email, password=password)"
