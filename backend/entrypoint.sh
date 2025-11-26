#!/bin/bash
APP_PORT=${PORT:-8080}
set -e
set -x
cd /app/
# Activate virtualenv
source /opt/venv/bin/activate

# Wait for DB
# echo "Waiting for Postgres..."
# until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" > /dev/null 2>&1; do
#   sleep 1
# done
# echo "Postgres ready!"

# Run migrations
echo "Running migrations..."
bash /app/migrate.sh


# Use Gunicorn from the Docker venv
/opt/venv/bin/gunicorn --worker-tmp-dir /dev/shm config.wsgi:application --bind "0.0.0.0:${APP_PORT}"
