# Guide de Deploiement Django sur VPS Elestio (avec OpenResty)

Ce document retrace toutes les etapes realisees pour deployer le projet **Latigue** (Django) sur un VPS Elestio partage, en utilisant Docker et le reverse proxy OpenResty integre d'Elestio.

---

## Contexte

- **VPS Elestio** : `latigue-u67346.vm.elestio.app` (IP: `159.195.104.193`)
- **PostgreSQL Elestio** : `postgres-u67346.vm.elestio.app:25432`
- **Autre projet sur le meme VPS** : `openclaw` (port 18789)
- **Reverse proxy** : OpenResty (gere par Elestio, ports 80/443, SSL automatique)

---

## Architecture Finale

```
Internet
   |
   v
OpenResty (Elestio) - ports 80/443, SSL automatique
   |
   v (proxy_pass vers port 8000)
Docker: latigue_web (Gunicorn + Django)
   |
   v
PostgreSQL Elestio (externe, port 25432)
```

> **Important** : On n'utilise PAS notre propre Nginx ni Certbot car OpenResty d'Elestio gere deja le SSL et le reverse proxy.

---

## Etape 1 : Preparation du VPS

### 1.1 Connexion SSH

```bash
ssh root@159.195.104.193
```

### 1.2 Cloner le projet

```bash
mkdir -p /var/www/latigue
cd /var/www/latigue
git clone https://github.com/<USERNAME>/latigue.git .
```

### 1.3 Creer les repertoires necessaires

```bash
cd /var/www/latigue
mkdir -p nginx/conf.d certbot/conf certbot/www logs staticfiles media
chmod -R 755 staticfiles media logs
```

---

## Etape 2 : Choisir le bon docker-compose

Le projet contient deux fichiers docker-compose :
- `docker-compose.yml` : avec PostgreSQL local + Nginx + Certbot
- `docker-compose.yml` : web + db (Nginx/SSL gérés par Elestio)

**On utilise ni l'un ni l'autre tel quel.** Puisque Elestio gere le proxy et qu'on a PostgreSQL externe, le `docker-compose.yml` final est **minimal** :

```yaml
services:
  web:
    build: .
    container_name: latigue_web
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./media:/app/media
      - ./logs:/app/logs
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

### Pourquoi ce choix ?

| Element | Raison du retrait |
|---------|-------------------|
| Service `db` | PostgreSQL est externe sur Elestio (port 25432) |
| Service `nginx` | OpenResty d'Elestio gere deja les ports 80/443 |
| Service `certbot` | OpenResty gere le SSL automatiquement |
| Bloc `environment` | Redondant avec `env_file`, et cause des warnings |
| `version: '3.8'` | Obsolete dans les versions recentes de Docker Compose |

### Commande pour creer le fichier

```bash
printf 'services:\n  web:\n    build: .\n    container_name: latigue_web\n    restart: unless-stopped\n    ports:\n      - "8000:8000"\n    env_file:\n      - .env.production\n    volumes:\n      - ./staticfiles:/app/staticfiles\n      - ./media:/app/media\n      - ./logs:/app/logs\n    networks:\n      - app_network\n\nnetworks:\n  app_network:\n    driver: bridge\n' > docker-compose.yml
```

---

## Etape 3 : Creer le fichier .env.production

```bash
nano .env.production
```

Contenu :

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY='VOTRE_SECRET_KEY_ICI'
DJANGO_SETTINGS_MODULE=latigue.settings
DB_HOST=postgres-u67346.vm.elestio.app
DB_PORT=25432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=VOTRE_MOT_DE_PASSE
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@postgres-u67346.vm.elestio.app:25432/postgres
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_app
CONTACT_EMAIL=votre@email.com
DEFAULT_FROM_EMAIL=votre@email.com
AWS_ACCESS_KEY_ID=VOTRE_AWS_KEY
AWS_SECRET_ACCESS_KEY=VOTRE_AWS_SECRET
AWS_STORAGE_BUCKET_NAME=personalporfolio
AWS_S3_REGION_NAME=eu-north-1
AWS_S3_CUSTOM_DOMAIN=d3tcb6ounmojtn.cloudfront.net
USE_S3_STORAGE=True
```

