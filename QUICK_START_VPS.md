# 🚀 Quick Start - Déploiement VPS (Version courte)

Pour une migration rapide si vous êtes familier avec Docker et Linux.

## 📝 Préparation

1. **Télécharger le backup Heroku**
   ```bash
   heroku pg:backups:capture && heroku pg:backups:download
   ```

2. **Noter les variables Elestio**
   - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

## 🖥️ Sur le VPS

```bash
# 1. Installer Docker
ssh root@<VPS_IP>
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
apt-get install docker-compose-plugin -y

# 2. Cloner le projet
mkdir -p /var/www/latigue && cd /var/www/latigue
git clone <VOTRE_REPO> .

# 3. Configurer l'environnement
python3 generate_secret_key.py  # Copier la clé générée
nano .env.production  # Remplir toutes les variables
chmod 600 .env.production

# 4. Restaurer la base de données
scp latest.dump root@<VPS_IP>:/var/www/latigue/  # Depuis votre machine locale
pg_restore --clean --no-acl --no-owner \
  -h postgres-u67346.vm.elestio.app -U <DB_USER> -d latigue_prod latest.dump

# 5. Lancer l'application
mkdir -p nginx/conf.d certbot/conf certbot/www logs staticfiles media
# Utiliser docker-compose.yml (DB dans le compose). Pour DB externe, définir DB_HOST dans .env
docker compose build && docker compose up -d

# 6. Vérifier
docker compose ps
docker compose logs -f web

# 7. Créer un superutilisateur
docker compose exec web python manage.py createsuperuser

# 8. Configurer SSL
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email <VOTRE_EMAIL> --agree-tos \
  -d postgres-u67346.vm.elestio.app

# Activer HTTPS dans nginx/conf.d/default.conf puis:
docker compose restart nginx

# 9. Backups automatiques
chmod +x backup.sh
crontab -e
# Ajouter: 0 2 * * * /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1
```

## ✅ Tests

- https://postgres-u67346.vm.elestio.app/ (page d'accueil)
- https://postgres-u67346.vm.elestio.app/admin/ (admin)
- Tester upload image, formulaire contact, blog

## 🔧 Commandes Utiles

```bash
docker compose logs -f              # Voir les logs
docker compose restart web          # Redémarrer Django
docker compose exec web python manage.py <cmd>  # Commandes Django
docker compose down && docker compose up -d --build  # Rebuild complet
```

## 📚 Documentation Complète

- **Checklist détaillée**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Guide complet**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Résumé migration**: [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)

---

⏱️ **Temps estimé**: 1-2 heures pour une personne expérimentée
