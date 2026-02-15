# 🎬 Marketing IA — Pipeline d'Automatisation Vidéo

App Django pour automatiser la création de contenu vidéo (Reels/TikTok) de bout en bout avec l'IA.

## 🎯 Objectif

Pipeline complet : **Script → Images → Voix-off → Montage → Stockage → Publication**

## 📊 Architecture

```
marketing/
├── models.py              # ContentScript, VideoProject, Publication
├── admin.py               # Interface Django Admin
├── ai/
│   ├── script_generator.py    # Génération scripts (Claude/GPT)
│   ├── image_generator.py     # DALL-E 3
│   ├── tts_generator.py       # ElevenLabs voix-off
│   └── video_editor.py        # MoviePy montage
├── publishers/
│   ├── tiktok.py              # API TikTok
│   ├── instagram.py           # Meta Graph API
│   └── youtube.py             # YouTube Data API
├── management/commands/
│   └── generate_content.py    # CLI: python manage.py generate_content
└── tasks.py               # Celery async tasks
```

## 🚀 Installation

### 1. Ajouter l'app aux settings

```python
# latigue/settings.py
INSTALLED_APPS = [
    ...
    'marketing',
]
```

### 2. Installer les dépendances

```bash
pip install -r requirements-marketing.txt
```

**Note:** FFmpeg doit être installé au niveau système :
```bash
# Debian/Ubuntu
apt-get update && apt-get install -y ffmpeg libmagic1

# macOS
brew install ffmpeg
```

### 3. Variables d'environnement

Ajouter dans `.env.production` :

```bash
# === IA APIs ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# === Stockage MinIO (S3-compatible) ===
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme_production_password
MINIO_BUCKET_VIDEOS=marketing-videos

# === Réseaux sociaux ===
TIKTOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...
YOUTUBE_API_KEY=...

# === Celery (production) ===
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**📦 MinIO Setup :** Voir `MINIO_SETUP.md` pour la configuration complète du stockage.

### 4. Migrations

```bash
python manage.py makemigrations marketing
python manage.py migrate
```

### 5. Créer un superuser (si pas déjà fait)

```bash
python manage.py createsuperuser
```

## 🧪 Tests

### Test 1 : Générer un script

```python
from marketing.ai import generate_script

result = generate_script(
    pillar='tips',
    theme='Liste comprehension Python en 30 secondes'
)

print(result['caption'])
print(result['hashtags'])
print(result['script']['hook']['text'])
```

### Test 2 : Via Django shell

```bash
python manage.py shell
```

```python
from marketing.models import ContentScript
from marketing.ai.script_generator import ScriptGenerator

# Générer un script
generator = ScriptGenerator(provider='anthropic')
data = generator.create('education', 'automatiser son business avec Python')

# Sauvegarder en DB
script = ContentScript.objects.create(
    pillar='education',
    theme='automatiser son business avec Python',
    script_json=data['script'],
    caption=data['caption'],
    hashtags=data['hashtags']
)

print(f"✅ Script créé : ID {script.id}")
```

### Test 3 : Via CLI (quand command sera créée)

```bash
python manage.py generate_content --pillar education --theme "automatiser avec Python"
```

## 💰 Coûts

| Étape | Outil | Coût unitaire |
|-------|-------|---------------|
| Script | Claude Sonnet | ~$0.01 (1k tokens) |
| Images (x8) | DALL-E 3 | ~$0.32 ($0.04/img) |
| Voix-off | ElevenLabs | ~$0.02 (300 chars) |
| Montage | FFmpeg (local) | Gratuit |
| Stockage | S3/R2 | ~$0.001/vidéo |
| **TOTAL** | | **~$0.35/vidéo** |

**Pour 100 vidéos/mois : ~$35**

## 📅 Roadmap

### ✅ Phase 1 : MVP (1 semaine) - EN COURS
- [x] Créer app Django `marketing`
- [x] Models (ContentScript, VideoProject, Publication)
- [x] Admin interface
- [x] Générateur de scripts (Claude/GPT)
- [ ] Générateur d'images (DALL-E 3)
- [ ] TTS voix-off (ElevenLabs)
- [ ] Montage vidéo (MoviePy)
- [ ] Produire 1 vidéo test complète

### 📋 Phase 2 : Automatisation (1 semaine)
- [ ] Celery + Redis (tasks async)
- [ ] Enchaînement automatique des étapes
- [ ] Stockage S3/R2
- [ ] Dashboard admin complet
- [ ] Production batch de 5 vidéos

### 🚀 Phase 3 : Publication (1 semaine)
- [ ] APIs TikTok/Instagram/YouTube
- [ ] Publishers pour chaque plateforme
- [ ] Planning de publication (django-cron)
- [ ] Dashboard analytics (views, likes)

### 🎨 Phase 4 : Optimisation (ongoing)
- [ ] A/B testing (hooks, styles)
- [ ] Amélioration prompts IA
- [ ] Clonage vocal ElevenLabs
- [ ] Templates vidéo multiples
- [ ] Analytics avancées

## 🎨 Admin Interface

Accéder à l'admin Django : `http://localhost:8000/admin/`

Sections disponibles :
- **Scripts de contenu** : Créer, visualiser scripts générés
- **Projets vidéo** : Suivre la production (statut, assets)
- **Publications** : Planifier, analyser performances

## 🔧 Prochaines Étapes Immédiates

1. **Activer l'app dans settings.py**
2. **Faire les migrations**
3. **Configurer les API keys**
4. **Tester génération de script**
5. **Implémenter image_generator.py**
6. **Implémenter tts_generator.py**
7. **Implémenter video_editor.py**
8. **Produire la première vidéo test !**

## 📚 Documentation Complète

Voir : `memory/strategie-marketing-ia.md` pour la stratégie complète et les détails techniques.

---

*Dernière mise à jour : 2026-02-15*
