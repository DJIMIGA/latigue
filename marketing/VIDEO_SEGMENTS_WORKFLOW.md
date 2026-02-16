# 🎬 Workflow Génération Vidéo par Segments

## Architecture

**Nouveau système modulaire et agnostique des providers.**

### Concept

Au lieu de générer une vidéo longue (30-60 sec) d'un coup, on découpe en **segments de 5 secondes** :

```
Vidéo 30 sec = 6 segments de 5 sec assemblés
```

**Avantages :**
- ✅ Meilleure qualité (chaque segment cohérent)
- ✅ Régénération ciblée (juste 1 segment si raté)
- ✅ Contrôle éditorial (tu valides chaque partie)
- ✅ Génération parallèle possible (tous les segments en même temps)
- ✅ Switch provider facilement (config .env)

---

## 🏗️ Architecture Technique

### 1. Provider Abstrait

Tous les providers vidéo (Luma, Runway, Pika, Stability) implémentent la même interface :

```python
class VideoProvider(ABC):
    def generate_clip(prompt, duration) -> VideoGenerationResult
    def get_status(job_id) -> VideoGenerationResult
    def estimate_cost(duration) -> float
```

**Switch provider = changer 1 variable d'env** ⚡

```bash
# .env.production
VIDEO_PROVIDER=luma        # ou runway, pika, stability
VIDEO_PROVIDER_FALLBACK=stability  # backup si échec
```

### 2. Modèles Django

**VideoSegment** : Un segment de 5 secondes
- `text` : Texte à dire
- `prompt` : Prompt pour génération vidéo IA
- `duration` : 5 secondes
- `status` : draft → pending → processing → completed
- `video_url` : URL du clip généré
- `provider` : Provider utilisé (luma, runway, etc.)

**VideoProject** : Projet complet
- Contient N segments
- Status global : script → segments_generating → completed
- Coût total calculé

### 3. Modules

```
marketing/ai/
├── video_providers/
│   ├── base.py          # Interface abstraite
│   ├── luma.py          # Luma AI impl
│   ├── runway.py        # Runway ML impl
│   ├── pika.py          # Pika Labs impl
│   └── stability.py     # Stability AI impl
├── segment_generator.py      # Génère script découpé
├── video_segment_processor.py # Génère les clips
└── video_assembler.py        # Assemble tout
```

---

## 🚀 Workflow Complet

### Pipeline automatique

```
1. Génération script segmenté (Claude/GPT)
   → Script découpé en N segments de 5 sec
   
2. Création projet + segments dans DB
   → VideoProject avec N VideoSegment
   
3. Génération vidéos (provider au choix)
   → Appels API parallèles ou séquentiels
   → Chaque segment = 1 vidéo de 5 sec
   
4. Assemblage final (MoviePy)
   → Concaténation segments
   → Ajout voix-off (ElevenLabs)
   → Ajout sous-titres
   → Export vidéo finale (9:16, 1080p)
```

### Commande CLI

```bash
# Génération complète automatique
python manage.py generate_video_segments \
    --theme "Python list comprehension tips" \
    --pillar tips \
    --duration 30 \
    --provider luma \
    --parallel

# Autres exemples
python manage.py generate_video_segments \
    --theme "Django deployment tutorial" \
    --pillar education \
    --duration 45 \
    --provider runway \
    --no-subtitles

python manage.py generate_video_segments \
    --theme "Mon parcours dev autodidacte" \
    --pillar story \
    --duration 60 \
    --provider stability \
    --output /tmp/ma_video.mp4
```

**Options :**
- `--provider luma|runway|pika|stability` : Provider vidéo
- `--parallel` : Génère tous les segments en parallèle (plus rapide)
- `--no-voiceover` : Sans voix-off
- `--no-subtitles` : Sans sous-titres
- `--output` : Chemin de sortie custom

---

## 🎨 Workflow Hybride (IA + Humain)

**Pour un contrôle éditorial maximal** :

### 1. Génère le script

```python
from marketing.ai.segment_generator import generate_segmented_script

script = generate_segmented_script(
    pillar='tips',
    theme='Python tips',
    total_duration=30
)

# script['segments'] = liste de 6 segments
```

### 2. Crée le projet

```python
from marketing.ai.segment_generator import create_video_project_with_segments

project = create_video_project_with_segments(script)
# → Crée VideoProject + 6 VideoSegment
```

### 3. Interface Django Admin

**URL :** `/admin/marketing/videoproject/{project.id}/change/`

Tu peux :
- ✏️ Éditer chaque segment (texte + prompt)
- ☑️ Décocher les segments à exclure
- 🔄 Changer l'ordre (drag & drop)
- 💾 Sauvegarder

### 4. Génère les vidéos

```python
from marketing.ai.video_segment_processor import VideoSegmentProcessor

processor = VideoSegmentProcessor(project, provider_name='luma')

# Génère tous les segments sélectionnés
processor.generate_all_segments(parallel=True)

# Check progression
progress = processor.check_progress()
# {'completed': 4, 'total': 6, 'progress': 67}
```

### 5. Régénère un segment raté

