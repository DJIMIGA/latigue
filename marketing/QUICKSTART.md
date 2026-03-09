# 🚀 Marketing IA - Quick Start

Guide rapide pour générer ta première vidéo en 5 minutes.

## ✅ Prérequis

1. **App activée dans settings.py**
   ```python
   INSTALLED_APPS = [
       ...
       'marketing',
   ]
   ```

2. **Migrations faites**
   ```bash
   python manage.py makemigrations marketing
   python manage.py migrate
   ```

3. **API keys configurées dans .env**
   ```bash
   OPENAI_API_KEY=sk-...
   ELEVENLABS_API_KEY=...
   MINIO_ENDPOINT=http://minio:9000
   MINIO_ROOT_USER=minioadmin
   MINIO_ROOT_PASSWORD=...
   ```

4. **MinIO démarré**
   ```bash
   # MinIO : service Elestio séparé. En local : lancer MinIO puis définir MINIO_ENDPOINT dans .env
   ```

---

## 🎬 Générer ta première vidéo

### Méthode 1 : CLI (Recommandée)

```bash
python manage.py generate_content \
  --pillar tips \
  --theme "Liste comprehension Python en 30 secondes" \
  --voice Adam \
  --subtitles
```

**Options disponibles :**
- `--pillar` : education | demo | story | tips (requis)
- `--theme` : Thème de la vidéo (requis)
- `--voice` : Adam | Bella | Antoni (défaut: Adam)
- `--subtitles` : Activer sous-titres automatiques
- `--no-upload` : Ne pas uploader sur MinIO
- `--output-dir` : Dossier de sortie custom

### Méthode 2 : Django Shell (Step by step)

```bash
python manage.py shell
```

```python
# 1. Générer le script
from marketing.ai import generate_script
script_data = generate_script('tips', 'Python tips')
print(script_data['caption'])

# 2. Sauvegarder en DB
from marketing.models import ContentScript, VideoProject
script = ContentScript.objects.create(
    pillar='tips',
    theme='Python tips',
    script_json=script_data['script'],
    caption=script_data['caption'],
    hashtags=script_data['hashtags']
)

project = VideoProject.objects.create(script=script)
print(f"✅ Projet #{project.id}")

# 3. Générer les images
from marketing.ai import generate_images_for_script
from marketing.ai.image_generator import download_and_save_images

images = generate_images_for_script(script_data)
image_paths = download_and_save_images(images, '/tmp/video_1', project.id)
print(f"✅ {len(image_paths)} images")

# 4. Générer la voix-off
from marketing.ai import generate_voiceover_from_script
generate_voiceover_from_script(script_data, '/tmp/video_1/audio.mp3', voice='Adam')
print("✅ Audio généré")

# 5. Monter la vidéo
from marketing.ai import create_video
metadata = create_video(
    image_paths,
    '/tmp/video_1/audio.mp3',
    '/tmp/video_1/final.mp4',
    with_subtitles=True
)
print(f"✅ Vidéo : {metadata['duration']}s, {metadata['file_size_mb']}MB")

# 6. Upload sur MinIO
from marketing.storage import upload_video
url = upload_video('/tmp/video_1/final.mp4', project.id)
print(f"✅ URL : {url}")

project.video_url = url
project.status = 'video'
project.save()
```

### Méthode 3 : Python Script

Créer `generate_video.py` :

```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'latigue.settings')
django.setup()

from marketing.ai import generate_script, generate_images_for_script, generate_voiceover_from_script, create_video
from marketing.ai.image_generator import download_and_save_images
from marketing.storage import upload_video
from marketing.models import ContentScript, VideoProject

# Paramètres
PILLAR = 'tips'
THEME = 'Python tips'
VOICE = 'Adam'
OUTPUT_DIR = '/tmp/my_video'

# 1. Script
script_data = generate_script(PILLAR, THEME)
script = ContentScript.objects.create(
    pillar=PILLAR,
    theme=THEME,
    script_json=script_data['script'],
    caption=script_data['caption'],
    hashtags=script_data['hashtags']
)

project = VideoProject.objects.create(script=script)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Images
images = generate_images_for_script(script_data)
image_paths = download_and_save_images(images, OUTPUT_DIR, project.id)

# 3. Audio
audio_path = f'{OUTPUT_DIR}/audio.mp3'
generate_voiceover_from_script(script_data, audio_path, voice=VOICE)

# 4. Vidéo
video_path = f'{OUTPUT_DIR}/final.mp4'
metadata = create_video(image_paths, audio_path, video_path, with_subtitles=True)

# 5. Upload
url = upload_video(video_path, project.id)
project.video_url = url
project.status = 'video'
project.save()

print(f"✅ Vidéo générée : {url}")
```

