# 🤖 Nour — Intégration IA sur bolibana.net

> Documentation de l'intégration de Nour (assistant IA) dans le portfolio de Konimba Djimiga.

---

## 📋 Table des matières

1. [Architecture générale](#architecture-générale)
2. [Accès Git — Coder & pusher du code](#accès-git--coder--pusher-du-code)
3. [Accès SSH au VPS](#accès-ssh-au-vps)
4. [Déploiement automatique](#déploiement-automatique)
5. [Chatbot Nour — Widget sur le portfolio](#chatbot-nour--widget-sur-le-portfolio)
6. [Configuration requise](#configuration-requise)
7. [Ce qui reste à faire](#ce-qui-reste-à-faire)

---

## Architecture générale

```
┌──────────────────────────────────────────────────┐
│                  VPS Elestio                      │
│              159.195.104.193                      │
│                                                   │
│  ┌─────────────────┐    ┌──────────────────────┐ │
│  │  OpenClaw (Nour) │    │  Latigue (Django)    │ │
│  │  Container       │    │  Container           │ │
│  │  Port 18789      │    │  Port 8000           │ │
│  │                  │    │                      │ │
│  │  - IA / Agent    │    │  - Portfolio web     │ │
│  │  - Telegram bot  │    │  - Blog, Services    │ │
│  │  - Webchat       │    │  - Formations        │ │
│  │  - Cron jobs     │    │  - Chatbot widget    │ │
│  └─────────────────┘    └──────────────────────┘ │
│           │                        │              │
│           │    ┌──────────┐        │              │
│           └────│ Postgres │────────┘              │
│                │ Port 5432│                       │
│                └──────────┘                       │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  OpenResty (Nginx)  — Ports 80/443          │ │
│  │  SSL + Reverse proxy → localhost:8000       │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
           │
           ▼
     bolibana.net (HTTPS)
```

---

## Accès Git — Coder & pusher du code

### Ce qui a été fait

Nour a un accès **lecture + écriture** sur le repo GitHub via un Personal Access Token.

| Élément | Valeur |
|---------|--------|
| **Repo** | `https://github.com/DJIMIGA/latigue` |
| **Branche** | `main` |
| **Clone local** | `/home/node/.openclaw/workspace/latigue` |
| **Git user** | `Nour <nour@bolibana.net>` |
| **Auth** | Personal Access Token (scope: `public_repo`) |

### Comment ça marche

1. Nour modifie les fichiers dans son workspace
2. `git add` → `git commit` → `git push origin main`
3. Les changements arrivent sur GitHub

### Commandes utilisées

```bash
# Clone initial
cd /home/node/.openclaw/workspace
git clone https://github.com/DJIMIGA/latigue.git

# Configuration Git
cd latigue
git config user.name "Nour"
git config user.email "nour@bolibana.net"

# Remote avec token (stocké dans l'URL)
git remote set-url origin https://<TOKEN>@github.com/DJIMIGA/latigue.git

# Workflow quotidien
git add -A
git commit -m "description du changement"
git push origin main
```

### Sécurité

- Le token est **scopé à `public_repo` uniquement** (minimum de permissions)
- Le token est stocké dans la config Git locale, jamais dans le code
- Si compromis → révoquer sur GitHub Settings → Developer Settings → Personal Access Tokens

---

## Accès SSH au VPS

### Ce qui a été fait

Nour peut se connecter en SSH au VPS pour déployer, diagnostiquer et administrer.

| Élément | Valeur |
|---------|--------|
| **Host** | `159.195.104.193` |
| **User** | `root` |
| **Auth** | Clé SSH ED25519 |
| **Clé publique** | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMNEFpAGdz7iB+5OlsTW5jMBvIz45Hac5RFBmbPdQfoy nour@openclaw` |

### Comment ça marche

```bash
# Connexion directe
ssh root@159.195.104.193

# Exécuter une commande
ssh root@159.195.104.193 "docker compose -f /var/www/latigue/docker-compose.yml ps"
```

### Sécurité

- Clé privée dans `/home/node/.ssh/id_ed25519` (container OpenClaw)
- Pour révoquer : supprimer la ligne correspondante dans `/root/.ssh/authorized_keys` sur le VPS

---

## Déploiement automatique

### Ce qui a été fait

Deux mécanismes de déploiement :

#### A. Déploiement manuel (par Nour via SSH)

```bash
ssh root@159.195.104.193 "cd /var/www/latigue && \
  git pull origin main && \
  docker compose build --no-cache web && \
  docker compose up -d --no-deps web"
```

#### B. Déploiement automatique (webhook GitHub) — À ACTIVER

Un script `deploy.sh` + endpoint webhook sont prêts mais le webhook GitHub n'est **pas encore configuré**.

**Fichiers créés :**

| Fichier | Rôle |
|---------|------|
| `deploy.sh` | Script bash : git pull → docker build → restart → collectstatic → migrate |
| `chatbot/webhook.py` | Endpoint Django `/chatbot/api/webhook/github/` qui reçoit le webhook |

**Pour activer le déploiement auto :**

1. GitHub → Repo → **Settings** → **Webhooks** → **Add webhook**
2. Payload URL : `https://bolibana.net/chatbot/api/webhook/github/`
3. Content type : `application/json`
4. Secret : `bolibana_deploy_2026` (stocké dans `.env.production`)
5. Events : Just the push event ✅

**Flux automatique :**
```
Nour push sur GitHub
        ↓
GitHub appelle le webhook
        ↓
Django reçoit → vérifie la signature HMAC
        ↓
Lance deploy.sh en arrière-plan
        ↓
git pull → docker build → restart
        ↓
Site à jour en ~60 secondes
```

### Déploiement — Commandes de référence

```bash
# Déploiement complet
ssh root@159.195.104.193 "cd /var/www/latigue && \
  git pull origin main && \
  docker compose build --no-cache web && \
  docker compose up -d --no-deps web"

# Juste restart (sans rebuild)
ssh root@159.195.104.193 "cd /var/www/latigue && \
  docker compose restart web"

# Collectstatic (après modif CSS/JS)
ssh root@159.195.104.193 "cd /var/www/latigue && \
  docker compose exec -T web python manage.py collectstatic --noinput"

# Migrations (après modif models)
ssh root@159.195.104.193 "cd /var/www/latigue && \
  docker compose exec -T web python manage.py migrate --noinput"

# Voir les logs
ssh root@159.195.104.193 "cd /var/www/latigue && \
  docker compose logs web --tail 20"
```

---

## Chatbot Nour — Widget sur le portfolio

### Ce qui a été fait

#### Frontend ✅

Un widget de chat flottant intégré sur toutes les pages du site.

| Fichier | Rôle |
|---------|------|
| `static/js/chatbot.js` | Widget complet (HTML + CSS + JS) injecté dynamiquement |
| `templates/base.html` | `<script src="chatbot.js" defer>` ajouté |

**Fonctionnalités du widget :**
- 💬 Bulle flottante violette (en bas à droite, à côté du bouton WhatsApp)
- 📱 Responsive mobile
- 🌙 Dark mode automatique
- ⌨️ Animation "typing" pendant l'attente
- 💾 Session ID persisté en localStorage (continuité de conversation)
- 🎨 Design cohérent avec la charte du site (couleur primaire indigo/violet)

#### Backend ✅

| Fichier | Rôle |
|---------|------|
| `chatbot/__init__.py` | App Django |
| `chatbot/apps.py` | Config de l'app |
| `chatbot/urls.py` | Routes : `/chatbot/api/chat/` et `/chatbot/api/webhook/github/` |
| `chatbot/views.py` | API chat — appelle l'API Anthropic (Claude) |
| `chatbot/webhook.py` | Webhook GitHub pour auto-deploy |

**Comment ça marche :**

```
Visiteur tape un message
        ↓
JS envoie POST /chatbot/api/chat/
  { message: "...", session_id: "v_xxx" }
        ↓
Django reçoit → appelle l'API Anthropic
  (Claude claude-sonnet-4-20250514, max 512 tokens)
        ↓
Claude répond avec le contexte du portfolio
        ↓
Django renvoie → JS affiche la réponse
```

**System prompt de Nour :**
- Présente le portfolio de Konimba
- Parle français par défaut
- Concis (2-3 phrases)
- Redirige vers le portfolio si hors sujet
- Connaît les services, formations, blog, réseaux sociaux

### ⚠️ Ce qui bloque — Clé API Anthropic

**Statut actuel : le widget s'affiche mais ne peut pas répondre.**

Les tokens OAuth d'OpenClaw (`sk-ant-oat01-...`) ne fonctionnent pas directement avec l'API Anthropic. Il faut une **vraie clé API**.

**Solution :** Créer une clé API sur [console.anthropic.com](https://console.anthropic.com) :
1. Se connecter / créer un compte
2. Aller dans **API Keys**
3. Créer une clé (format `sk-ant-api03-...`)
4. L'ajouter dans `.env.production` sur le VPS :

```bash
ssh root@159.195.104.193 "cd /var/www/latigue && \
  sed -i 's/^ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=sk-ant-api03-TA_NOUVELLE_CLE/' .env.production && \
  cp .env.production .env && \
  docker compose up -d --no-deps web"
```

**Alternative gratuite :** Utiliser un autre modèle (Groq, Mistral, Ollama local). Nour peut adapter le code facilement.

---

## Configuration requise

### Fichiers de configuration sur le VPS

**`/var/www/latigue/.env.production`** (fichier secrets, jamais dans Git) :

```env
# Django
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<secret>
DJANGO_SETTINGS_MODULE=latigue.settings

# Base de données
DB_HOST=postgres-u67346.vm.elestio.app
DB_PORT=25432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=<password>

# Chatbot
ANTHROPIC_API_KEY=<clé API Anthropic>    # ← À REMPLACER avec une vraie clé

# Auto-deploy webhook
GITHUB_WEBHOOK_SECRET=bolibana_deploy_2026

# OpenClaw gateway (pour usage futur)
OPENCLAW_GATEWAY_URL=ws://172.17.0.1:18789
OPENCLAW_GATEWAY_TOKEN=<token>
```

### Apps Django installées

Dans `latigue/settings.py`, l'app `chatbot` a été ajoutée à `INSTALLED_APPS`.

### URLs

Dans `latigue/urls.py` :
```python
path('chatbot/', include('chatbot.urls')),
```

### Docker

Le `Dockerfile` a été mis à jour de `python:3.9.4-slim` (Buster, EOL) vers `python:3.11-slim-bookworm`.

---

## Ce qui reste à faire

### Priorité haute 🔴

- [ ] **Obtenir une clé API Anthropic** (ou alternative) pour activer le chatbot
- [ ] **Activer le webhook GitHub** pour le déploiement automatique

### Priorité moyenne 🟡

- [ ] Rate limiting sur l'API chat (éviter les abus)
- [ ] Stocker les conversations en DB (au lieu de la mémoire)
- [ ] Ajouter un CSRF token pour sécuriser l'endpoint
- [ ] Logs des conversations pour analyse

### Priorité basse 🟢

- [ ] Personnaliser le design du widget (couleurs, avatar)
- [ ] Ajouter des réponses rapides / boutons suggérés
- [ ] Mode nuit forcé / animations supplémentaires
- [ ] Connecter le chatbot au gateway OpenClaw (pour parler à "Nour" directement)

---

## Résumé des commits

| Date | Commit | Description |
|------|--------|-------------|
| 2026-02-09 | `fac0c54` | ✨ Ajout chatbot Nour — widget + API Django |
| 2026-02-09 | `ff6126c` | 🔄 Auto-deploy: webhook GitHub + script |
| 2026-02-09 | `64a4fb7` | 🐳 Upgrade Dockerfile Python 3.11 |
| 2026-02-09 | `5b890fe` | 🤖 Chatbot: API Anthropic directe |

---

*Documentation rédigée par Nour ✨ — 9 février 2026*
