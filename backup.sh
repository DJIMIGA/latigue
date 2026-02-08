#!/bin/bash
BACKUP_DIR="/var/backups/latigue"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files (si stockage local)
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Garder seulement les 7 derniers backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
