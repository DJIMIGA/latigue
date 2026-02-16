# 🚀 Configuration CI/CD Elestio pour Latigue

Ce guide explique comment configurer le déploiement automatique sur Elestio.

## 📋 Prérequis

- [ ] Repo Git sur Github/Gitlab
- [ ] Service PostgreSQL Elestio déjà créé
- [ ] Les credentials/secrets à portée de main

---

## 🔧 Configuration sur Elestio

### Étape 1 : Créer le service CI/CD

1. **Dans l'interface Elestio** → "Create CI/CD pipeline"
2. **Choisir la méthode** :
   - ✅ **Github** (recommandé pour auto-déploiement)
   - OU Docker Compose (upload manuel)

### Étape 2 : Configuration Github CI/CD

Si vous choisissez **Github** :

1. **Source** :
   - Repository : `votre-username/latigue`
   - Branch : `main`
   - Path to docker-compose : `docker-compose.yml`

2. **Target** :
   - Region : Choisissez votre région (ex: eu-central)
   - VPS Size : Au moins 2GB RAM recommandé

3. **Configuration** :
   - Service name : `latigue`
   - Ports : `8000` (HTTP)

### Étape 3 : Définir les variables d'environnement

Dans l'interface Elestio, section **Environment Variables**, ajoutez :

```bash
# Django Core
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=votre_secret_key_ici
DJANGO_SETTINGS_MODULE=latigue.settings
# Optionnel : hôtes supplémentaires (évite 502 si accès par IP ou autre domaine)
# ALLOWED_HOSTS_EXTRA=159.195.104.193,autre-domaine.com

# Database (votre PostgreSQL Elestio existant)
DB_HOST=postgres-u67346.vm.elestio.app
DB_PORT=25432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe_postgresql

# Email
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre_app_password
CONTACT_EMAIL=contact@bolibana.net
DEFAULT_FROM_EMAIL=noreply@bolibana.net

# AWS S3
AWS_ACCESS_KEY_ID=votre_access_key
AWS_SECRET_ACCESS_KEY=votre_secret_key
AWS_STORAGE_BUCKET_NAME=personalporfolio
AWS_S3_REGION_NAME=eu-north-1
AWS_S3_CUSTOM_DOMAIN=d3tcb6ounmojtn.cloudfront.net
USE_S3_STORAGE=True

# Cloudinary (si utilisé)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret
```

### Étape 4 : Configuration OpenResty (Reverse Proxy)

Elestio va créer automatiquement le reverse proxy. Vérifiez la configuration :

**Fichier** : `/opt/elestio/nginx/conf.d/latigue.conf`

```nginx
server {
  listen 443 ssl http2;
  ssl_certificate /etc/nginx/certs/cert.pem;
  ssl_certificate_key /etc/nginx/certs/key.pem;
  server_name votre-domaine.vm.elestio.app bolibana.net www.bolibana.net;

  location / {
    proxy_pass http://172.17.0.1:8000/;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### Étape 5 : Domaine personnalisé

1. **DNS (chez Gandi)** — pour Latigue :
   - **A** `@` → `159.195.104.193` (IP du VPS Elestio)
   - **CNAME** `www` → `latigue-u67346.vm.elestio.app.`
   - Ne pas modifier : MX, TXT, SRV, _domainkey, webmail (config email Gandi).
   - Référence complète : voir `DEPLOIEMENT_VPS_ELESTIO.md` § 11.1.

2. **Dans Elestio** → Settings → Custom Domain :
   - Ajoutez `bolibana.net` et `www.bolibana.net`
   - Elestio générera automatiquement les certificats SSL

---

## 🔄 Workflow de déploiement

Une fois configuré, le workflow devient simple :

```bash
# Sur votre machine locale
git add .
git commit -m "Nouvelle fonctionnalité"
git push origin main

