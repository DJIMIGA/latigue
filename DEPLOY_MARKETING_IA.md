# 🚀 Déploiement Pipeline Marketing IA — Checklist

## 📦 Fichiers créés

### ✅ Phase 1 — Infrastructure (FAIT)

**App Django `marketing/` :**
- `__init__.py`, `apps.py`, `models.py`, `admin.py`
- `ai/script_generator.py` — Générateur de scripts (Claude/GPT)
- `storage.py` — Helper MinIO (upload/download S3-compatible)
- `README.md` — Documentation complète

**Docker & Config :**
- MinIO : service Elestio séparé (ports 9000/9001) ou `MINIO_ENDPOINT` dans .env
- `.env.production.example` — Variables MinIO + APIs IA ajoutées
- `requirements-marketing.txt` — Dépendances IA (OpenAI, ElevenLabs, MoviePy, Whisper, Celery)
- `MINIO_SETUP.md` — Guide complet MinIO

**Docs :**
- `memory/strategie-marketing-ia.md` — Stratégie complète (13KB)
- `memory/persona-marketing.md` — Personas et piliers de contenu

---

## 🔧 Étapes de déploiement (À faire sur VPS)

### 1. Push le code sur GitHub

```bash
cd /home/node/.openclaw/workspace/latigue

# Vérifier changements
git status

# Ajouter fichiers
git add marketing/ MINIO_SETUP.md DEPLOY_MARKETING_IA.md requirements-marketing.txt .env.production.example

# Commit
git commit -m "feat: Pipeline Marketing IA - Phase 1 MVP (MinIO + script generator)"

# Push
git push origin main
```

### 2. Connecter au VPS et pull

```bash
ssh root@159.195.104.193
cd /opt/app/latigue
git pull origin main
```

### 3. Fusionner les dépendances

```bash
# Ajouter requirements-marketing.txt dans requirements.txt
cat requirements-marketing.txt >> requirements.txt

# Ou éditer manuellement requirements.txt
nano requirements.txt
```

**⚠️ NOTE:** Commenter ou enlever `torch` et `torchaudio` si espace limité. On peut utiliser l'API OpenAI Whisper à la place.

### 4. Mettre à jour le Dockerfile

Ajouter FFmpeg dans le Dockerfile :

```dockerfile
# Avant la ligne RUN pip install...
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*
```

### 5. Activer l'app dans Django

Éditer `latigue/settings.py` :

```python
INSTALLED_APPS = [
    ...
    'services',
    'formations',
    'chatbot',
    'marketing',  # ← AJOUTER ICI
]
```

### 6. Configurer les variables d'environnement

Éditer `.env.production` (ou UI Elestio) :

```bash
# === MinIO ===
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE
MINIO_BUCKET_VIDEOS=marketing-videos

# === Marketing IA APIs ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# === Réseaux sociaux (Phase 3) ===
TIKTOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...
YOUTUBE_API_KEY=...

# === Celery (Phase 2) ===
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**🔑 Où obtenir les API keys :**
- **Anthropic Claude :** https://console.anthropic.com/settings/keys
- **OpenAI (DALL-E 3):** https://platform.openai.com/api-keys
- **ElevenLabs (TTS):** https://elevenlabs.io/app/settings/api-keys

### 7. Rebuild et redéployer

```bash
cd /opt/app/latigue

# Rebuild avec nouvelles dépendances
docker compose build web

# Redémarrer tous les services
docker compose down
docker compose up -d
```

### 8. Faire les migrations Django

```bash
docker exec -it latigue_web python manage.py makemigrations marketing
docker exec -it latigue_web python manage.py migrate
```

### 9. Vérifier que MinIO tourne

```bash
# Vérifier containers
docker ps | grep minio

# Logs MinIO
docker logs latigue_minio

# Accéder à la console MinIO
# URL : http://159.195.104.193:9001
# Login : minioadmin / mot_de_passe_configuré
```

### 10. Tester la connexion MinIO

```bash
docker exec -it latigue_web python manage.py shell
```

```python
from marketing.storage import get_storage

storage = get_storage()
print(f"✅ Connecté : {storage.endpoint}")
print(f"✅ Bucket : {storage.bucket_videos}")

# Lister fichiers (devrait être vide au début)
files = storage.list_files()
print(f"📁 Fichiers : {len(files)}")
```

Si ça affiche sans erreur → **MinIO fonctionne !** ✅

### 11. Tester la génération de script

```bash
docker exec -it latigue_web python manage.py shell
```

```python
from marketing.ai import generate_script

# Générer un script
result = generate_script(
    pillar='tips',
    theme='Liste comprehension Python en 30 secondes'
)