```python
from marketing.ai.video_segment_processor import regenerate_segment
from marketing.models import VideoSegment

segment = VideoSegment.objects.get(id=123)

# Avec nouveau prompt
regenerate_segment(segment, new_prompt="Better visual description...")
```

### 6. Assemble la vidéo finale

```python
from marketing.ai.video_assembler import VideoAssembler

assembler = VideoAssembler(project)
output = assembler.assemble(
    add_voiceover=True,
    add_subtitles=True
)

print(f"Vidéo finale: {output}")
```

---

## 💰 Coûts par Provider

**Vidéo 30 secondes (6 segments de 5 sec) :**

| Provider  | Prix/segment | Total segments | Script | Voix | **Total** |
|-----------|--------------|----------------|--------|------|-----------|
| Luma      | $0.15        | $0.90          | $0.01  | $0.02| **$0.93** |
| Runway    | $0.25        | $1.50          | $0.01  | $0.02| **$1.53** |
| Pika      | $0.15        | $0.90          | $0.01  | $0.02| **$0.93** |
| Stability | $0.075       | $0.45          | $0.01  | $0.02| **$0.48** |

**Production 100 vidéos/mois :**
- Stability : ~$48/mois (économique)
- Luma/Pika : ~$93/mois (bon équilibre)
- Runway : ~$153/mois (qualité premium)

---

## 🔧 Configuration

### 1. Copie le fichier exemple

```bash
cp .env.video-providers.example .env.production
```

### 2. Configure tes API keys

```bash
# Provider par défaut
VIDEO_PROVIDER=luma

# API Keys
LUMA_API_KEY=luma_xxx
RUNWAY_API_KEY=runway_xxx
PIKA_API_KEY=pika_xxx
STABILITY_API_KEY=sk-xxx

# Autres (déjà configurés)
ANTHROPIC_API_KEY=sk-ant-xxx
ELEVENLABS_API_KEY=elevenlabs_xxx
```

### 3. Teste la config

```python
from marketing.ai.video_providers import list_available_providers

providers = list_available_providers()
# {
#   'luma': {'available': True, 'api_key_configured': True},
#   'runway': {'available': True, 'api_key_configured': False},
#   ...
# }
```

---

## 🎯 Prochaines Étapes

### Phase 1 ✅ TERMINÉ
- [x] Architecture provider abstrait
- [x] Implémentation Luma, Runway, Pika, Stability
- [x] Modèles Django (VideoSegment)
- [x] Générateur de scripts segmentés
- [x] Processeur de segments
- [x] Assembleur vidéo
- [x] Commande CLI

### Phase 2 - Interface Web (prochaine)
- [ ] Dashboard génération temps réel
- [ ] Preview segments avant génération
- [ ] Drag & drop pour réorganiser
- [ ] Interface d'édition inline
- [ ] Progress bar live

### Phase 3 - Optimisations
- [ ] Celery pour génération async
- [ ] Redis pour cache/queue
- [ ] Batch generation (10 vidéos d'un coup)
- [ ] Retry automatique si échec
- [ ] Upload auto MinIO/S3

### Phase 4 - Publication
- [ ] APIs TikTok/Instagram/YouTube
- [ ] Planning automatique
- [ ] Analytics tracking

---

## 📝 Exemples d'usage

### Exemple 1 : Génération rapide

```bash
python manage.py generate_video_segments \
    --theme "5 erreurs Python débutants" \
    --pillar tips \
    --provider luma
```

### Exemple 2 : Contrôle total

```python
# 1. Génère script
script = generate_segmented_script('tips', 'Python tips', 30)

# 2. Crée projet
project = create_video_project_with_segments(script)

# 3. Édite dans l'admin Django
# /admin/marketing/videoproject/{project.id}/change/

# 4. Génère
processor = VideoSegmentProcessor(project, provider_name='luma')
processor.generate_all_segments(parallel=True)

# 5. Assemble
assembler = VideoAssembler(project)
video_path = assembler.assemble()
```

### Exemple 3 : Test différents providers

```python
# Génère 3 versions avec providers différents
providers = ['luma', 'runway', 'stability']

for provider in providers:
    processor = VideoSegmentProcessor(project, provider_name=provider)
    segments = processor.generate_all_segments()
    print(f"{provider}: {len([s for s in segments if s.status == 'completed'])} OK")
```

---

## 🐛 Troubleshooting

### Provider API key manquante

```
ValueError: API key manquante: LUMA_API_KEY
```

**Solution :** Configure la variable d'environnement dans `.env.production`

### Segment failed

```python
# Check les erreurs
segment = VideoSegment.objects.get(id=123)
print(segment.error_message)

# Régénère
regenerate_segment(segment)
```

### Timeout génération

Par défaut, max 5 minutes par segment. Si timeout :
- Vérifie la connexion réseau
- Essaye un autre provider
- Check le status API du provider

---

## 🎓 Ressources

- **Luma AI Docs :** https://docs.lumalabs.ai/
- **Runway API :** https://docs.runwayml.com/
- **Pika API :** https://docs.pika.art/
- **Stability AI :** https://platform.stability.ai/docs/

---

**Version :** 1.0  
**Dernière mise à jour :** 2026-02-16