### Pieges a eviter

| Piege | Solution |
|-------|----------|
| Espaces en debut de ligne | **Aucun espace** avant les noms de variables |
| SECRET_KEY avec `$` ou `(` | Entourer la valeur avec des **guillemets simples** `'...'` |
| Port PostgreSQL | Elestio utilise le port **25432** (pas 5432) |

### Securiser le fichier

```bash
chmod 600 .env.production
```

---

## Etape 4 : Corriger le Dockerfile

L'image `python:3.9.4-slim` est basee sur Debian Buster (obsolete, repos supprimes).

```bash
sed -i 's/FROM python:3.9.4-slim/FROM python:3.9-slim/' Dockerfile
```

**Avant** : `FROM python:3.9.4-slim` (Buster - ERREUR)
**Apres** : `FROM python:3.9-slim` (Bookworm - OK)

---

## Etape 5 : Build et lancement

```bash
docker compose build
docker compose up -d
```

### Verification

```bash
docker compose ps
# latigue_web doit etre "Up"

docker compose logs web | tail -20
# Doit afficher :
# - ✅ PostgreSQL is ready!
# - 🔄 Running migrations...
# - 🔄 Collecting static files...
# - ✅ Starting application...
# - [INFO] Listening at: http://0.0.0.0:8000
```

---

## Etape 6 : Appliquer les migrations manquantes

Si des tables n'existent pas (erreur `relation "xxx" does not exist`) :

```bash
docker compose exec web python manage.py makemigrations portfolio blog services formations
docker compose exec web python manage.py migrate
```

Verification :

```bash
docker compose exec web python manage.py showmigrations
# Toutes les migrations doivent etre [X]
```

---

## Etape 7 : Configurer OpenResty (reverse proxy Elestio)

C'est l'etape **critique**. OpenResty d'Elestio ecoute sur les ports 80/443 et doit router le trafic vers le port 8000 de Django.

### 7.1 Creer la config Nginx pour latigue

```bash
nano /opt/elestio/nginx/conf.d/latigue.conf
```

Contenu :

```nginx
map $http_upgrade $connection_upgrade_latigue {
  default upgrade;
  '' close;
}

proxy_cache_path /tmp/latigue levels=1:2 keys_zone=latigue:10m max_size=1g inactive=60m use_temp_path=off;
limit_req_zone $binary_remote_addr$http_x_forwarded_for zone=latiguee:16m rate=1000000r/m;

server {
  listen 443 ssl;
  http2 on;
  ssl_certificate /etc/nginx/certs/cert.pem;
  ssl_certificate_key /etc/nginx/certs/key.pem;
  server_name latigue-u67346.vm.elestio.app bolibana.net www.bolibana.net;

  client_header_buffer_size 32k;
  large_client_header_buffers 4 64k;
  underscores_in_headers on;

  location / {
    limit_req zone=latiguee burst=1000000 nodelay;

    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
    proxy_connect_timeout 180s;
    keepalive_timeout 180s;

    proxy_http_version 1.1;
    proxy_pass http://172.17.0.1:8000/;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade_latigue;
  }
}
```

> **Note** : `proxy_pass` pointe vers `172.17.0.1:8000` (bridge Docker du host). Le header `X-Forwarded-Proto` est transmis pour que Django sache que la requete arrive en HTTPS (evite la boucle de redirection).

### 7.2 Ajouter le domaine dans le .env d'Elestio

```bash
nano /opt/elestio/nginx/.env
```

Ajouter le domaine a `ALLOWED_DOMAINS` :

```
ALLOWED_DOMAINS=openclaw-u67346.vm.elestio.app|postgres-u67346.vm.elestio.app|latigue-u67346.vm.elestio.app|bolibana.net|www.bolibana.net
```

### 7.3 Redemarrer OpenResty

