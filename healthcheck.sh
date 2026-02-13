#!/bin/bash
LOG="/var/log/latigue-health.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:8000)
if [ "$STATUS" != "200" ] && [ "$STATUS" != "301" ] && [ "$STATUS" != "302" ]; then
echo "$DATE - ALERTE: Site DOWN (HTTP $STATUS)" >> $LOG
docker restart latigue_web
else
echo "$DATE - OK (HTTP $STATUS)" >> $LOG
fi
