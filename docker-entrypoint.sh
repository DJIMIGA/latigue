#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL to be ready..."
# Attendre max 30 secondes pour PostgreSQL
TIMEOUT=30
ELAPSED=0
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1 || [ $ELAPSED -eq $TIMEOUT ]; do
  sleep 1
  ELAPSED=$((ELAPSED + 1))
  if [ $((ELAPSED % 5)) -eq 0 ]; then
    echo "⏳ Still waiting for PostgreSQL... ($ELAPSED/$TIMEOUT seconds)"
  fi
done

if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; then
  echo "✅ PostgreSQL is ready!"
else
  echo "⚠️  PostgreSQL not ready after ${TIMEOUT}s, continuing anyway..."
  echo "   Django will handle database connection errors"
fi

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🔄 Building Tailwind CSS..."
if [ -f "package.json" ]; then
  if ! command -v npm &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
  fi
  npm install
  npm run build
fi

echo "✅ Starting application..."
exec "$@"