```bash
cd /opt/elestio/nginx && docker compose restart
```

---

## Etape 8 : Ajouter le hostname dans ALLOWED_HOSTS de Django

Le `settings.py` doit inclure le hostname du VPS :

```bash
sed -i "s/'postgres-u67346.vm.elestio.app',/'postgres-u67346.vm.elestio.app','latigue-u67346.vm.elestio.app',/" /var/www/latigue/latigue/settings.py
```

Puis rebuild :

```bash
cd /var/www/latigue
docker compose down
docker compose build
docker compose up -d
```

### Verification

```bash
docker compose exec web python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','latigue.settings')
django.setup()
from django.conf import settings
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
"
# Doit contenir 'latigue-u67346.vm.elestio.app'
```

---

## Etape 9 : Tests

### Test en ligne de commande

```bash
# Test sans SSL (depuis le VPS)
curl -I -H "X-Forwarded-Proto: https" http://localhost:8000
# Attendu : HTTP/1.1 200 OK

# Test via le proxy
curl -I https://latigue-u67346.vm.elestio.app
# Attendu : HTTP/2 200
```

### Test navigateur

- Page d'accueil : https://latigue-u67346.vm.elestio.app/
- Admin Django : https://latigue-u67346.vm.elestio.app/admin/

### Creer un superutilisateur

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Problemes rencontres et solutions

### 1. `apt-get update` echoue dans Docker (Debian Buster)

**Erreur** : `The repository 'http://deb.debian.org/debian buster Release' does not have a Release file`

**Cause** : `python:3.9.4-slim` utilise Debian Buster (EOL, repos supprimes)

**Solution** : Utiliser `python:3.9-slim` (sans version patch)

---

### 2. Variables d'environnement non lues (warnings DB_HOST not set)

**Erreur** : `WARN The "DB_HOST" variable is not set. Defaulting to a blank string.`

**Cause** : Le bloc `environment` dans `docker-compose.yml` utilise `${DB_HOST}` qui est evalue au niveau du **shell host**, pas depuis `.env.production`

**Solution** : Supprimer le bloc `environment` et garder uniquement `env_file`. Les variables sont chargees directement dans le conteneur.

---

### 3. Variable "buhd" not set

**Erreur** : `WARN The "buhd" variable is not set`

**Cause** : La SECRET_KEY contient `$buhd` qui est interprete comme une variable shell

**Solution** : Entourer la SECRET_KEY de guillemets simples dans `.env.production` :
```
DJANGO_SECRET_KEY='84(-9azqu=@n*cr!$buhd-jalv%*(j-mdsql*b6b*bz0g%cd8t'
```

---

### 4. Port 80 deja utilise

**Erreur** : `failed to bind host port for 0.0.0.0:80 - address already in use`

**Cause** : OpenResty d'Elestio utilise deja les ports 80 et 443

**Solution** : Ne pas lancer notre propre Nginx. Utiliser OpenResty comme reverse proxy vers le port 8000.

---

### 5. DisallowedHost

**Erreur** : `Invalid HTTP_HOST header: 'latigue-u67346.vm.elestio.app'. You may need to add it to ALLOWED_HOSTS.`

**Cause** : Le hostname du VPS n'etait pas dans `ALLOWED_HOSTS` de Django

**Solution** : Ajouter `'latigue-u67346.vm.elestio.app'` dans la liste `ALLOWED_HOSTS` du `settings.py`

---

### 6. Tables inexistantes (relation does not exist)

**Erreur** : `django.db.utils.ProgrammingError: relation "portfolio_profile" does not exist`

**Cause** : Les migrations n'avaient pas ete appliquees sur la base Elestio

**Solution** :
```bash
docker compose exec web python manage.py makemigrations portfolio blog services formations
docker compose exec web python manage.py migrate
```

---

### 7. Espaces dans .env.production

**Erreur** : Les variables ne sont pas lues par Docker

**Cause** : Des espaces au debut des lignes dans le fichier `.env.production`

**Solution** : Aucun espace en debut de ligne. Chaque ligne doit commencer directement par `NOM_VARIABLE=valeur`

