# Troubleshooting Pipeline CI/CD Elestio - Latigue

## Contexte

Migration de l'ancien deploiement manuel (`/var/www/latigue/`) vers le pipeline CI/CD Elestio (`/opt/app/latigue/`). Ce document recense les problemes rencontres et leurs solutions pour eviter de les revivre.

---

## Fichiers docker-compose (apres nettoyage)

- **`docker-compose.yml`** : utilise par le pipeline Elestio (web + db). Son contenu est ecrase par la config du Dashboard Elestio a chaque build.
- **`docker-compose.dev.yml`** : developpement local avec hot reload (web + db). Usage : `docker compose -f docker-compose.dev.yml up --build`.

Les anciens fichiers `docker-compose.prod.yml` et `docker-compose.external-db.yml` ont ete supprimes (redundants / obsoletes).

---

## Probleme 1 : `.env.production not found`

**Erreur :**
```
env file /opt/app/latigue/.env.production not found
```

**Cause :** Le `docker-compose.yml` referenciait `env_file: .env.production` alors que le pipeline Elestio cree un fichier `.env` (pas `.env.production`).

**Solution :** Remplacer dans `docker-compose.yml` :
```yaml
env_file:
  - .env    # PAS .env.production
```

**Commit :** `afe8b14` - fix: utiliser .env au lieu de .env.production

---

## Probleme 2 : `container_name already in use`

**Erreur :**
```
Error response from daemon: Conflict. The container name "/latigue_web" is already in use
```

**Cause :** Les `container_name` fixes (`latigue_web`, `latigue_db`, etc.) dans le `docker-compose.yml` empechent Docker de recreer les conteneurs lors d'un redeploiement si les anciens existent encore.

**Solution :** Supprimer toutes les directives `container_name` des fichiers docker-compose. Docker Compose gere les noms automatiquement via le nom de projet (ex: `latigue-web-1`).

```yaml
# AVANT (problematique)
services:
  web:
    container_name: latigue_web   # A SUPPRIMER

# APRES (correct)
services:
  web:
    # Pas de container_name, Docker gere automatiquement
```

**Commit :** `63c0d4f` - fix(elestio): supprimer container_name

---

## Probleme 3 : `port 80 address already in use`

**Erreur :**
```
failed to bind host port for 0.0.0.0:80 - address already in use
```

**Cause :** Le `docker-compose.yml` contenait les services `nginx` et `certbot` qui tentaient de se binder sur les ports 80/443. Or, Elestio gere deja le reverse proxy via **OpenResty** (`elestio-nginx`) sur ces ports.

