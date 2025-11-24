#!/bin/bash
set -e
set -x
cd /app/

# Activate virtualenv
source /opt/venv/bin/activate

# Wait for DB
echo "Waiting for Postgres..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres ready!"

# Run migrations
echo "Running migrations..."
bash /app/migrate-celery.sh  

# Start Celery
echo "Starting Celery worker..."
exec /opt/venv/bin/celery -A product_order_api worker --loglevel=info