---

## Bonnes pratiques et reflexes VPS

### Creer des fichiers sur le VPS : utiliser `tee` au lieu de `nano`

`nano` pose souvent des problemes :
- Les lignes longues sont coupees automatiquement (word wrap)
- Le copier-coller peut ajouter des espaces ou casser l'indentation
- On colle parfois les instructions avec le contenu du fichier

**Methode fiable avec `tee` et heredoc** :

```bash
tee /chemin/du/fichier << 'ENDOFSCRIPT'
contenu du fichier ici
ENDOFSCRIPT
```

> Les guillemets simples autour de `'ENDOFSCRIPT'` empechent l'interpretation des variables `$` dans le contenu. Sans guillemets, `$DATE` serait evalue immediatement.

### Executer les commandes une par une

Ne jamais coller plusieurs commandes d'un coup. Le terminal peut les fusionner et creer des erreurs.

**Mauvais** : coller 3 commandes en meme temps
**Bon** : coller une commande, appuyer sur Entree, attendre le resultat, puis passer a la suivante

### Fichiers .env : pas d'espaces en debut de ligne

Docker ne supporte pas les espaces avant les noms de variables :

```
# MAUVAIS (espace au debut)
  DB_HOST=localhost

# BON
DB_HOST=localhost
```

### Variables avec caracteres speciaux

Si une valeur contient `$`, `(`, `)`, `!`, `%`, entourer de guillemets simples :

```
# MAUVAIS - $buhd est interprete comme une variable
DJANGO_SECRET_KEY=84(-9azqu=@n*cr!$buhd

# BON
DJANGO_SECRET_KEY='84(-9azqu=@n*cr!$buhd'
```

### Verifier un fichier apres edition

Toujours verifier le contenu apres avoir edite :

```bash
cat /chemin/du/fichier
```

### Docker Compose : pas de bloc `environment` avec `env_file`

Si on utilise `env_file`, le bloc `environment` avec `${VAR}` est redondant et cause des warnings car Docker cherche les variables dans le shell host :

```yaml
# MAUVAIS - double declaration
env_file:
  - .env.production
environment:
  - DB_HOST=${DB_HOST}  # cherche dans le shell, pas dans .env.production

# BON - env_file suffit
env_file:
  - .env.production
```

---

## Commandes utiles

```bash
# Voir les logs
cd /var/www/latigue && docker compose logs -f web

# Redemarrer l'app
docker compose restart

# Rebuild complet
docker compose down && docker compose build && docker compose up -d

# Entrer dans le conteneur
docker compose exec web bash

# Lancer les migrations
docker compose exec web python manage.py migrate

# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput

# Creer un superutilisateur
docker compose exec web python manage.py createsuperuser

# Redemarrer OpenResty (proxy Elestio)
cd /opt/elestio/nginx && docker compose restart
```

---

## Fichiers importants sur le VPS

| Fichier | Emplacement |
|---------|-------------|
| Code Django | `/var/www/latigue/` |
| docker-compose.yml | `/var/www/latigue/docker-compose.yml` |
| Variables d'env | `/var/www/latigue/.env.production` |
| Config OpenResty latigue | `/opt/elestio/nginx/conf.d/latigue.conf` |
| Domaines autorises Elestio | `/opt/elestio/nginx/.env` |
| Logs Nginx Elestio | `/opt/elestio/nginx/logs/` |

---

## Prochaines etapes

- [x] Configurer le domaine custom `bolibana.net`
- [x] Migrer les donnees depuis Heroku (`pg_dump` / `pg_restore`)
- [x] Configurer les backups automatiques
- [x] Monitoring et alertes

---

## Etape 10 : Migration des donnees Heroku

### 10.1 Exporter la base Heroku (depuis la machine locale)

```bash
heroku pg:backups:capture --app latigue-9570ef49bb0e
heroku pg:backups:download --app latigue-9570ef49bb0e
```

### 10.2 Envoyer le dump sur le VPS

