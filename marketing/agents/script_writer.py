"""
ScriptWriterAgent — Génère des scripts optimisés format court.

Format performant (Matt Ganzak):
- Hook: 1-2s, claim audacieux ou question provocante
- Problem: pain point reconnaissable immédiatement
- Framework: 3 steps ou 3 bullets max
- Example: preuve concrète
- CTA: une seule action

Guardrails:
- Max 60 secondes au débit naturel
- Niveau lecture ~collège
- Une seule idée par vidéo
- Pas de jargon, pas de tangentes
"""

from django.conf import settings
from .base import BaseAgent, AgentResult


SCRIPT_SYSTEM_PROMPT = """Tu es un expert en création de scripts vidéo court format (TikTok, Reels, Shorts).

Contexte: Tu crées des scripts pour Djimiga Tech, une entreprise de services numériques ciblant:
- France (EUR) : freelances, TPE, PME
- Afrique francophone (FCFA) : commerçants, entrepreneurs

RÈGLES STRICTES:
1. Maximum 60 secondes au débit naturel
2. Niveau de lecture simple, direct
3. UNE seule idée par vidéo
4. Pas de jargon technique inutile
5. Chaque phrase apporte de la valeur

FORMAT DE SORTIE (JSON):
{
  "hook": {"text": "...", "duration": 2, "timing": "0-2s"},
  "problem": {"text": "...", "duration": 5, "timing": "2-7s"},
  "framework": {"text": "...", "duration": 12, "timing": "7-19s"},
  "example": {"text": "...", "duration": 8, "timing": "19-27s"},
  "cta": {"text": "...", "duration": 3, "timing": "27-30s"},
  "total_duration": 30,
  "voiceover_text": "Texte complet pour la voix-off...",
  "visual_directions": ["Description visuelle segment 1", "..."]
}
"""


class ScriptWriterAgent(BaseAgent):
    name = "ScriptWriterAgent"
    
    def can_run(self, job) -> bool:
        return job.status in ('draft', 'script_pending')
    
    def execute(self, job) -> AgentResult:
        """
        Génère un script pour le job.
        Si le job a déjà un script_text (depuis VideoScript), l'enrichit.
        Sinon, génère from scratch via LLM.
        """
        
        if job.script_text and len(job.script_text) > 50:
            # Script existant depuis bibliothèque — enrichir
            return self._enrich_existing_script(job)
        else:
            # Générer from scratch
            return self._generate_new_script(job)
    
    def _generate_new_script(self, job) -> AgentResult:
        """Génère un nouveau script via Claude/GPT."""
        try:
            import anthropic
            
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    message="ANTHROPIC_API_KEY non configurée",
                    errors=["missing_api_key"]
                )
            
            client = anthropic.Anthropic(api_key=api_key)
            
            user_prompt = f"""Crée un script vidéo court format sur le thème:
"{job.theme}"

Titre: {job.title}
Durée cible: {job.get_config('duration_max', 30)} secondes
Pilier: {job.get_config('pillar', 'tips')}
"""
            
            response = client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1000,
                system=SCRIPT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            script_text = response.content[0].text
            
            job.script_text = script_text
            job.status = 'script_ready'
            job.script_metadata = {
                'generated_by': 'ScriptWriterAgent',
                'model': 'claude-sonnet-4-5',
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
            }
            job.save(update_fields=['script_text', 'status', 'script_metadata'])
            
            cost = (response.usage.input_tokens * 3 + response.usage.output_tokens * 15) / 1_000_000
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                message=f"Script généré ({len(script_text)} chars)",
                data={"script_length": len(script_text)},
                cost_usd=cost
            )
            
        except Exception as e:
            job.status = 'failed'
            job.error_log = f"ScriptWriterAgent: {e}"
            job.save(update_fields=['status', 'error_log'])
            
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=str(e),
                errors=[str(e)]
            )
    
    def _enrich_existing_script(self, job) -> AgentResult:
        """Le script existe déjà, on le valide et passe au statut suivant."""
        job.status = 'script_ready'
        job.script_metadata = {
            'source': 'video_script_library',
            'enriched': False,
        }
        job.save(update_fields=['status', 'script_metadata'])
        
        return AgentResult(
            success=True,
            agent_name=self.name,
            message=f"Script existant validé ({len(job.script_text)} chars)",
            data={"script_length": len(job.script_text), "source": "library"}
        )
