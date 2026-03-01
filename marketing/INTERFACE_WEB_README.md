# Interface Web Production Vidéo IA

## 🎯 Architecture Scalable & Agnostique

Interface complète pour gérer la production vidéo IA **sans hardcode**, extensible à tous providers et modes.

---

## 📦 Composants

### Models (`models_extended.py`)
- **`VideoProjectTemplate`** : Templates réutilisables (durée, structure, config)
- **`VideoProductionJob`** : Job principal orchestration bout-en-bout
- **`SegmentAsset`** : Assets de référence (images/vidéos pour image-to-video)
- **`VideoSegmentGeneration`** : Génération individuelle d'un segment

### Forms (`forms.py`)
- **`VideoProductionJobForm`** : Création job (wizard étape 1)
- **`BulkSegmentConfigForm`** : Config tous segments (wizard étape 2)
- **`SegmentAssetUploadForm`** : Upload assets (image-to-video)
- **`QuickVideoForm`** : Génération rapide one-shot

### Views (`views.py`)
- **`VideoProductionDashboardView`** : Dashboard principal (liste jobs, stats)
- **`VideoJobCreateView`** : Créer job (étape 1)
- **`VideoJobConfigureSegmentsView`** : Config segments (étape 2)
- **`VideoJobDetailView`** : Monitoring temps réel
- **`quick_video_view`** : Génération rapide
- **API endpoints** : Polling status JSON, retry segments

### Admin (`admin.py`)
- Interface admin Django customisée
- Badges colorés, progress bars, actions en masse
- Inline editing segments/assets

---

## 🚀 Intégration

### 1. Ajouter routes dans `latigue/urls.py`

```python
from django.urls import path, include

urlpatterns = [
    # ... autres routes
    path('marketing/', include('marketing.urls')),
]
```

### 2. Créer migrations

```bash
python manage.py makemigrations marketing
python manage.py migrate marketing
```

### 3. Créer superuser (si pas déjà fait)

```bash
python manage.py createsuperuser
```

### 4. Créer un template par défaut (via admin ou shell)

```python
from marketing.models_extended import VideoProjectTemplate, ContentPillar

template = VideoProjectTemplate.objects.create(
    name="Reels 30s Standard",
    description="Format standard TikTok/Reels 30 secondes",
    pillar=ContentPillar.TIPS,
    segments_count=6,
    segment_duration=5,
    default_config={
        'provider': 'luma',
        'mode': 'text_to_video',
        'aspect_ratio': '9:16',
    }
)
```

---

## 🎨 Workflows Supportés

### Mode 1 : Text-to-Video (actuel)

```
1. Créer job → thème "Django tips"
2. Configurer segments → 6 prompts texte
3. Lancer génération → Luma génère vidéos from scratch
4. Assemblage → Vidéo finale 30s
```

### Mode 2 : Image-to-Video (nouveau)

```
1. Créer job → thème "Python code walkthrough"
2. Upload screenshots VS Code pour chaque segment
3. Prompts animation → "Curseur tape le code ligne par ligne"
4. Lancer génération → Luma anime les screenshots
5. Assemblage → Vidéo finale ultra cohérente
```

### Mode 3 : Hybrid (avancé)

```
Segments 1-2 : Text-to-video (intro générique)
Segments 3-5 : Image-to-video (démo code)
Segment 6 : Text-to-video (outro)
```

---

## 📡 URLs Disponibles

```
/marketing/                          → Dashboard
/marketing/job/create/               → Créer job (wizard)
/marketing/job/<id>/configure/       → Config segments
/marketing/job/<id>/                 → Détail/monitoring
/marketing/job/<id>/generate/        → Lancer génération
/marketing/quick/                    → Génération rapide

# API (AJAX polling)
/marketing/api/job/<id>/status/      → Status JSON temps réel
/marketing/api/job/<id>/segment/<n>/retry/ → Retry segment
```

---

## 🎯 Templates HTML à Créer

Créer dans `marketing/templates/marketing/` :

### `base_marketing.html`
```html
{% extends "base.html" %}
{% block extra_css %}
<style>
.status-badge { padding: 5px 10px; border-radius: 5px; color: white; }
.progress-bar { background: #e9ecef; border-radius: 3px; overflow: hidden; }
</style>
{% endblock %}
```

### `dashboard.html`
```html
{% extends "marketing/base_marketing.html" %}

{% block content %}
<h1>📊 Production Vidéo Dashboard</h1>

<div class="stats">
    <div class="stat">Total jobs: {{ stats.total_jobs }}</div>
    <div class="stat">Terminés: {{ stats.completed }}</div>
    <div class="stat">En cours: {{ stats.in_progress }}</div>
    <div class="stat">Coût total: ${{ stats.total_cost }}</div>
</div>

<a href="{% url 'marketing:job_create' %}" class="btn btn-primary">➕ Nouveau Job</a>
<a href="{% url 'marketing:quick_video' %}" class="btn btn-success">⚡ Génération Rapide</a>

<table class="table">
    <thead>
        <tr>
            <th>Titre</th>
            <th>Status</th>
            <th>Template</th>
            <th>Progression</th>
            <th>Coût</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for job in jobs %}
        <tr>
            <td>{{ job.title }}</td>
            <td>{{ job.get_status_display }}</td>
            <td>{{ job.template.name|default:"-" }}</td>
            <td>{{ job.progress_percent }}%</td>
            <td>${{ job.estimated_cost }}</td>
            <td>
                <a href="{% url 'marketing:job_detail' job.pk %}">Voir</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

### `job_create.html`
```html
{% extends "marketing/base_marketing.html" %}