Exécuter :
```bash
python generate_video.py
```

---

## 📊 Accéder à l'Admin

URL : `http://localhost:8000/admin/marketing/`

Sections :
- **Scripts de contenu** : Voir tous les scripts générés
- **Projets vidéo** : Suivre la production (statut, assets)
- **Publications** : Planifier/analyser (Phase 3)

---

## 🎨 Personnaliser les voix

### Lister les voix disponibles

```python
from marketing.ai.tts_generator import list_available_voices

voices = list_available_voices()
print(f"Voix disponibles : {', '.join(voices)}")
```

### Voix recommandées (ElevenLabs)

- **Adam** : Masculine, claire, professionnelle
- **Bella** : Féminine, douce, narrative
- **Antoni** : Masculine, profonde, sérieuse
- **Elli** : Féminine, jeune, dynamique
- **Josh** : Masculine, énergique, conversationnelle

Pour cloner ta propre voix : https://elevenlabs.io/app/voice-lab

---

## 🎬 Exemples de commandes

### Vidéo éducation (sans sous-titres)

```bash
python manage.py generate_content \
  --pillar education \
  --theme "Automatiser son business avec Python" \
  --voice Bella
```

### Vidéo tips (avec sous-titres)

```bash
python manage.py generate_content \
  --pillar tips \
  --theme "3 astuces Django que tu ne connais pas" \
  --voice Josh \
  --subtitles
```

### Vidéo storytelling

```bash
python manage.py generate_content \
  --pillar story \
  --theme "Comment je suis passé de primeur à développeur" \
  --voice Adam \
  --subtitles
```

### Démo Djimiga Tech Stock

```bash
python manage.py generate_content \
  --pillar demo \
  --theme "Scanner 50 produits en 2 minutes avec Djimiga Tech Stock" \
  --voice Bella
```

### Test local (sans upload MinIO)

```bash
python manage.py generate_content \
  --pillar tips \
  --theme "Python test" \
  --no-upload \
  --output-dir /tmp/test_video
```

---

## 💰 Coûts par vidéo

| Étape | Service | Coût unitaire |
|-------|---------|---------------|
| Script | Claude Sonnet | ~$0.01 |
| Images (x8) | DALL-E 3 | ~$0.32 |
| Voix-off | ElevenLabs | ~$0.02 |
| Montage | MoviePy (local) | Gratuit |
| Stockage | MinIO (VPS) | Gratuit |
| **TOTAL** | | **~$0.35** |

**Pour 100 vidéos/mois : ~$35**

---

## 🆘 Troubleshooting

### "No module named 'openai'"
```bash
pip install -r requirements-marketing.txt
```

### "ELEVENLABS_API_KEY non configurée"
```bash
# Ajouter dans .env.production
ELEVENLABS_API_KEY=your_key_here
```

### "Connection refused" MinIO
```bash
docker ps | grep minio
docker logs latigue_minio
```

### DALL-E 3 "Insufficient quota"
→ Vérifier : https://platform.openai.com/account/usage
→ Ajouter méthode de paiement

### ElevenLabs "Unauthorized"
→ Vérifier : https://elevenlabs.io/app/usage
→ Plan gratuit épuisé ? Upgrade ou attendre le reset

### MoviePy "No such file or directory: 'ffmpeg'"
```bash
# Dans le container Docker
apt-get update && apt-get install -y ffmpeg

# Ou mettre à jour le Dockerfile
RUN apt-get update && apt-get install -y ffmpeg libmagic1
```

### Whisper trop lent / erreur mémoire
→ Désactiver les sous-titres : enlever `--subtitles`
→ Ou utiliser l'API OpenAI au lieu du modèle local (automatique si `openai-whisper` pas installé)

---

## 📚 Documentation complète

- `README.md` — Overview complet du pipeline
- `MINIO_SETUP.md` — Configuration stockage MinIO
- `DEPLOY_MARKETING_IA.md` — Checklist déploiement VPS
- `memory/strategie-marketing-ia.md` — Stratégie marketing complète
- `memory/persona-marketing.md` — Personas et piliers de contenu

---

## 🚀 Prochaines étapes

1. **Générer 5-10 vidéos test** pour valider le pipeline
2. **Ajuster les prompts** dans `ai/script_generator.py` si besoin
3. **Phase 2 : Automatisation** (Celery + batch production)
4. **Phase 3 : Publication** (APIs TikTok/Instagram/YouTube)

---

*Dernière mise à jour : 2026-02-15*
