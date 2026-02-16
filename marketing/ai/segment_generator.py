"""
Génération de scripts découpés en segments de 5 secondes.
"""

from typing import List, Dict
from django.conf import settings
import anthropic
import openai


def generate_segmented_script(
    pillar: str,
    theme: str,
    total_duration: int = 30,
    segment_duration: int = 5,
    provider: str = 'anthropic'
) -> Dict:
    """
    Génère un script découpé en segments de 5 secondes.
    
    Args:
        pillar: Pilier de contenu (education, demo, story, tips)
        theme: Thème de la vidéo
        total_duration: Durée totale souhaitée (défaut: 30 sec)
        segment_duration: Durée de chaque segment (défaut: 5 sec)
        provider: 'anthropic' (Claude) ou 'openai' (GPT-4)
    
    Returns:
        Dict avec structure:
        {
            "theme": str,
            "total_duration": int,
            "segments": [
                {
                    "order": 1,
                    "duration": 5,
                    "text": "Texte à dire en 5 sec",
                    "prompt": "Prompt pour génération vidéo",
                    "timing": "0-5s"
                },
                ...
            ],
            "voiceover": "Texte complet pour la voix-off",
            "hashtags": [...],
            "caption": "...",
        }
    """
    
    num_segments = total_duration // segment_duration
    
    prompt = _build_prompt(pillar, theme, num_segments, segment_duration)
    
    if provider == 'anthropic':
        result = _generate_with_claude(prompt)
    else:
        result = _generate_with_gpt(prompt)
    
    return result


def _build_prompt(pillar: str, theme: str, num_segments: int, segment_duration: int) -> str:
    """Construit le prompt pour l'IA"""
    
    pillar_context = {
        'education': "Format éducatif, partage de savoir technique",
        'demo': "Démo de projet BoliBana Stock (gestion inventaire restaurant)",
        'story': "Storytelling, parcours personnel, inspiration",
        'tips': "Tips rapides dev/tech, astuces pratiques"
    }
    
    context = pillar_context.get(pillar, "Contenu tech/dev")
    
    return f"""Génère un script pour une vidéo Reels/TikTok de {num_segments * segment_duration} secondes.

Pilier: {pillar} ({context})
Thème: {theme}

Format requis:
- Découpe en {num_segments} segments de {segment_duration} secondes chacun
- Chaque segment doit être cohérent et visuel
- Structure narrative: Hook → Problème/Contexte → Solution/Demo → CTA

Pour CHAQUE segment, fournis:
1. **text**: Le texte à dire (max {segment_duration} secondes de parole)
2. **prompt**: Prompt pour génération vidéo IA (description visuelle du segment)

IMPORTANT pour les prompts vidéo:
- Descriptions visuelles concrètes et cinématographiques
- Éviter les textes/code à l'écran (difficile pour l'IA vidéo)
- Privilégier: visages, gestes, objets, environnements
- Style: "Close-up of...", "Dynamic shot of...", "Cinematic view of..."

Exemple de structure pour une vidéo 30 sec (6 segments):
Segment 1 (Hook): "Vous perdez 2h par jour à cause de cette erreur Python"
Segment 2 (Problème): "Voici pourquoi vos boucles sont si lentes"
Segment 3 (Context): "La plupart des devs ignorent cette technique"
Segment 4 (Solution): "Avec list comprehension, tout change"
Segment 5 (Demo): "Regardez la différence de performance"
Segment 6 (CTA): "Lien en bio pour le tuto complet"

Réponds au format JSON:
{{
    "segments": [
        {{
            "order": 1,
            "duration": {segment_duration},
            "text": "...",
            "prompt": "Close-up of frustrated developer looking at slow code on screen, dramatic lighting",
            "timing": "0-{segment_duration}s"
        }},
        ...
    ],
    "voiceover": "Texte complet de la voix-off (tous les segments assemblés)",
    "hashtags": ["#python", "#dev", "#tips", "#coding"],
    "caption": "Caption Instagram/TikTok engageante avec émojis"
}}"""


def _generate_with_claude(prompt: str) -> Dict:
    """Génère avec Claude (Anthropic)"""
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Parse JSON response
    import json
    content = response.content[0].text
    
    # Extraire le JSON (Claude peut wrapper dans ```json```)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    result = json.loads(content)
    
    return result


def _generate_with_gpt(prompt: str) -> Dict:
    """Génère avec GPT-4 (OpenAI)"""
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un expert en création de contenu viral pour Reels/TikTok. Réponds uniquement en JSON valide."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    import json
    result = json.loads(response.choices[0].message.content)
    
    return result


# Helper pour créer les objets Django
def create_video_project_with_segments(script_data: Dict, script_obj=None) -> 'VideoProject':
    """
    Crée un VideoProject avec ses segments depuis les données générées.
    
    Args:
        script_data: Dict retourné par generate_segmented_script()
        script_obj: ContentScript existant (optionnel)
    
    Returns:
        VideoProject avec segments créés
    """
    from marketing.models import VideoProject, VideoSegment, ContentScript
    
    # Créer ou utiliser le ContentScript
    if script_obj is None:
        script_obj = ContentScript.objects.create(
            pillar='tips',  # À adapter
            theme=script_data.get('theme', 'Video'),
            script_json=script_data,
            hashtags=' '.join(script_data.get('hashtags', [])),
            caption=script_data.get('caption', '')
        )
    
    # Créer le projet
    project = VideoProject.objects.create(
        script=script_obj,
        status='segments_draft',
        duration_seconds=sum(seg['duration'] for seg in script_data['segments'])
    )
    
    # Créer les segments
    for seg_data in script_data['segments']:
        VideoSegment.objects.create(
            project=project,
            order=seg_data['order'],
            text=seg_data['text'],
            prompt=seg_data['prompt'],
            duration=seg_data['duration'],
            status='draft',
            selected=True
        )
    
    return project
