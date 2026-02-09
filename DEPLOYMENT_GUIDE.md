# Guide de Déploiement - Migration Heroku vers Elestio VPS

Ce guide vous accompagne dans le déploiement de votre application Django sur le VPS Elestio.

## 📋 Prérequis

- [ ] Accès SSH au VPS Elestio
- [ ] Variables d'environnement PostgreSQL Elestio (DB_HOST, DB_USER, DB_PASSWORD)
- [ ] Backup de la base de données Heroku téléchargé
- [ ] AWS S3 configuré et opérationnel

## ⚙️ Étape 1: Préparer le VPS

```bash
# Connexion SSH
ssh root@<ELESTIO_VPS_IP>

# Mettre à jour le système
apt-get update && apt-get upgrade -y

# Installer Docker (si nécessaire)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installer Docker Compose plugin
apt-get install docker-compose-plugin -y

# Vérifier l'installation
docker --version
docker compose version
```

## 📦 Étape 2: Déployer l'Application

```bash
# Créer le répertoire de l'application
mkdir -p /var/www/latigue
cd /var/www/latigue

# Cloner le projet (remplacez par votre URL Git)
git clone https://github.com/<VOTRE_USERNAME>/latigue.git .

# OU upload via rsync depuis votre machine locale:
# rsync -avz --exclude='venv' --exclude='*.pyc' --exclude='db.sqlite3' \
#   C:\Users\djimi\latigue\ root@<VPS_IP>:/var/www/latigue/
```

## 🔐 Étape 3: Configuration des Variables d'Environnement

```bash
# Générer une nouvelle SECRET_KEY (ne pas réutiliser celle de Heroku!)
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Créer le fichier .env.production
nano .env.production
```

Copier le contenu suivant dans `.env.production` (remplacer les valeurs par les vôtres):

```bash
# Django Core
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<VOTRE_NOUVELLE_CLE_SECRETE>
DJANGO_SETTINGS_MODULE=latigue.settings

# Database Elestio
DB_HOST=postgres-u67346.vm.elestio.app
DB_PORT=5432
DB_NAME=latigue_prod
DB_USER=<USERNAME_ELESTIO>
DB_PASSWORD=<PASSWORD_ELESTIO>
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Email Gmail
EMAIL_HOST_USER=<VOTRE_EMAIL>
EMAIL_HOST_PASSWORD=<VOTRE_MOT_DE_PASSE_APP>
CONTACT_EMAIL=<VOTRE_EMAIL>
DEFAULT_FROM_EMAIL=<VOTRE_EMAIL>

# AWS S3
AWS_ACCESS_KEY_ID=<VOTRE_AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<VOTRE_AWS_SECRET_KEY>
AWS_STORAGE_BUCKET_NAME=personalporfolio
AWS_S3_REGION_NAME=eu-north-1
AWS_S3_CUSTOM_DOMAIN=d3tcb6ounmojtn.cloudfront.net
USE_S3_STORAGE=True
```

```bash
# Sécuriser le fichier
chmod 600 .env.production
```

## 🗄️ Étape 4: Restaurer la Base de Données

```bash
# Option A: Télécharger le backup depuis votre machine
scp latest.dump root@<VPS_IP>:/var/www/latigue/

# Option B: Télécharger directement depuis Heroku (si heroku CLI installé)
# heroku pg:backups:download --app latigue-9570ef49bb0e

# Restaurer dans PostgreSQL Elestio
pg_restore --verbose --clean --no-acl --no-owner \
  -h postgres-u67346.vm.elestio.app \
  -U <DB_USER> \
  -d latigue_prod \
  latest.dump

# Vérifier la restauration
psql -h postgres-u67346.vm.elestio.app -U <DB_USER> -d latigue_prod -c "\dt"
```

## 🐳 Étape 5: Créer les Répertoires et Lancer Docker

```bash
# Créer les répertoires nécessaires
mkdir -p nginx/conf.d certbot/conf certbot/www logs staticfiles media

# Donner les permissions
chmod -R 755 staticfiles media logs

# Build et démarrer les conteneurs
docker compose build
docker compose up -d

# Vérifier que tout fonctionne
docker compose ps
docker compose logs -f web
```

Vous devriez voir:
```
✅ PostgreSQL is ready!
🔄 Running migrations...
🔄 Collecting static files...
✅ Starting application...
```

## 🔒 Étape 6: Configuration SSL (Let's Encrypt)

