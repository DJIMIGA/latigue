"""
Orchestrateur de génération vidéo.
Lance et gère la génération de tous les segments d'un job.
"""

import os
import time
from django.conf import settings
from ..models_extended import VideoProductionJob, VideoSegmentGeneration
from .video_providers.luma import LumaProvider
from .video_providers.base import VideoGenerationResult


class GenerationOrchestrator:
    """
    Orchestre la génération complète d'un job vidéo.
    
    v1: Synchrone (bloquant)
    v2: Async avec Celery (TODO)
    """
    
    def __init__(self, job: VideoProductionJob):
        self.job = job
        self.provider = self._get_provider()
    
    def _get_provider(self):
        """Initialise le provider selon la config du job"""
        provider_name = self.job.get_config('provider', 'luma')
        
        if provider_name == 'luma':
            api_key = os.environ.get('LUMA_API_KEY')
            if not api_key:
                raise ValueError("LUMA_API_KEY not found in environment")
            return LumaProvider(api_key)
        
        # Ajouter d'autres providers ici
        # elif provider_name == 'runway':
        #     return RunwayProvider(...)
        
        raise ValueError(f"Unknown provider: {provider_name}")
    
    def start_generation(self):
        """
        Lance la génération de tous les segments.
        
        v1: Synchrone - lance tous les segments et attend
        v2: Async - met en queue Celery
        
        Returns:
            bool: True si lancé avec succès
        """
        segments = self.job.generations.filter(status='pending').order_by('segment_index')
        
        if not segments.exists():
            raise ValueError("No pending segments to generate")
        
        # Update job status
        self.job.status = VideoProductionJob.Status.VIDEO_PENDING
        self.job.current_step = f"Génération de {segments.count()} segments..."
        self.job.save()
        
        # Lancer tous les segments
        for segment in segments:
            self._generate_segment(segment)
        
        return True
    
    def _generate_segment(self, segment: VideoSegmentGeneration):
        """
        Génère un segment vidéo.
        
        v1: Appel API synchrone
        v2: Task Celery async
        """
        try:
            # Update status
            segment.status = VideoSegmentGeneration.Status.PROCESSING
            segment.save()
            
            # Skip les segments uploadés (pas besoin de génération IA)
            if segment.source_type == 'uploaded_clip' and segment.uploaded_clip:
                segment.status = VideoSegmentGeneration.Status.COMPLETED
                segment.save()
                print(f"✓ Segment {segment.segment_index} = clip uploadé, skip IA")
                return
            
            # Utiliser le prompt enrichi (cohérence personnage/scène)
            enriched_prompt = segment.get_enriched_prompt()
            
            # Appel provider
            result = self.provider.generate_clip(
                prompt=enriched_prompt,
                duration=segment.duration,
                aspect_ratio=segment.aspect_ratio,
            )
            
            if result.status == "failed":
                segment.status = VideoSegmentGeneration.Status.FAILED
                segment.error_message = result.error_message
                segment.save()
                return
            
            # Sauvegarder job_id
            segment.provider_job_id = result.job_id
            segment.save()
            
            # Log
            print(f"✓ Segment {segment.segment_index} lancé: {result.job_id}")
            
        except Exception as e:
            segment.status = VideoSegmentGeneration.Status.FAILED
            segment.error_message = str(e)
            segment.save()
            print(f"✗ Erreur segment {segment.segment_index}: {e}")
    
    def poll_status(self):
        """
        Vérifie le status de tous les segments en cours.
        À appeler périodiquement (cron ou Celery beat).
        
        Returns:
            dict: Stats (pending, processing, completed, failed)
        """
        segments = self.job.generations.filter(
            status__in=[
                VideoSegmentGeneration.Status.PROCESSING,
                VideoSegmentGeneration.Status.PENDING
            ]
        )
        
        stats = {
            'total': segments.count(),
            'completed': 0,
            'failed': 0,
            'processing': 0
        }
        
        for segment in segments:
            if not segment.provider_job_id:
                continue
            
            try:
                result = self.provider.get_status(segment.provider_job_id)
                
                if result.status == "completed":
                    segment.status = VideoSegmentGeneration.Status.COMPLETED
                    segment.video_url = result.video_url
                    segment.cost = self.provider.estimate_cost(segment.duration)
                    segment.save()
                    stats['completed'] += 1
                    print(f"✓ Segment {segment.segment_index} terminé: {result.video_url}")
                
                elif result.status == "failed":
                    segment.status = VideoSegmentGeneration.Status.FAILED
                    segment.error_message = result.error_message
                    segment.save()
                    stats['failed'] += 1
                    print(f"✗ Segment {segment.segment_index} échoué: {result.error_message}")
                
                else:
                    stats['processing'] += 1
                
            except Exception as e:
                print(f"⚠ Erreur polling segment {segment.segment_index}: {e}")
                stats['failed'] += 1
        
        # Update job status si tout est terminé
        self._update_job_status()
        
        return stats
    
    def _update_job_status(self):
        """Met à jour le status global du job selon l'état des segments"""
        total = self.job.generations.count()
        completed = self.job.generations.filter(
            status=VideoSegmentGeneration.Status.COMPLETED
        ).count()
        failed = self.job.generations.filter(
            status=VideoSegmentGeneration.Status.FAILED
        ).count()
        
        if completed == total:
            self.job.status = VideoProductionJob.Status.COMPLETED
            self.job.current_step = "✅ Génération terminée"
        elif failed > 0 and (completed + failed) == total:
            self.job.status = VideoProductionJob.Status.FAILED
            self.job.current_step = f"❌ {failed} segment(s) échoué(s)"
        else:
            self.job.status = VideoProductionJob.Status.VIDEO_PENDING
            self.job.current_step = f"⏳ {completed}/{total} segments générés"
        
        self.job.save()
    
    def wait_for_completion(self, max_wait: int = 600, poll_interval: int = 10):
        """
        Attend que tous les segments soient terminés (helper pour tests/debug).
        
        Args:
            max_wait: Temps max d'attente en secondes (défaut: 10min)
            poll_interval: Intervalle entre chaque check (défaut: 10s)
        
        Returns:
            bool: True si tous terminés, False si timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            stats = self.poll_status()
            
            if stats['total'] == stats['completed'] + stats['failed']:
                return True
            
            time.sleep(poll_interval)
        
        return False  # Timeout