**Solution :** Supprimer les services `nginx` et `certbot` du `docker-compose.yml`. Elestio gere :
- Le reverse proxy (OpenResty sur port 80/443 → proxy vers port 8000)
- Les certificats SSL (Let's Encrypt automatique)
- Les domaines personnalises

**Commit :** `f057411` - fix(elestio): supprimer nginx/certbot et container_name

---

## Probleme 4 : Le pipeline ecrase le `docker-compose.yml`

**Symptome :** Malgre les corrections poussees sur Git, le pipeline continuait d'utiliser l'ancienne version du `docker-compose.yml` (avec nginx, certbot, container_name).

**Cause :** Le pipeline Elestio **ne lit pas le `docker-compose.yml` du repo Git**. Il utilise sa propre copie stockee dans la configuration du service. Lors de chaque build, il :

1. Clone le repo Git
2. **Ecrase** le `docker-compose.yml` avec sa version interne
3. Cree le fichier `.env`
4. Lance `docker compose up`

Les logs du pipeline montrent clairement :
```
Running clone script.
Creating .env file
Creating docker compose file    <-- IL ECRASE NOTRE FICHIER
```

**Solution :** Mettre a jour le `docker-compose.yml` **dans le dashboard Elestio** :

> Elestio Dashboard → Service CI/CD → Docker Compose (ou "Edit docker-compose") → Coller la version correcte → Sauvegarder

Les modifications dans le repo Git ne suffisent PAS pour le docker-compose. Il faut AUSSI mettre a jour la config Elestio.

---

## Probleme 5 : Anciens conteneurs de `/var/www/latigue/`

**Symptome :** Des conteneurs `latigue_web`, `latigue_db`, `latigue_nginx`, `latigue_certbot` tournaient encore depuis l'ancien deploiement manuel dans `/var/www/latigue/`, causant des conflits de ports et de noms.

**Solution :**
```bash
# Arreter et supprimer les anciens conteneurs
cd /var/www/latigue
docker compose down --remove-orphans

# Sauvegarder les fichiers importants
mkdir -p /root/backup_latigue_old
cp .env .env.production latest.dump backup.sh /root/backup_latigue_old/

# Supprimer l'ancien dossier
rm -rf /var/www/latigue
```

**Important :** Les sauvegardes sont dans `/root/backup_latigue_old/`.

---

## Architecture finale sur Elestio

```
Internet
    |
    v
[elestio-nginx] (OpenResty - ports 80/443, SSL automatique)
    |
    v (proxy_pass → port 8000)
[latigue-web-1] (Django + Gunicorn - port 8000)
    |
    v
[latigue-db-1] (PostgreSQL 15 - port 5432)
```

### Services geres par Elestio (NE PAS dupliquer) :
- **Reverse proxy** : `elestio-nginx` (OpenResty)
- **SSL/TLS** : Certificats Let's Encrypt automatiques
- **Postfix** : `elestio-postfix` pour les emails

### Services dans notre `docker-compose.yml` :
- **web** : Django + Gunicorn (port 8000)
- **db** : PostgreSQL 15 (port 5432)

### Services a NE PAS mettre dans le compose Elestio :
- ~~nginx~~ (deja gere par Elestio)
- ~~certbot~~ (deja gere par Elestio)
- ~~container_name~~ (laisser Docker gerer les noms)

---

## docker-compose.yml correct pour Elestio

```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DB_HOST=${DB_HOST:-db}
      - DB_PORT=${DB_PORT:-5432}
      - DB_NAME=${DB_NAME:-postgres}
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD}
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-postgres}
      - DJANGO_DEBUG=${DJANGO_DEBUG:-False}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-latigue.settings}
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app_network

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-postgres}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - app_network
    ports:
      - "5432:5432"

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

---

## Erreur 502 / DisallowedHost

**Symptome :** 502 Bad Gateway ou dans les logs Django :
```
Invalid HTTP_HOST header: '159.195.104.193:8000'. You may need to add '159.195.104.193' to ALLOWED_HOSTS.
```

**Cause :** Une requete arrive avec un Host (IP ou domaine) qui n'est pas dans `ALLOWED_HOSTS`.

**Solution :** Dans **Elestio Dashboard → Environment Variables**, ajouter :
```
ALLOWED_HOSTS_EXTRA=159.195.104.193
```
(valeur = IP ou domaine, plusieurs valeurs separees par des virgules). Pas besoin de modifier le code ni de redepoyer : Elestio reinjecte les variables au demarrage du conteneur.

---

## Checklist pour futurs deploiements

- [ ] Modifier le code et pousser sur `main`
- [ ] Si le `docker-compose.yml` change : **mettre a jour AUSSI dans le dashboard Elestio**
- [ ] Verifier qu'aucun ancien conteneur ne tourne (`docker ps -a | grep latigue`)
- [ ] Ne JAMAIS ajouter `nginx`, `certbot` ou `container_name` dans le compose Elestio
- [ ] Les variables d'environnement se configurent dans **Elestio Dashboard → Environment**
- [ ] Le fichier `.env.production` n'existe plus, tout passe par `.env` (cree par Elestio)

---

## Commandes utiles

```bash
# Voir les conteneurs latigue
docker ps -a --filter "name=latigue"

# Voir les logs de l'app
docker logs latigue-web-1 -f --tail 100

# Voir quel compose a lance un conteneur
docker inspect latigue-web-1 --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'

# Voir les ports en ecoute (pour debug conflits)
ss -tlnp

# Arreter proprement et relancer
cd /opt/app/latigue
docker compose down --remove-orphans
git checkout -- docker-compose.yml   # restaurer depuis Git si ecrase
docker compose up -d --build
```

---

*Derniere mise a jour : 15 fevrier 2026*