print("📝 Caption :", result['caption'])
print("🏷️ Hashtags :", result['hashtags'])
print("🎣 Hook :", result['script']['hook']['text'])
print("🖼️ Prompts images :", len(result['image_prompts']))
```

Si ça génère un script → **IA fonctionne !** ✅

### 12. Créer un script en DB

```python
from marketing.models import ContentScript

script = ContentScript.objects.create(
    pillar='tips',
    theme='Liste comprehension Python',
    script_json=result['script'],
    caption=result['caption'],
    hashtags=result['hashtags']
)

print(f"✅ Script créé : ID {script.id}")
```

### 13. Accéder à l'admin Django

URL : `https://bolibana.net/admin/`

**Sections disponibles :**
- **Scripts de contenu** → Voir le script créé
- **Projets vidéo** (vide pour l'instant)
- **Publications** (vide pour l'instant)

---

## 🎯 Prochaines étapes (Phase 1 — reste à coder)

### À faire ensuite :

1. **`marketing/ai/image_generator.py`**
   - Génération d'images avec DALL-E 3
   - Upload vers MinIO automatique

2. **`marketing/ai/tts_generator.py`**
   - Génération voix-off avec ElevenLabs
   - Export MP3 + upload MinIO

3. **`marketing/ai/video_editor.py`**
   - Montage vidéo avec MoviePy
   - Enchaînement images + audio + sous-titres
   - Export MP4 + upload MinIO

4. **`marketing/management/commands/generate_content.py`**
   - CLI pour générer une vidéo complète
   - `python manage.py generate_content --pillar tips --theme "ton thème"`

5. **Test end-to-end : produire 1 vidéo complète**

Tu veux que je code ces modules maintenant ou tu préfères d'abord déployer ce qui est prêt pour tester ?

---

## 🆘 Troubleshooting

### Erreur "ModuleNotFoundError: No module named 'marketing'"
→ Pas migré ou app pas dans INSTALLED_APPS
```bash
docker exec -it latigue_web python manage.py migrate
```

### MinIO "Connection refused"
→ Container MinIO pas démarré ou problème réseau Docker
```bash
docker logs latigue_minio
docker network inspect latigue_app_network
```

### "No module named 'openai'" / "No module named 'elevenlabs'"
→ Dépendances pas installées
```bash
docker exec -it latigue_web pip install -r requirements.txt
# Ou rebuild l'image
docker compose build web
```

### DALL-E 3 "Insufficient quota"
→ Crédit OpenAI épuisé ou pas de méthode de paiement
→ Vérifier : https://platform.openai.com/account/usage

### ElevenLabs "Unauthorized"
→ API key invalide ou plan gratuit épuisé
→ Vérifier : https://elevenlabs.io/app/usage

---

## 💰 Budget estimé (Phase 1 tests)

**Génération de 10 vidéos test :**
- 10 scripts (Claude) : $0.10
- 80 images (DALL-E 3) : $3.20
- 10 voix-off (ElevenLabs) : $0.20
- **Total : ~$3.50**

**Plan gratuit :**
- Claude (via OpenClaw) : probablement gratuit si tu utilises ton token anthropic:antropic
- DALL-E 3 : $5 de crédit offert lors de l'inscription OpenAI (50+ images)
- ElevenLabs : 10,000 chars gratuits/mois (≈ 10-15 vidéos)

**→ Tu peux tester gratuitement !**

---

## 📊 Checklist complète

### ✅ Fait (local)
- [x] App Django `marketing` créée
- [x] Models (ContentScript, VideoProject, Publication)
- [x] Admin Django configuré
- [x] `script_generator.py` (Claude/GPT)
- [x] `storage.py` (MinIO helper)
- [x] Docker Compose MinIO configuré
- [x] Documentation complète

### 🔧 À faire (VPS)
- [ ] Push sur GitHub
- [ ] Pull sur VPS
- [ ] Fusionner requirements-marketing.txt
- [ ] Mettre à jour Dockerfile (FFmpeg)
- [ ] Activer app dans settings.py
- [ ] Configurer .env.production (API keys)
- [ ] Rebuild + redéployer containers
- [ ] Migrations Django
- [ ] Tester MinIO
- [ ] Tester génération script
- [ ] Créer premier script en DB

### 💻 À coder (Phase 1 suite)
- [ ] `image_generator.py`
- [ ] `tts_generator.py`
- [ ] `video_editor.py`
- [ ] `generate_content.py` (CLI)
- [ ] Produire 1 vidéo test complète

### 🚀 Phase 2 (Automatisation)
- [ ] Celery + Redis
- [ ] Tasks async (enchaînement auto)
- [ ] Dashboard admin amélioré
- [ ] Batch production (5 vidéos)

### 📱 Phase 3 (Publication)
- [ ] APIs TikTok/Instagram/YouTube
- [ ] Publishers
- [ ] Planning automatique
- [ ] Analytics

---

*Dernière mise à jour : 2026-02-15*
