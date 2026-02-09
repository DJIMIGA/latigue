# Latigue - Portfolio Django

Portfolio personnel avec blog, services et formations développé avec Django 4.2.

## 🌐 Production

- **URL Temporaire**: https://postgres-u67346.vm.elestio.app
- **Domaine Final**: https://bolibana.net (à configurer)
- **Admin**: `/admin/`

## 🚀 Stack Technique

- **Framework**: Django 4.2.13
- **Base de données**: PostgreSQL 15
- **Serveur Web**: Gunicorn + Nginx
- **Conteneurisation**: Docker + Docker Compose
- **Fichiers Statiques**: WhiteNoise
- **Fichiers Média**: AWS S3 + CloudFront CDN
- **SSL**: Let's Encrypt (certbot)
- **Email**: Gmail SMTP
- **Frontend**: Tailwind CSS

## 📦 Applications Django

- `portfolio` - Page d'accueil et informations personnelles
- `blog` - Articles de blog avec Markdown et coloration syntaxique
- `services` - Services proposés
- `formations` - Formations disponibles
- `ckeditor` - Éditeur WYSIWYG pour l'admin

## 🛠️ Développement Local

### Prérequis

- Python 3.9.4
- Node.js 18+ (pour Tailwind CSS)
- PostgreSQL (optionnel, SQLite par défaut en dev)

### Installation

```bash
# Cloner le projet
git clone https://github.com/<VOTRE_USERNAME>/latigue.git
cd latigue

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances Python
pip install -r requirements.txt

# Installer les dépendances Node (Tailwind)
npm install

# Créer le fichier .env
cp .env.example .env
# Remplir les variables nécessaires

# Migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Build Tailwind CSS
npm run build

# Lancer le serveur de développement
python manage.py runserver
```

L'application sera accessible sur http://localhost:8000

### Variables d'Environnement (.env)

```bash
# Django
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=<votre-cle-secrete>

# Email (optionnel en dev)
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app

# AWS S3 (optionnel en dev)
USE_S3_STORAGE=False  # True pour tester S3
AWS_ACCESS_KEY_ID=<votre-access-key>
AWS_SECRET_ACCESS_KEY=<votre-secret-key>
AWS_STORAGE_BUCKET_NAME=<votre-bucket>
AWS_S3_REGION_NAME=eu-north-1
```

## 🐳 Déploiement Docker (Production)

Le projet est configuré pour être déployé sur un VPS avec Docker.

### Quick Start

```bash
# Sur le VPS
cd /var/www/latigue
git clone <VOTRE_REPO> .

# Configuration
python3 generate_secret_key.py
nano .env.production  # Remplir toutes les variables
chmod 600 .env.production

# Lancement
mkdir -p nginx/conf.d certbot/conf certbot/www logs staticfiles media
docker compose build
docker compose up -d

# Logs
docker compose logs -f
```

### Documentation Déploiement

- 📋 **[Checklist Détaillée](DEPLOYMENT_CHECKLIST.md)** - Checklist étape par étape avec cases à cocher
- 📖 **[Guide Complet](DEPLOYMENT_GUIDE.md)** - Guide de déploiement exhaustif avec explications
- 🚀 **[Quick Start VPS](QUICK_START_VPS.md)** - Version rapide pour utilisateurs expérimentés
- 📊 **[Résumé Migration](MIGRATION_SUMMARY.md)** - Résumé de la migration Heroku → VPS

### Commandes Docker Utiles

```bash
# Voir les conteneurs
docker compose ps

# Logs en temps réel
docker compose logs -f web

# Redémarrer l'application
docker compose restart web

# Rebuild après changements
docker compose up -d --build web

# Exécuter des commandes Django
docker compose exec web python manage.py <commande>

# Shell Django
docker compose exec web python manage.py shell

# Accès PostgreSQL
docker compose exec db psql -U <DB_USER> -d <DB_NAME>

# Arrêter tous les services
docker compose down
```

## 🔐 Sécurité

- ✅ DEBUG=False en production
- ✅ SECRET_KEY unique et sécurisée
- ✅ SSL/HTTPS avec Let's Encrypt
- ✅ CSRF_TRUSTED_ORIGINS configuré
- ✅ Headers de sécurité Django (HSTS, etc.)
- ✅ Fichiers sensibles dans .gitignore
- ✅ Variables d'environnement sécurisées

## 📊 SEO et Performance

- ✅ Sitemap XML automatique (`/sitemap.xml`)
- ✅ Robots.txt optimisé
- ✅ Meta tags SEO (title, description, OG)
- ✅ Structured Data (JSON-LD)
- ✅ Cache headers pour fichiers statiques
- ✅ WhiteNoise pour compression et fingerprinting
- ✅ CDN CloudFront pour les médias
- ✅ Index de base de données optimisés

## 🔄 Backups

```bash
# Script de backup automatique inclus
./backup.sh

# Configurer le cron (quotidien à 2h du matin)
crontab -e
# Ajouter: 0 2 * * * /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1
```

Les backups sont stockés dans `/var/backups/latigue/` et conservés pendant 7 jours.

## 🧪 Tests

```bash
# Lancer les tests
python manage.py test

# Tests avec coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Gestion de Contenu

### Admin Django

L'interface d'administration est accessible sur `/admin/` et permet de gérer:

- Articles de blog (avec Markdown et CKEditor)
- Services et formations
- Images (upload vers S3)
- Utilisateurs

### Markdown pour les Articles

Les articles de blog supportent le Markdown avec:
- Coloration syntaxique (Pygments)
- Images
- Liens
- Listes
- Citations
- Code blocks

## 🌍 Domaine Custom

Pour migrer vers le domaine `bolibana.net`:

1. Configurer les DNS (Type A: bolibana.net → IP VPS)
2. Obtenir le certificat SSL: `docker compose run --rm certbot certonly --webroot -d bolibana.net -d www.bolibana.net`
3. Mettre à jour `nginx/conf.d/default.conf` (server_name)
4. Redémarrer nginx: `docker compose restart nginx`

Voir [DEPLOYMENT_GUIDE.md Phase 9](DEPLOYMENT_GUIDE.md#phase-9-migration-du-domaine-custom-bolibabanet) pour plus de détails.

## 🐛 Troubleshooting

### Le site ne charge pas
```bash
docker compose logs nginx
docker compose logs web
```

### Erreurs de base de données
```bash
docker compose exec web python manage.py check --database default
docker compose exec web python manage.py migrate
```

### Fichiers statiques manquants
```bash
docker compose exec web python manage.py collectstatic --clear --noinput
```

### Certificat SSL expiré
```bash
docker compose run --rm certbot renew --force-renewal
docker compose restart nginx
```

## 📞 Contact

- **Email**: <VOTRE_EMAIL>
- **Site**: https://bolibana.net

## 📄 License

Tous droits réservés.

---

**Version**: 2.0.0 (Migration VPS)
**Dernière mise à jour**: 2026-02-08
