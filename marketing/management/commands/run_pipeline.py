"""
Management command pour exécuter le pipeline vidéo.

Usage:
    # Exécuter tout le pipeline sur un job
    python manage.py run_pipeline --job-id 1
    
    # Exécuter un agent spécifique
    python manage.py run_pipeline --job-id 1 --agent script_writer
    
    # Créer des jobs depuis la bibliothèque et lancer
    python manage.py run_pipeline --intake --count 3
    
    # Lancer tous les jobs en attente
    python manage.py run_pipeline --pending
"""

from django.core.management.base import BaseCommand
from marketing.agents import (
    IdeaIntakeAgent,
    ScriptWriterAgent, 
    VoiceAgent,
    VideoAgent,
    QAAgent,
)
from marketing.models_extended import VideoProductionJob


# Pipeline ordonné
PIPELINE = [
    ('idea_intake', IdeaIntakeAgent, ['draft']),
    ('script_writer', ScriptWriterAgent, ['draft', 'script_pending']),
    ('voice', VoiceAgent, ['script_ready']),
    ('video', VideoAgent, ['assets_ready', 'script_ready']),
    ('qa', QAAgent, ['video_ready']),
]


class Command(BaseCommand):
    help = 'Exécute le pipeline de production vidéo'
    
    def add_arguments(self, parser):
        parser.add_argument('--job-id', type=int, help='ID du job à traiter')
        parser.add_argument('--agent', type=str, help='Agent spécifique à exécuter')
        parser.add_argument('--intake', action='store_true', help='Créer des jobs depuis bibliothèque')
        parser.add_argument('--count', type=int, default=3, help='Nombre de jobs à créer (avec --intake)')
        parser.add_argument('--pending', action='store_true', help='Traiter tous les jobs en attente')
        parser.add_argument('--dry-run', action='store_true', help='Simulation sans exécution')
    
    def handle(self, *args, **options):
        if options['intake']:
            self._handle_intake(options['count'])
            return
        
        if options['pending']:
            self._handle_pending(options)
            return
        
        if options['job_id']:
            self._handle_job(options['job_id'], options.get('agent'), options.get('dry_run', False))
            return
        
        self.stderr.write("Spécifiez --job-id, --intake, ou --pending")
    
    def _handle_intake(self, count):
        """Crée des jobs depuis la bibliothèque de scripts."""
        agent = IdeaIntakeAgent()
        job_ids = agent.create_jobs_from_scripts(count=count)
        self.stdout.write(self.style.SUCCESS(f"✅ {len(job_ids)} jobs créés: {job_ids}"))
    
    def _handle_pending(self, options):
        """Traite tous les jobs en attente."""
        # Trouver les jobs à chaque étape du pipeline
        for agent_name, agent_class, valid_statuses in PIPELINE:
            if options.get('agent') and options['agent'] != agent_name:
                continue
            
            jobs = VideoProductionJob.objects.filter(status__in=valid_statuses)
            
            if jobs.exists():
                self.stdout.write(f"\n🔄 {agent_name}: {jobs.count()} jobs en attente")
                
                for job in jobs:
                    self._run_agent(agent_class, job, options.get('dry_run', False))
    
    def _handle_job(self, job_id, agent_name, dry_run):
        """Traite un job spécifique."""
        try:
            job = VideoProductionJob.objects.get(id=job_id)
        except VideoProductionJob.DoesNotExist:
            self.stderr.write(f"Job #{job_id} introuvable")
            return
        
        self.stdout.write(f"📋 Job #{job.id}: {job.title} [{job.status}]")
        
        if agent_name:
            # Agent spécifique
            agent_map = {name: cls for name, cls, _ in PIPELINE}
            if agent_name not in agent_map:
                self.stderr.write(f"Agent inconnu: {agent_name}. Dispo: {list(agent_map.keys())}")
                return
            
            self._run_agent(agent_map[agent_name], job, dry_run)
        else:
            # Pipeline complet
            for name, agent_class, valid_statuses in PIPELINE:
                if job.status in valid_statuses:
                    result = self._run_agent(agent_class, job, dry_run)
                    if not result or not result.success:
                        break
                    job.refresh_from_db()
    
    def _run_agent(self, agent_class, job, dry_run=False):
        """Exécute un agent sur un job."""
        agent = agent_class()
        
        if not agent.can_run(job):
            self.stdout.write(f"  ⏭️ {agent.name}: skip (statut incompatible: {job.status})")
            return None
        
        if dry_run:
            self.stdout.write(f"  🔍 {agent.name}: [DRY RUN] would run on job #{job.id}")
            return None
        
        result = agent.run(job)
        
        if result.success:
            self.stdout.write(self.style.SUCCESS(f"  ✅ {result}"))
        else:
            self.stdout.write(self.style.ERROR(f"  ❌ {result}"))
        
        if result.cost_usd > 0:
            self.stdout.write(f"     💰 Coût: ${result.cost_usd:.4f}")
        
        return result
