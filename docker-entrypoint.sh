#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "✅ PostgreSQL is ready!"

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