{% block content %}
<h1>➕ Créer un Job de Production</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-primary">Suivant →</button>
</form>
{% endblock %}
```

### `job_configure_segments.html`
```html
{% extends "marketing/base_marketing.html" %}

{% block content %}
<h1>⚙️ Configuration Segments - {{ object.title }}</h1>

<p>Mode: <strong>{{ mode }}</strong> | Segments: <strong>{{ segments_count }}</strong></p>

<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ segments_form.as_p }}
    <button type="submit" class="btn btn-success">Valider Configuration</button>
</form>
{% endblock %}
```

### `job_detail.html`
```html
{% extends "marketing/base_marketing.html" %}

{% block content %}
<h1>{{ object.title }}</h1>

<div class="job-header">
    <p>Status: {{ object.get_status_display }}</p>
    <p>Progression: {{ progress }}%</p>
    <p>Coût estimé: ${{ object.estimated_cost }} | Actuel: ${{ segments_cost }}</p>
</div>

{% if object.status == 'assets_ready' %}
    <a href="{% url 'marketing:job_generate' object.pk %}" class="btn btn-primary">▶️ Lancer Génération</a>
{% endif %}

<h2>Segments ({{ generations.count }})</h2>
<table class="table">
    <thead>
        <tr>
            <th>#</th>
            <th>Prompt</th>
            <th>Mode</th>
            <th>Provider</th>
            <th>Status</th>
            <th>Progression</th>
            <th>Vidéo</th>
        </tr>
    </thead>
    <tbody>
        {% for gen in generations %}
        <tr>
            <td>{{ gen.segment_index }}</td>
            <td>{{ gen.prompt|truncatewords:10 }}</td>
            <td>{{ gen.get_generation_mode_display }}</td>
            <td>{{ gen.provider }}</td>
            <td>{{ gen.get_status_display }}</td>
            <td>{{ gen.progress_percent }}%</td>
            <td>
                {% if gen.video_url %}
                <a href="{{ gen.video_url }}" target="_blank">🎬 Voir</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<script>
// Polling temps réel
setInterval(() => {
    fetch("{% url 'marketing:api_job_status' object.pk %}")
        .then(res => res.json())
        .then(data => {
            console.log('Status update:', data);
            // TODO: Update UI
        });
}, 5000); // Poll toutes les 5 sec
</script>
{% endblock %}
```

### `quick_video.html`
```html
{% extends "marketing/base_marketing.html" %}

{% block content %}
<h1>⚡ Génération Rapide</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    
    <label>
        <input type="checkbox" name="auto_generate" value="1">
        Lancer génération automatiquement (skip config manuelle)
    </label>
    
    <button type="submit" class="btn btn-success">Créer & Générer</button>
</form>
{% endblock %}
```

---

## 🔧 Prochaines Étapes

### Phase 1 : Backend (fait ✅)
- ✅ Models extensibles
- ✅ Forms dynamiques
- ✅ Views & URLs
- ✅ Admin Django

### Phase 2 : Frontend (à faire)
- [ ] Créer templates HTML
- [ ] Styling Tailwind
- [ ] AJAX polling temps réel
- [ ] Upload drag & drop assets

### Phase 3 : Génération Async (à faire)
- [ ] Celery tasks pour génération segments
- [ ] Queue management
- [ ] Retry automatique échecs
- [ ] Notification fin de job

### Phase 4 : Upgrade Providers (à faire)
- [ ] Implémenter image-to-video dans `luma.py`
- [ ] Ajouter Runway/Pika providers
- [ ] Fallback automatique si échec

---

## 💡 Utilisation

### Workflow Standard

1. **Admin** → Créer templates réutilisables
2. **Dashboard** → Créer job depuis template
3. **Config segments** → Définir prompts (+ upload assets optionnel)
4. **Lancer génération** → Backend génère segments async
5. **Monitoring** → Polling temps réel progression
6. **Résultat** → Vidéo finale assemblée

### Quick Mode

1. **Quick form** → Remplir sujet + params
2. **Auto generate** → Skip config manuelle
3. **Backend** → Script IA + génération auto
4. **Résultat** → Vidéo prête en ~5-10 min

---

## 🎨 Extensibilité

### Ajouter un nouveau provider

1. Créer `marketing/ai/video_providers/newprovider.py`
2. Hériter de `VideoProvider` base class
3. Ajouter dans `VideoProvider.choices`
4. Configurer API key dans `.env`
5. Aucun changement code UI nécessaire ✅

### Ajouter un nouveau mode

1. Ajouter dans `VideoGenerationMode.choices`
2. Implémenter logique dans provider
3. Aucun changement forms/views ✅

---

## 📊 Monitoring Production

- **Dashboard** : Vue d'ensemble tous jobs
- **Job detail** : Progression temps réel segment par segment
- **Admin** : Gestion fine, actions en masse
- **API** : Polling JSON pour intégrations externes

---

**Architecture 100% scalable, 0% hardcode** 🚀
