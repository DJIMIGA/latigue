# 🚀 Guide de déploiement Latigue

Ce projet Django peut être déployé de **deux façons** :

## 1️⃣ Développement Local

```bash
# Copier le template d'environnement
cp .env.production.example .env

# Éditer .env avec vos valeurs locales
nano .env

# Lancer avec PostgreSQL local
docker compose -f docker-compose.dev.yml up --build

# L'application est disponible sur http://localhost:8000
```

## 2️⃣ Production sur Elestio (CI/CD automatique)

### Option A : Github CI/CD (Recommandé)

**Étape 1** : Pushez ce code sur Github

```bash
git add .
git commit -m "Configuration Docker Compose pour Elestio"
git push origin main
```

**Étape 2** : Dans l'interface Elestio

1. **Create CI/CD pipeline** → Choisir **Github**
2. **Source** :
   - Repository : `votre-username/latigue`
   - Branch : `main`
   - Docker Compose file : `docker-compose.prod.yml`
3. **Target** :
   - Region : eu-central (ou votre choix)
   - VPS Size : 2GB minimum
4. **Configuration** :
   - Service name : `latigue`
   - Ports : `8000`

**Étape 3** : Définir les variables d'environnement

Dans Elestio UI → Environment Variables, ajoutez toutes les variables de `.env.production.example`

**Résultat** : Chaque `git push` déclenchera un déploiement automatique ! 🎉

### Option B : Custom Docker Compose (Upload manuel)

1. **Create CI/CD pipeline** → Choisir **Custom docker-compose**
2. Copier le contenu de `docker-compose.prod.yml`
3. Coller dans l'éditeur Elestio
4. Ajouter les variables d'environnement
5. Deploy !

---

## 📚 Documentation détaillée

- **[ELESTIO_SETUP.md](./ELESTIO_SETUP.md)** - Guide complet Elestio avec troubleshooting
- **[DEPLOIEMENT_VPS_ELESTIO.md](./DEPLOIEMENT_VPS_ELESTIO.md)** - Historique du déploiement actuel

---

## 🔐 Sécurité

⚠️ **IMPORTANT** : Ne commitez JAMAIS ces fichiers :
- `.env`
- `.env.production`
- Tout fichier contenant des credentials

Ces fichiers sont déjà dans `.gitignore` ✅

---

## 🧪 Tester avant de déployer

```bash
# Build local avec la config production
docker compose -f docker-compose.prod.yml build

# Vérifier que l'image se build correctement
docker images | grep latigue
```

---

## 📦 Structure des fichiers

```
latigue/
├── docker-compose.prod.yml    # Production Elestio (CI/CD)
├── docker-compose.dev.yml     # Développement local
├── docker-compose.yml         # Ancien (à supprimer après migration)
├── Dockerfile                 # Image Docker avec healthcheck
├── docker-entrypoint.sh       # Script de démarrage
├── .env.production.example    # Template (PAS de secrets)
├── .env                       # Vos secrets (GIT IGNORÉ)
├── backup.sh                  # Script de backup sécurisé
├── healthcheck.sh             # Healthcheck externe (optionnel)
└── ELESTIO_SETUP.md          # Guide détaillé
```

---

## 🆘 Besoin d'aide ?

Consultez le [troubleshooting dans ELESTIO_SETUP.md](./ELESTIO_SETUP.md#-troubleshooting)
