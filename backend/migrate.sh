#!/bin/bash
set -e
set -x

cd /app/

# Activate virtualenv
source /opt/venv/bin/activate

# Wait for Postgres
echo "Waiting for Postgres at db:5432..."


echo "Postgres is ready!"
echo "Creating migration files..."
/opt/venv/bin/python manage.py makemigrations --noinput

echo "Running migrations..."
/opt/venv/bin/python manage.py migrate --noinput

# Create superuser if it doesn't exist
/opt/venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model

User = get_user_model()
email = 'admin@gmail.com'
password = 'admin'
first_name = 'Admin'
last_name = 'Admin'

if not User.objects.filter(email=email).exists():
    admin = User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    admin.is_verified = True
    admin.is_active = True
    admin.save()
    print(f'Superuser created & verified: {email}')
else:
    admin = User.objects.get(email=email)
    if not admin.is_verified:
        admin.is_verified = True
        admin.is_active = True
        admin.save()
        print(f'Superuser verified: {email}')
    else:
        print(f'Superuser already exists & verified: {email}')
"
