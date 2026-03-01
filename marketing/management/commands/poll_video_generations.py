"""
Management command pour vérifier le status des générations vidéo en cours.
À appeler périodiquement (cron toutes les 30 secondes ou 1 minute).

Usage: python manage.py poll_video_generations
"""

from django.core.management.base import BaseCommand
from marketing.models_extended import VideoProductionJob, VideoSegmentGeneration
from marketing.ai.generation_orchestrator import GenerationOrchestrator


class Command(BaseCommand):
    help = 'Poll video generation status for all active jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=int,
            help='Poll specific job only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed output',
        )

    def handle(self, *args, **options):
        job_id = options.get('job_id')
        verbose = options.get('verbose', False)
        
        # Jobs à checker
        if job_id:
            jobs = VideoProductionJob.objects.filter(pk=job_id)
        else:
            jobs = VideoProductionJob.objects.filter(
                status=VideoProductionJob.Status.VIDEO_PENDING
            )
        
        if not jobs.exists():
            if verbose:
                self.stdout.write(self.style.WARNING("No jobs to poll"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Polling {jobs.count()} job(s)..."))
        
        total_stats = {
            'jobs_polled': 0,
            'segments_completed': 0,
            'segments_failed': 0,
            'segments_processing': 0,
        }
        
        for job in jobs:
            try:
                orchestrator = GenerationOrchestrator(job)
                stats = orchestrator.poll_status()
                
                total_stats['jobs_polled'] += 1
                total_stats['segments_completed'] += stats.get('completed', 0)
                total_stats['segments_failed'] += stats.get('failed', 0)
                total_stats['segments_processing'] += stats.get('processing', 0)
                
                if verbose:
                    self.stdout.write(
                        f"  Job #{job.pk} ({job.title}): "
                        f"{stats.get('completed', 0)} completed, "
                        f"{stats.get('failed', 0)} failed, "
                        f"{stats.get('processing', 0)} processing"
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error polling job #{job.pk}: {e}")
                )
        
        # Résumé
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Polled {total_stats['jobs_polled']} job(s): "
                f"{total_stats['segments_completed']} completed, "
                f"{total_stats['segments_failed']} failed, "
                f"{total_stats['segments_processing']} processing"
            )
        )
