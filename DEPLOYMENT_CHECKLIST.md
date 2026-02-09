# ✅ Checklist de Déploiement VPS Elestio

Utilisez cette checklist pour suivre votre progression durant la migration.

## 📋 Préparation (Avant le déploiement)

- [ ] **Backup Heroku téléchargé**
  ```bash
  heroku pg:backups:capture --app latigue-9570ef49bb0e
  heroku pg:backups:download --app latigue-9570ef49bb0e
  ```
  Fichier: `latest.dump`

- [ ] **Variables d'environnement Elestio notées**
  - [ ] DB_HOST: `postgres-u67346.vm.elestio.app`
  - [ ] DB_PORT: `5432`
  - [ ] DB_NAME: `_______________`
  - [ ] DB_USER: `_______________`
  - [ ] DB_PASSWORD: `_______________`

- [ ] **Accès SSH VPS configuré**
  - IP VPS: `_______________`
  - Utilisateur: `root`
  - [ ] Test connexion: `ssh root@<VPS_IP>`

- [ ] **AWS S3 opérationnel**
  - [ ] Test upload image depuis Admin Django Heroku
  - [ ] Bucket: `personalporfolio`
  - [ ] CloudFront: `d3tcb6ounmojtn.cloudfront.net`

---

## 🖥️ Phase 1: Préparation du VPS (30 min)

- [ ] **Connexion SSH**
  ```bash
  ssh root@<VPS_IP>
  ```

- [ ] **Mise à jour système**
  ```bash
  apt-get update && apt-get upgrade -y
  ```