```bash
scp latest.dump root@159.195.104.193:/var/www/latigue/
```

### 10.3 Restaurer dans PostgreSQL Elestio

`pg_restore` n'est pas installe sur le VPS, on utilise le conteneur Docker :

```bash
# Copier le dump dans le conteneur
docker cp /var/www/latigue/latest.dump latigue_web:/app/latest.dump

# Restaurer
docker exec -e PGPASSWORD=VOTRE_MOT_DE_PASSE latigue_web pg_restore --verbose --clean --no-acl --no-owner -h postgres-u67346.vm.elestio.app -p 25432 -U postgres -d postgres /app/latest.dump
```

> **Note** : Les erreurs `transaction_timeout` et `pg_stat_statements` sont normales (differences de version PostgreSQL). Les donnees sont bien importees.

### 10.4 Redemarrer Django

```bash
cd /var/www/latigue && docker compose restart
```

---

## Etape 11 : Configurer le domaine bolibana.net

### 11.1 DNS chez Gandi

Référence des enregistrements DNS (valeurs par défaut Gandi ; pour Latigue, modifier uniquement **A** et **CNAME www** comme indiqué ci-dessous) :

| Nom | Type | TTL | Valeur |
|-----|------|-----|--------|
| @ | A | 10800 | 217.70.184.38 |
| @ | MX | 10800 | 10 spool.mail.gandi.net. |
| @ | MX | 10800 | 50 fb.mail.gandi.net. |
| @ | TXT | 10800 | "v=spf1 include:_mailcust.gandi.net ?all" |
| @ | TXT | 10800 | "google-site-verification=7lliWyH2WrbnUHOrTUGBLqLDuMyQa5Fei79eFA_TXMk" |
| _imap._tcp | SRV | 10800 | 0 0 0 . |
| _imaps._tcp | SRV | 10800 | 0 1 993 mail.gandi.net. |
| _pop3._tcp | SRV | 10800 | 0 0 0 . |
| _pop3s._tcp | SRV | 10800 | 10 1 995 mail.gandi.net. |
| _submission._tcp | SRV | 10800 | 0 1 465 mail.gandi.net. |
| gm1._domainkey | CNAME | 10800 | gm1.gandimail.net. |
| gm2._domainkey | CNAME | 10800 | gm2.gandimail.net. |
| gm3._domainkey | CNAME | 10800 | gm3.gandimail.net. |
| webmail | CNAME | 10800 | webmail.gandi.net. |
| www | CNAME | 10800 | webredir.vip.gandi.net. |

Pour pointer le site Latigue vers Elestio, modifier **uniquement** :
- **A** `@` → `159.195.104.193` (IP du VPS Elestio)
- **CNAME** `www` → `latigue-u67346.vm.elestio.app.`

> **Ne pas toucher** aux enregistrements MX, TXT, SRV et _domainkey (config email et vérification Google Gandi).

### 11.2 Ajouter les domaines dans OpenResty

Modifier `/opt/elestio/nginx/conf.d/latigue.conf` :

```nginx
server_name latigue-u67346.vm.elestio.app bolibana.net www.bolibana.net;
```

Modifier `/opt/elestio/nginx/.env` :

```
ALLOWED_DOMAINS=openclaw-u67346.vm.elestio.app|postgres-u67346.vm.elestio.app|latigue-u67346.vm.elestio.app|bolibana.net|www.bolibana.net
```

Redemarrer OpenResty :

```bash
cd /opt/elestio/nginx && docker compose restart
```

### 11.3 Django ALLOWED_HOSTS

`bolibana.net` et `www.bolibana.net` sont deja dans le `settings.py`, pas de modification necessaire.

### 11.4 Verification

```bash
# Attendre la propagation DNS (peut prendre jusqu'a 48h, souvent 15-30 min)
dig bolibana.net +short
# Doit retourner : 159.195.104.193

# Test
curl -I https://bolibana.net
curl -I https://www.bolibana.net
```

URLs finales :
- https://bolibana.net
- https://www.bolibana.net
- https://bolibana.net/admin/

