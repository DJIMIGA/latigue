"""
Générateur de scripts vidéo avec Claude/GPT
"""
import os
import json
from anthropic import Anthropic
from openai import OpenAI


class ScriptGenerator:
    """Génère des scripts structurés pour vidéos Reels/TikTok"""
    
    def __init__(self, provider='anthropic'):
        """
        Args:
            provider: 'anthropic' (Claude) ou 'openai' (GPT-4)
        """
        self.provider = provider
        
        if provider == 'anthropic':
            self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            self.model = 'claude-sonnet-4-5-20250929'
        elif provider == 'openai':
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = 'gpt-4o'
        else:
            raise ValueError(f"Provider '{provider}' non supporté")
    
    def create(self, pillar: str, theme: str, duration: int = 45) -> dict:
        """
        Génère un script complet pour une vidéo
        
        Args:
            pillar: Pilier de contenu ('education', 'demo', 'story', 'tips')
            theme: Thème de la vidéo
            duration: Durée cible en secondes (défaut: 45s)
        
        Returns:
            {
                'script': {...},  # Structure du script
                'caption': str,   # Légende pour le post
                'hashtags': str   # Hashtags SEO
            }
        """
        prompt = self._build_prompt(pillar, theme, duration)
        
        if self.provider == 'anthropic':
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.content[0].text
        
        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content
        
        # Parser le JSON retourné
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback: extraire JSON du texte
            import re
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("Impossible de parser la réponse JSON")
        
        return data
    
    def _build_prompt(self, pillar: str, theme: str, duration: int) -> str:
        """Construit le prompt pour l'IA"""
        
        pillar_descriptions = {
            'education': "Éducation / Partage de savoir (commerce, entrepreneuriat, culture tech)",
            'demo': "Démo BoliBana Stock (app de gestion de stock pour primeurs)",
            'story': "Storytelling / Parcours (primeur → développeur)",
            'tips': "Tips Dev & Tech (Python, Django, IA, prompt engineering)"
        }
        
        templates = {
            'education': "Hook problème/curiosité → Explication claire → Exemple concret → CTA",
            'demo': "Hook douleur → Avant/Après → Démo rapide feature → CTA téléchargement",
            'story': "Hook moment pivot → Contexte → Défi → Leçon → CTA inspiration",
            'tips': "Hook astuce → Pourquoi c'est utile → Démo code/technique → CTA save"
        }
        
        persona_target = {
            'education': "Entrepreneur Tech-Curious (25-45 ans, PME, reconversion)",
            'demo': "Primeurs, commerçants, gérants de petits magasins",
            'story': "Apprenti Dev (18-35 ans, reconversion, autodidacte)",
            'tips': "Apprenti Dev / Dev Junior"
        }
        
        description = pillar_descriptions.get(pillar, pillar)
        template = templates.get(pillar, "Hook → Contenu → CTA")
        persona = persona_target.get(pillar, "Public général")
        
        prompt = f"""Tu es un expert en création de contenu viral pour TikTok/Reels.

CONTEXTE:
- **Créateur:** Konimba Djimiga (Bolibana) — "AppBuilder with Prompt & Supervision"
- **Parcours:** Primeur chez Auchan → Développeur Python/Django
- **Pilier de contenu:** {description}
- **Thème:** {theme}
- **Durée cible:** {duration} secondes
- **Public cible:** {persona}

STRUCTURE ATTENDUE:
{template}

CONTRAINTES:
- Ton: Accessible, authentique, motivant (pas de jargon inutile)
- Hook: 3-5 secondes max, captivant
- Contenu: Clair, concret, actionnable
- CTA: Engageant (follow, save, commente, partage)
- Langue: Français

FORMAT DE SORTIE (JSON strict):
{{
  "script": {{
    "hook": {{
      "text": "Texte du hook (voix-off)",
      "duration": 3,
      "visual_prompt": "Description pour génération image/vidéo"
    }},
    "content": [
      {{
        "text": "Segment de contenu",
        "duration": 10,
        "visual_prompt": "Description visuelle"
      }}
    ],
    "cta": {{
      "text": "Call-to-action",
      "duration": 2,
      "visual_prompt": "Description visuelle CTA"
    }}
  }},
  "voiceover": "Texte complet de la voix-off (tout le script d'un coup)",
  "image_prompts": [
    "Prompt DALL-E pour image 1 (style: digital art, vibrant, modern)",
    "Prompt DALL-E pour image 2",
    ...
  ],
  "caption": "Légende courte et engageante pour le post (2-3 lignes)",
  "hashtags": "#AppBuilder #PythonFR #DjangoFR #Reconversion #DevJunior #CodingTikTok #TechFR"
}}

Génère maintenant le script complet en JSON."""
        
        return prompt


# Fonction helper pour tests rapides
def generate_script(pillar: str, theme: str, provider: str = 'anthropic') -> dict:
    """
    Fonction rapide pour générer un script
    
    Usage:
        from marketing.ai.script_generator import generate_script
        result = generate_script('tips', 'automatiser avec Python')
        print(result['caption'])
    """
    generator = ScriptGenerator(provider=provider)
    return generator.create(pillar, theme)


if __name__ == '__main__':
    # Test rapide
    result = generate_script('tips', 'Liste comprehension Python en 30 secondes')
    print(json.dumps(result, indent=2, ensure_ascii=False))
