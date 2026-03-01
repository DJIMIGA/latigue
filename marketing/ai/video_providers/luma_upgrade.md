# Upgrade Luma : Image-to-Video

## Modification nécessaire dans luma.py

```python
def generate_clip(
    self, 
    prompt: str, 
    duration: int = 5,
    aspect_ratio: str = "9:16",
    image_url: Optional[str] = None,  # ← AJOUTER
    **kwargs
) -> VideoGenerationResult:
    """Génère un clip avec Luma AI"""
    
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_map.get(aspect_ratio, "vertical"),
        "duration": duration,
    }
    
    # ← AJOUTER support image
    if image_url:
        payload["image_url"] = image_url
    
    payload.update(kwargs)
    
    # ... reste du code identique
```

## Workflow amélioré

### Actuellement (text-to-video)
```
Prompt: "Écran VS Code avec code Python"
→ Luma génère une approximation (qualité variable)
```

### Avec image-to-video
```
1. Génère screenshot VS Code avec DALL-E/Midjourney
   → Image fixe parfaite de ton IDE
   
2. Upload image + prompt animation
   → "Anime ce code : curseur tape, lignes apparaissent"
   
3. Luma anime l'image exacte
   → Résultat cohérent, professionnel, contrôlé
```

## Exemple usage

```bash
# Génération avec image de référence
python manage.py generate_video_segments \
  --theme "Django tips" \
  --pillar tips \
  --provider luma \
  --use-reference-images  # ← option à ajouter
```

## Avantages

✅ **Cohérence** : Pas de surprises, tu vois l'image avant animation
✅ **Qualité** : Vrais screenshots VS Code → look professionnel
✅ **Contrôle** : Choisis exactement le code/terminal/UI
✅ **Branding** : Même style visuel sur toutes tes vidéos

## Coût
- Identique : ~$0.15 par segment 5sec
- +$0.02 si image générée par DALL-E (optionnel)

## Phase d'implémentation

**Phase 1 (actuel)** : Text-to-video pur
**Phase 2 (facile)** : Image-to-video
**Phase 3 (avancé)** : Hybrid (mix des deux selon segment)