# Elestio automatiquement :
# ✅ Détecte le push
# ✅ Clone le repo
# ✅ Build l'image Docker
# ✅ Lance docker-compose.yml (contenu pris depuis la config Elestio Dashboard)
# ✅ Vérifie le healthcheck
# ✅ Bascule le trafic (zero-downtime)
# ✅ Rollback automatique si échec
```

---

## 🧪 Tests après déploiement

### 1. Vérifier les logs
```bash
# Dans l'interface Elestio → Logs
# OU via SSH :
ssh root@votre-ip
docker logs latigue_web -f
```

### 2. Tester l'application
```bash
curl -I https://bolibana.net
# Attendu : HTTP/2 200
```

### 3. Vérifier le healthcheck
```bash
docker inspect latigue_web | grep -A 10 Health
```

---

## 📦 Backups automatiques

### Option 1 : Backup Elestio (recommandé)

Elestio propose des backups automatiques :
- Interface Elestio → Settings → Backups
- Fréquence : Quotidien recommandé
- Rétention : 7 jours

### Option 2 : Script custom (si besoin)

Le script `backup.sh` est déjà prêt (credentials sécurisés) :

```bash
# SSH sur le VPS
ssh root@votre-ip

# Rendre le script exécutable
chmod +x /root/backup.sh

# Tester
./backup.sh

# Cron quotidien (2h du matin)
crontab -e
# Ajouter :
0 2 * * * /root/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🔧 Migration depuis votre setup actuel

### 1. Sauvegarder la configuration actuelle
```bash
ssh root@159.195.104.193
cd /var/www/latigue

# Sauvegarder .env.production
cp .env.production ~/.env.production.backup

# Backup de la base
docker exec latigue_web bash -c 'pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME' > backup_avant_migration.sql
```

### 2. Arrêter l'ancien setup
```bash
cd /var/www/latigue
docker compose down
```

### 3. Configurer le nouveau service Elestio (voir étapes ci-dessus)

### 4. Vérifier que tout fonctionne
```bash
# Tester le site
curl -I https://bolibana.net

# Vérifier les logs
# Via interface Elestio ou SSH
```

### 5. Nettoyer l'ancien (optionnel)
```bash
# Une fois que tout fonctionne avec le CI/CD
# Vous pouvez supprimer /var/www/latigue si vous voulez
# MAIS gardez les backups !
```

---

## 📊 Monitoring

### Healthcheck automatique
Le healthcheck Docker vérifie toutes les 30s que l'app répond.
En cas d'échec, le conteneur redémarre automatiquement.

### Logs
- **Interface Elestio** : Logs en temps réel
- **SSH** : `docker logs latigue_web -f`
- **Fichiers** : `/app/logs/` dans le conteneur

---

## 🆘 Troubleshooting

### Le build échoue
```bash
# Vérifier les logs de build dans Elestio UI
# Problèmes fréquents :
# - requirements.txt manquant une dépendance
# - Variables d'environnement manquantes
```

### L'app ne démarre pas
```bash
ssh root@votre-ip
docker logs latigue_web --tail 100

# Vérifier les variables d'env
docker exec latigue_web env | grep DB_
```

### Erreur 502 Bad Gateway
```bash
# Vérifier que le port 8000 est bien exposé
docker ps

# Vérifier le healthcheck
docker inspect latigue_web | grep -A 10 Health
```

### DisallowedHost
```bash
# Ajouter le domaine dans Django settings.py :
ALLOWED_HOSTS = [
    'bolibana.net',
    'www.bolibana.net',
    'votre-service.vm.elestio.app',
]
```

---

## ✅ Checklist finale

- [ ] Service CI/CD Elestio créé et connecté à Github
- [ ] Toutes les variables d'environnement définies
- [ ] PostgreSQL Elestio connecté et accessible
- [ ] Domaine personnalisé configuré (DNS + Elestio)
- [ ] SSL actif sur bolibana.net
- [ ] Healthcheck fonctionnel
- [ ] Backups configurés
- [ ] Git push déclenche bien un déploiement
- [ ] Site accessible et fonctionnel

---

## 🔗 Ressources

- [Documentation Elestio CI/CD](https://docs.elest.io/ci-cd)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