- [ ] **Installation Docker**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  docker --version
  ```

- [ ] **Installation Docker Compose**
  ```bash
  apt-get install docker-compose-plugin -y
  docker compose version
  ```

---

## 📦 Phase 2: Déploiement du Code (20 min)

- [ ] **Créer le répertoire**
  ```bash
  mkdir -p /var/www/latigue
  cd /var/www/latigue
  ```

- [ ] **Cloner le projet**

  **Option A - Git:**
  ```bash
  git clone https://github.com/<VOTRE_USERNAME>/latigue.git .
  ```

  **Option B - Rsync (depuis votre machine locale):**
  ```bash
  rsync -avz --exclude='venv' --exclude='*.pyc' --exclude='db.sqlite3' \
    C:\Users\djimi\latigue\ root@<VPS_IP>:/var/www/latigue/
  ```

- [ ] **Vérifier les fichiers**
  ```bash
  ls -la
  # Doit contenir: Dockerfile, docker-compose.yml, nginx/, etc.
  ```

---

## 🔐 Phase 3: Configuration Environnement (15 min)

- [ ] **Générer nouvelle SECRET_KEY**
  ```bash
  python3 generate_secret_key.py
  ```
  SECRET_KEY générée: `_________________________________`

- [ ] **Créer .env.production**
  ```bash
  nano .env.production
  ```

- [ ] **Remplir toutes les variables**
  - [ ] DJANGO_DEBUG=False
  - [ ] DJANGO_SECRET_KEY=<NOUVELLE_CLE>
  - [ ] DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  - [ ] DATABASE_URL
  - [ ] EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
  - [ ] AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.
  - [ ] USE_S3_STORAGE=True

- [ ] **Sécuriser le fichier**
  ```bash
  chmod 600 .env.production
  ls -la .env.production
  # Doit afficher: -rw------- (permissions 600)
  ```

---

## 🗄️ Phase 4: Migration Base de Données (30 min)

- [ ] **Upload du backup**
  ```bash
  # Depuis votre machine locale:
  scp latest.dump root@<VPS_IP>:/var/www/latigue/
  ```

- [ ] **Créer la base de données** (si nécessaire)
  ```bash
  psql -h postgres-u67346.vm.elestio.app -U <DB_USER> -d postgres
  CREATE DATABASE latigue_prod;
  \q
  ```

- [ ] **Restaurer le backup**
  ```bash
  pg_restore --verbose --clean --no-acl --no-owner \
    -h postgres-u67346.vm.elestio.app \
    -U <DB_USER> \
    -d latigue_prod \
    latest.dump
  ```

- [ ] **Vérifier la restauration**
  ```bash
  psql -h postgres-u67346.vm.elestio.app -U <DB_USER> -d latigue_prod
  \dt
  SELECT COUNT(*) FROM blog_blogpost;
  SELECT COUNT(*) FROM services_service;
  \q
  ```
  Nombre de posts: `_____`
  Nombre de services: `_____`

---

## 🐳 Phase 5: Lancement Docker (20 min)

- [ ] **Créer les répertoires**
  ```bash
  cd /var/www/latigue
  mkdir -p nginx/conf.d certbot/conf certbot/www logs staticfiles media
  chmod -R 755 staticfiles media logs
  ```

- [ ] **Choisir le docker-compose**

  **Option A - PostgreSQL EXTERNE (Recommandé):**
  ```bash
  cp docker-compose.external-db.yml docker-compose.yml
  ```

  **Option B - PostgreSQL LOCAL:**
  ```bash
  # Utiliser le docker-compose.yml par défaut
  # Modifier .env.production: DB_HOST=db
  ```

- [ ] **Build les images**
  ```bash
  docker compose build
  ```
  Temps estimé: 3-5 minutes

- [ ] **Démarrer les services**
  ```bash
  docker compose up -d
  ```

- [ ] **Vérifier les conteneurs**
  ```bash
  docker compose ps
  ```
  État attendu:
  - [ ] latigue_web: Up
  - [ ] latigue_nginx: Up
  - [ ] latigue_certbot: Up

- [ ] **Vérifier les logs**
  ```bash
  docker compose logs web | tail -50
  ```
  Doit afficher:
  - [ ] ✅ PostgreSQL is ready!
  - [ ] 🔄 Running migrations...
  - [ ] 🔄 Collecting static files...
  - [ ] ✅ Starting application...

---

## 🌐 Phase 6: Test HTTP (10 min)

- [ ] **Vérifier l'accès HTTP**
  ```bash
  curl -I http://postgres-u67346.vm.elestio.app
  ```
  Statut attendu: `HTTP/1.1 200 OK` ou `302 Found`

- [ ] **Test dans le navigateur**
  - [ ] Page d'accueil: http://postgres-u67346.vm.elestio.app/
  - [ ] Admin: http://postgres-u67346.vm.elestio.app/admin/

- [ ] **Créer un superutilisateur**
  ```bash
  docker compose exec web python manage.py createsuperuser
  ```
  Username: `_______________`
  Email: `_______________`

⚠️ **IMPORTANT**: Si tout fonctionne en HTTP, passez à la Phase 7 pour activer HTTPS.

---

## 🔒 Phase 7: Configuration SSL/HTTPS (15 min)

- [ ] **Obtenir le certificat Let's Encrypt**
  ```bash
  docker compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email <VOTRE_EMAIL> \
    --agree-tos \
    --no-eff-email \
    -d postgres-u67346.vm.elestio.app
  ```
  Statut attendu: `Successfully received certificate`

- [ ] **Vérifier le certificat**
  ```bash
  ls -la certbot/conf/live/postgres-u67346.vm.elestio.app/
  ```
  Fichiers attendus:
  - [ ] fullchain.pem
  - [ ] privkey.pem

- [ ] **Activer HTTPS dans Nginx**
  ```bash
  nano nginx/conf.d/default.conf
  ```
  Modifications:
  - [ ] Décommenter le bloc `server { listen 443 ssl http2; ... }`
  - [ ] Commenter le bloc HTTP temporaire
  - [ ] Activer la redirection HTTPS: `return 301 https://$host$request_uri;`

- [ ] **Recharger Nginx**
  ```bash
  docker compose restart nginx
  docker compose logs nginx | tail -20
  ```

- [ ] **Tester HTTPS**
  ```bash
  curl -I https://postgres-u67346.vm.elestio.app
  ```
  Statut attendu: `HTTP/2 200`

- [ ] **Test renouvellement automatique**
  ```bash
  docker compose run --rm certbot renew --dry-run
  ```
  Statut attendu: `Congratulations, all renewals succeeded!`

---

## ✅ Phase 8: Tests Complets (20 min)

### Tests Techniques

- [ ] **Vérifier les conteneurs**
  ```bash
  docker compose ps
  # Tous les conteneurs doivent être "Up"
  ```

- [ ] **Tester la base de données**
  ```bash
  docker compose exec web python manage.py dbshell
  \dt
  \q
  ```

- [ ] **Vérifier les migrations**
  ```bash
  docker compose exec web python manage.py showmigrations
  # Toutes les migrations doivent être [X]
  ```

- [ ] **Vérifier collectstatic**
  ```bash
  docker compose exec web python manage.py collectstatic --noinput
  # Doit copier les fichiers vers staticfiles/
  ```