---

## Etape 12 : Backups automatiques

### 12.1 Script de backup

Le script `/var/www/latigue/backup.sh` sauvegarde la base de donnees et les fichiers media :

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/latigue"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker exec -e PGPASSWORD=VOTRE_MOT_DE_PASSE latigue_web pg_dump -h postgres-u67346.vm.elestio.app -p 25432 -U postgres postgres | gzip > $BACKUP_DIR/db_$DATE.sql.gz
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /var/www/latigue media/
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete
echo "Backup completed: $DATE"
```

> **Piege** : La ligne `docker exec ... pg_dump` doit etre sur **une seule ligne**. Si elle est coupee dans nano, la commande echoue.

### 12.2 Creer le script avec `tee` (methode fiable)

```bash
tee /var/www/latigue/backup.sh << 'ENDOFSCRIPT'
#!/bin/bash
BACKUP_DIR="/var/backups/latigue"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker exec -e PGPASSWORD=VOTRE_MOT_DE_PASSE latigue_web pg_dump -h postgres-u67346.vm.elestio.app -p 25432 -U postgres postgres | gzip > $BACKUP_DIR/db_$DATE.sql.gz
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /var/www/latigue media/
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete
echo "Backup completed: $DATE"
ENDOFSCRIPT
chmod +x /var/www/latigue/backup.sh
```

### 12.3 Test manuel

```bash
bash /var/www/latigue/backup.sh
ls -lh /var/backups/latigue/
# Attendu : db_YYYYMMDD_HHMMSS.sql.gz (~28K) + media_YYYYMMDD_HHMMSS.tar.gz (~37M)
```

### 12.4 Cron (backup chaque nuit a 2h)

```bash
(crontab -l; echo "0 2 * * * /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1") | crontab -
crontab -l  # Verifier
```

### 12.5 Methode fiable : copier le script depuis la machine locale

Quand les heredocs et echo posent probleme, utiliser `scp` :

```bash
# Creer le fichier en local, puis le copier sur le VPS
scp healthcheck.sh root@159.195.104.193:/var/www/latigue/healthcheck.sh
ssh root@159.195.104.193 "chmod +x /var/www/latigue/healthcheck.sh"
```

### 12.6 Restauration d'un backup

```bash
# Restaurer la base
gunzip -c /var/backups/latigue/db_YYYYMMDD_HHMMSS.sql.gz | docker exec -i -e PGPASSWORD=VOTRE_MOT_DE_PASSE latigue_web psql -h postgres-u67346.vm.elestio.app -p 25432 -U postgres postgres

# Restaurer les media
tar -xzf /var/backups/latigue/media_YYYYMMDD_HHMMSS.tar.gz -C /var/www/latigue/
```

---

## Etape 13 : Monitoring et healthcheck

### 13.1 Aliases utiles

Deja configures dans `~/.bashrc` :

```bash
alias latilog='cd /var/www/latigue && docker compose logs -f web'
alias latips='cd /var/www/latigue && docker compose ps'
```

### 13.2 Script de healthcheck

Le script `/var/www/latigue/healthcheck.sh` verifie toutes les 5 minutes que le site repond. Si le site est DOWN, il redemarre automatiquement le conteneur.

```bash
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
```

> **Note** : On teste `http://localhost:8000` (pas HTTPS) car depuis le VPS, curl ne peut pas verifier le certificat SSL d'OpenResty. HTTP 301 est normal (Django redirige vers HTTPS).

### 13.3 Cron healthcheck (toutes les 5 minutes)

```bash
(crontab -l; echo "*/5 * * * * /var/www/latigue/healthcheck.sh") | crontab -
```

### 13.4 Consulter les logs

```bash
# Logs du healthcheck
cat /var/log/latigue-health.log

# Logs Django en temps reel
latilog

# Etat des conteneurs
latips
```

### 13.5 Resume des crons configures

```
0 2 * * *   /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1
*/5 * * * * /var/www/latigue/healthcheck.sh
```