```bash
# Tester que le domaine est accessible
curl -I http://postgres-u67346.vm.elestio.app

# Obtenir le certificat SSL
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email <VOTRE_EMAIL> \
  --agree-tos \
  --no-eff-email \
  -d postgres-u67346.vm.elestio.app

# Activer HTTPS dans Nginx
nano nginx/conf.d/default.conf
```

Dans le fichier, décommenter le bloc `server` qui écoute sur le port 443 et activer la redirection HTTPS.

```bash
# Recharger Nginx
docker compose restart nginx

# Tester le renouvellement automatique
docker compose run --rm certbot renew --dry-run
```

## ✅ Étape 7: Tests de Vérification

```bash
# 1. Vérifier les conteneurs
docker compose ps

# 2. Tester la base de données
docker compose exec web python manage.py dbshell
\dt
\q

# 3. Créer un superutilisateur
docker compose exec web python manage.py createsuperuser

# 4. Vérifier collectstatic
docker compose exec web python manage.py collectstatic --noinput

# 5. Voir les logs
docker compose logs web | tail -50
```

### Tests dans le navigateur:

1. ✅ Page d'accueil: https://postgres-u67346.vm.elestio.app/
2. ✅ Admin Django: https://postgres-u67346.vm.elestio.app/admin/
3. ✅ Blog: https://postgres-u67346.vm.elestio.app/blog/
4. ✅ Services: https://postgres-u67346.vm.elestio.app/services/
5. ✅ Formulaire de contact (test envoi email)

## 📊 Étape 8: Configuration du Backup Automatique

```bash
# Rendre le script exécutable
chmod +x /var/www/latigue/backup.sh

# Configurer le cron (backup quotidien à 2h du matin)
crontab -e

# Ajouter cette ligne:
0 2 * * * /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1
```

## 🔧 Commandes Utiles

```bash
# Redémarrer l'application
docker compose restart web

# Rebuild après changements
docker compose up -d --build web

# Voir les logs en temps réel
docker compose logs -f

# Exécuter des commandes Django
docker compose exec web python manage.py <command>

# Accéder au shell Django
docker compose exec web python manage.py shell

# Accéder au shell PostgreSQL
docker compose exec db psql -U <DB_USER> -d <DB_NAME>

# Arrêter tous les services
docker compose down

# Supprimer tous les conteneurs et volumes (⚠️ DANGER)
docker compose down -v
```

## 🌐 Étape 9: Migration vers Domaine Custom (bolibana.net)

Quand vous serez prêt:

### Configuration DNS

Chez votre registrar:
```
Type A: bolibana.net → <IP_VPS>
Type A: www.bolibana.net → <IP_VPS>
```

### Obtenir le certificat SSL

```bash
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email <VOTRE_EMAIL> \
  --agree-tos \
  -d bolibana.net \
  -d www.bolibana.net
```

### Mettre à jour Nginx

```bash
# Modifier server_name dans nginx/conf.d/default.conf
nano nginx/conf.d/default.conf

# Changer:
server_name postgres-u67346.vm.elestio.app;
# En:
server_name bolibana.net www.bolibana.net;

# Recharger
docker compose restart nginx
```

## 🚨 Troubleshooting

### Problème: Le site ne charge pas

```bash
# Vérifier les logs
docker compose logs nginx
docker compose logs web

# Vérifier que les ports sont ouverts
netstat -tuln | grep -E '80|443|8000'
```

### Problème: Erreurs de base de données

```bash
# Vérifier la connexion
docker compose exec web python manage.py check --database default

# Relancer les migrations
docker compose exec web python manage.py migrate
```

### Problème: Fichiers statiques ne chargent pas

```bash
# Recollect les fichiers statiques
docker compose exec web python manage.py collectstatic --clear --noinput

# Vérifier les permissions
ls -la staticfiles/
```

### Problème: Certificat SSL expire

```bash
# Forcer le renouvellement
docker compose run --rm certbot renew --force-renewal
docker compose restart nginx
```

## 📝 Notes Importantes

- ⚠️ **Ne jamais** commiter le fichier `.env.production` dans Git
- ⚠️ **Toujours** tester les backups régulièrement
- ⚠️ **Surveiller** les logs après le déploiement
- ✅ **Maintenir** Docker et les images à jour
- ✅ **Documenter** tous les changements de configuration

## 🎉 Déploiement Réussi!

Votre application Django est maintenant déployée sur Elestio VPS avec:
- ✅ Docker containerisé
- ✅ PostgreSQL externe
- ✅ Nginx reverse proxy
- ✅ SSL/HTTPS avec Let's Encrypt
- ✅ AWS S3 pour les médias
- ✅ Backups automatiques

Pour toute question, consultez la documentation Docker ou contactez le support Elestio.
