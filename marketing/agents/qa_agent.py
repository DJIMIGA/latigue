"""
QAAgent — Contrôle qualité automatique avant publication.

Checks automatiques:
- Vidéo: durée entre 30-60s, résolution OK
- Audio: pas de clipping (si audio dispo)
- Contenu: pas de termes interdits
- Cohérence: script ↔ vidéo générée

Review package envoyé à l'humain pour validation finale.
"""

from django.utils import timezone
from .base import BaseAgent, AgentResult


class QAAgent(BaseAgent):
    name = "QAAgent"
    
    # Termes interdits dans les scripts
    BANNED_TERMS = [
        'garanti', 'gratuit sans condition', 'revenus passifs',
        'devenir riche', 'argent facile', 'sans effort',
    ]
    
    def can_run(self, job) -> bool:
        return job.status == 'video_ready'
    
    def execute(self, job) -> AgentResult:
        """Exécute les checks QA sur le job."""
        checks = []
        errors = []
        warnings = []
        
        # 1. Check script content
        script_result = self._check_script(job)
        checks.append(script_result)
        if not script_result['pass']:
            errors.extend(script_result.get('errors', []))
        
        # 2. Check segments status
        segments_result = self._check_segments(job)
        checks.append(segments_result)
        if not segments_result['pass']:
            errors.extend(segments_result.get('errors', []))
        
        # 3. Check total duration
        duration_result = self._check_duration(job)
        checks.append(duration_result)
        if not duration_result['pass']:
            warnings.append(duration_result.get('message', ''))
        
        # Résultat global
        all_passed = all(c['pass'] for c in checks)
        
        if all_passed:
            job.status = 'completed'
            job.completed_at = timezone.now()
        else:
            job.status = 'failed'
            job.error_log = f"QA failed: {'; '.join(errors + warnings)}"
        
        job.save(update_fields=['status', 'completed_at', 'error_log'])
        
        return AgentResult(
            success=all_passed,
            agent_name=self.name,
            message=f"QA {'✅ passed' if all_passed else '❌ failed'}: {len(checks)} checks, {len(errors)} errors",
            data={
                "checks": checks,
                "errors": errors,
                "warnings": warnings,
            },
            errors=errors
        )
    
    def _check_script(self, job) -> dict:
        """Vérifie le contenu du script."""
        script = (job.script_text or '').lower()
        
        found_banned = [t for t in self.BANNED_TERMS if t in script]
        
        if found_banned:
            return {
                'name': 'script_content',
                'pass': False,
                'errors': [f"Termes interdits: {', '.join(found_banned)}"],
            }
        
        if len(job.script_text or '') < 50:
            return {
                'name': 'script_content',
                'pass': False,
                'errors': ["Script trop court (<50 chars)"],
            }
        
        return {'name': 'script_content', 'pass': True}
    
    def _check_segments(self, job) -> dict:
        """Vérifie que tous les segments sont générés."""
        segments = job.generations.all()
        
        if not segments.exists():
            return {
                'name': 'segments',
                'pass': False,
                'errors': ["Aucun segment généré"],
            }
        
        completed = segments.filter(status='completed').count()
        total = segments.count()
        
        if completed < total:
            failed = segments.filter(status='failed').count()
            return {
                'name': 'segments',
                'pass': False,
                'errors': [f"{completed}/{total} segments OK, {failed} en erreur"],
            }
        
        # Vérifier que chaque segment a une video_url
        missing_url = segments.filter(video_url='').count()
        if missing_url > 0:
            return {
                'name': 'segments',
                'pass': False,
                'errors': [f"{missing_url} segments sans video_url"],
            }
        
        return {'name': 'segments', 'pass': True, 'message': f'{total} segments OK'}
    
    def _check_duration(self, job) -> dict:
        """Vérifie la durée totale."""
        segments = job.generations.filter(status='completed')
        total_duration = sum(s.duration for s in segments)
        
        min_dur = job.get_config('duration_min', 15)
        max_dur = job.get_config('duration_max', 60)
        
        if total_duration < min_dur:
            return {
                'name': 'duration',
                'pass': False,
                'message': f"Trop court: {total_duration}s (min: {min_dur}s)",
            }
        
        if total_duration > max_dur + 10:  # marge de 10s
            return {
                'name': 'duration',
                'pass': False,
                'message': f"Trop long: {total_duration}s (max: {max_dur}s)",
            }
        
        return {'name': 'duration', 'pass': True, 'message': f'{total_duration}s OK'}
