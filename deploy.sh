#!/bin/bash
# 🚀 Script de déploiement automatique - bolibana.net
# Appelé par le webhook GitHub à chaque push sur main

set -e

PROJECT_DIR="/var/www/latigue"
LOG_FILE="/var/www/latigue/logs/deploy.log"

echo "========================================" >> "$LOG_FILE"
echo "[$(date)] Déploiement déclenché" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# 1. Pull les derniers changements
echo "[$(date)] Git pull..." >> "$LOG_FILE"
git pull origin main >> "$LOG_FILE" 2>&1

# 2. Rebuild et restart les containers
echo "[$(date)] Rebuild containers..." >> "$LOG_FILE"
docker compose build --no-cache web >> "$LOG_FILE" 2>&1
docker compose up -d web >> "$LOG_FILE" 2>&1

# 3. Collecter les fichiers statiques
echo "[$(date)] Collectstatic..." >> "$LOG_FILE"
docker compose exec -T web python manage.py collectstatic --noinput >> "$LOG_FILE" 2>&1

# 4. Migrations si nécessaire
echo "[$(date)] Migrations..." >> "$LOG_FILE"
docker compose exec -T web python manage.py migrate --noinput >> "$LOG_FILE" 2>&1

echo "[$(date)] ✅ Déploiement terminé !" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
