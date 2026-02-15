#!/bin/bash
# Ne pas utiliser set -e : on veut toujours lancer Gunicorn même si une étape échoue (éviter 502)
set +e

echo "🔄 Waiting for PostgreSQL to be ready..."
TIMEOUT=30
ELAPSED=0
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1 || [ $ELAPSED -eq $TIMEOUT ]; do
  sleep 1
  ELAPSED=$((ELAPSED + 1))
  if [ $((ELAPSED % 5)) -eq 0 ]; then
    echo "⏳ Still waiting for PostgreSQL... ($ELAPSED/$TIMEOUT seconds)"
  fi
done

if pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1; then
  echo "✅ PostgreSQL is ready!"
else
  echo "⚠️  PostgreSQL not ready after ${TIMEOUT}s, continuing anyway..."
fi

echo "🔄 Running migrations..."
python manage.py migrate --noinput || echo "⚠️  Migrations failed, continuing (check DB env vars)"

echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "⚠️  collectstatic failed, continuing"

# Tailwind/npm : non bloquant pour éviter 502 si build front échoue (Gunicorn démarre quand même)
echo "🔄 Building Tailwind CSS (optional)..."
if [ -f "package.json" ]; then
  if command -v npm &> /dev/null; then
    npm install && npm run build || echo "⚠️  npm build failed, continuing without Tailwind assets"
  else
    echo "⚠️  npm not found, skipping Tailwind build"
  fi
fi

echo "✅ Starting application..."
exec "$@"
