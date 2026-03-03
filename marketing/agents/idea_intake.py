"""
IdeaIntakeAgent — Récupère des idées et crée des VideoJobs.

Sources supportées:
- Fichier texte/JSON (dossier d'idées)
- Base de données (VideoScript existants)
- Input direct (prompt)

Règles:
- 3-10 idées/jour
- Déduplication (pas de thème répété en 30 jours)
- Priorisation par pilier de contenu
"""

from django.utils import timezone
from datetime import timedelta
from .base import BaseAgent, AgentResult


class IdeaIntakeAgent(BaseAgent):
    name = "IdeaIntakeAgent"
    
    def execute(self, job) -> AgentResult:
        """
        Pour un job existant: vérifie la validité du thème.
        Pour batch: crée des jobs à partir de scripts en bibliothèque.
        """
        # Vérifier déduplication
        from marketing.models_extended import VideoProductionJob
        
        recent_themes = VideoProductionJob.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).exclude(id=job.id).values_list('theme', flat=True)
        
        # Simple check: thème pas déjà utilisé
        theme_lower = job.theme.lower().strip()
        duplicates = [t for t in recent_themes if t.lower().strip() == theme_lower]
        
        if duplicates:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=f"Thème '{job.theme}' déjà utilisé dans les 30 derniers jours",
                errors=["duplicate_theme"]
            )
        
        # Marquer le job comme validé
        job.status = 'script_pending'
        job.save(update_fields=['status'])
        
        return AgentResult(
            success=True,
            agent_name=self.name,
            message=f"Thème validé: {job.theme}",
            data={"job_id": job.id, "theme": job.theme}
        )
    
    def create_jobs_from_scripts(self, count: int = 5, pillar: str = None):
        """
        Crée des VideoJobs à partir des scripts en bibliothèque.
        Sélectionne les moins utilisés.
        """
        from marketing.models_extended import VideoScript, VideoProductionJob
        
        scripts = VideoScript.objects.all().order_by('usage_count')
        
        if pillar:
            scripts = scripts.filter(theme=pillar)
        
        scripts = scripts[:count]
        created = []
        
        for script in scripts:
            job = VideoProductionJob.objects.create(
                title=script.title,
                theme=f"{script.code} - {script.title}",
                status='draft',
                script_text=self._format_script(script),
                config={
                    'script_code': script.code,
                    'duration_min': script.duration_min,
                    'duration_max': script.duration_max,
                    'platform': script.platform,
                }
            )
            script.increment_usage()
            created.append(job.id)
        
        return created
    
    def _format_script(self, script) -> str:
        """Formate un VideoScript en texte pour le job."""
        parts = script.get_full_script()
        lines = []
        for section, data in parts.items():
            lines.append(f"[{data['timing']}] {section.upper()}: {data['text']}")
        return "\n".join(lines)