### Tests Fonctionnels dans le Navigateur

- [ ] **Page d'accueil**
  URL: https://postgres-u67346.vm.elestio.app/
  - [ ] Page charge correctement
  - [ ] CSS Tailwind appliqué
  - [ ] Aucune erreur 404 console

- [ ] **Admin Django**
  URL: https://postgres-u67346.vm.elestio.app/admin/
  - [ ] Connexion avec superuser
  - [ ] Accès aux modèles (Blog, Services, Formations)
  - [ ] Upload d'une image test
  - [ ] Image visible (chargée depuis S3)

- [ ] **Blog**
  URL: https://postgres-u67346.vm.elestio.app/blog/
  - [ ] Liste des articles
  - [ ] Détail d'un article
  - [ ] Images chargées depuis CloudFront
  - [ ] Markdown rendu correctement

- [ ] **Services**
  URL: https://postgres-u67346.vm.elestio.app/services/
  - [ ] Liste des services
  - [ ] Détail d'un service
  - [ ] Navigation fonctionnelle

- [ ] **Formations**
  URL: https://postgres-u67346.vm.elestio.app/formations/
  - [ ] Liste des formations
  - [ ] Détail d'une formation
  - [ ] Prix affichés correctement

- [ ] **Formulaire de Contact**
  - [ ] Remplir et envoyer le formulaire
  - [ ] Vérifier réception email sur `<VOTRE_EMAIL>`
  - [ ] Confirmation affichée à l'utilisateur

- [ ] **Certificat SSL**
  - [ ] Cadenas vert dans le navigateur
  - [ ] Certificat valide (pas d'avertissement)
  - [ ] Redirection HTTP → HTTPS fonctionne

---

## 📊 Phase 9: Monitoring et Backups (15 min)

- [ ] **Configurer le backup automatique**
  ```bash
  chmod +x backup.sh
  crontab -e
  ```
  Ligne à ajouter:
  ```
  0 2 * * * /var/www/latigue/backup.sh >> /var/log/backup.log 2>&1
  ```

- [ ] **Tester le backup manuellement**
  ```bash
  ./backup.sh
  ls -lh /var/backups/latigue/
  ```
  Fichiers attendus:
  - [ ] db_YYYYMMDD_HHMMSS.sql.gz
  - [ ] media_YYYYMMDD_HHMMSS.tar.gz

- [ ] **Configurer le monitoring des logs**
  ```bash
  # Créer un alias pour voir les logs facilement
  echo "alias latilog='cd /var/www/latigue && docker compose logs -f'" >> ~/.bashrc
  source ~/.bashrc
  ```

---

## 🎉 Phase 10: Finalisation

- [ ] **Documenter les informations**
  - [ ] IP VPS: `_______________`
  - [ ] URL temporaire: https://postgres-u67346.vm.elestio.app
  - [ ] DB Host: postgres-u67346.vm.elestio.app
  - [ ] Admin username: `_______________`

- [ ] **Créer un README pour l'équipe**
  - [ ] Commandes Docker de base
  - [ ] Procédure de mise à jour du code
  - [ ] Contacts en cas de problème

- [ ] **Surveillance post-déploiement (48h)**
  - [ ] Vérifier les logs chaque jour
  - [ ] Tester les fonctionnalités principales
  - [ ] Monitorer l'utilisation CPU/RAM
  - [ ] Vérifier les emails de contact

---

## 🚨 Rollback Plan (si problème)

Si quelque chose ne fonctionne pas:

1. **Heroku est toujours actif**
   - Application toujours accessible sur Heroku
   - Database intacte

2. **Diagnostic VPS**
   ```bash
   docker compose logs
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

3. **Restaurer un backup**
   ```bash
   pg_restore --clean -h postgres-u67346.vm.elestio.app \
     -U <DB_USER> -d latigue_prod /var/backups/latigue/db_*.sql.gz
   ```

---

## 📞 Contacts et Ressources

- **Email**: <VOTRE_EMAIL>
- **Documentation**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Support Elestio**: https://elest.io/docs
- **Docker Docs**: https://docs.docker.com/

---

## ✅ Résumé Final

**Date de migration**: `_______________`
**Durée totale**: `_______________`
**Problèmes rencontrés**:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

**URL production**: https://postgres-u67346.vm.elestio.app

✅ Migration réussie! 🎉

---

**Prochaine étape**: Migration vers domaine custom `bolibana.net` (voir DEPLOYMENT_GUIDE.md Phase 9)
