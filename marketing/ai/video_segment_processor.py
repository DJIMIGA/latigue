"""
Processeur pour générer et assembler les segments vidéo.
"""

import time
import logging
from typing import List, Optional
from pathlib import Path
from django.conf import settings

from marketing.models import VideoSegment, VideoProject
from marketing.ai.video_providers import get_provider, VideoGenerationResult

logger = logging.getLogger(__name__)


class VideoSegmentProcessor:
    """
    Gère la génération et l'assemblage des segments vidéo.
    """
    
    def __init__(self, project: VideoProject, provider_name: Optional[str] = None):
        """
        Args:
            project: Projet vidéo
            provider_name: Provider à utiliser (None = utilise config)
        """
        self.project = project
        self.provider_name = provider_name or getattr(settings, 'VIDEO_PROVIDER', 'luma')
        self.provider = get_provider(self.provider_name)
        
        # Mise à jour du provider utilisé
        if not self.project.video_provider:
            self.project.video_provider = self.provider_name
            self.project.save()
    
    def generate_all_segments(self, parallel: bool = False) -> List[VideoSegment]:
        """
        Génère toutes les vidéos des segments sélectionnés.
        
        Args:
            parallel: Si True, lance toutes les générations en parallèle
                     Si False, attend chaque génération (séquentiel)
        
        Returns:
            Liste des segments mis à jour
        """
        segments = self.project.get_selected_segments()
        
        if not segments.exists():
            logger.warning(f"Aucun segment sélectionné pour le projet {self.project.id}")
            return []
        
        logger.info(f"Génération de {segments.count()} segments avec {self.provider_name}")
        
        self.project.status = 'segments_generating'
        self.project.save()
        
        if parallel:
            return self._generate_parallel(segments)
        else:
            return self._generate_sequential(segments)
    
    def _generate_sequential(self, segments) -> List[VideoSegment]:
        """Génère les segments un par un (attend chaque)"""
        
        results = []
        
        for segment in segments:
            logger.info(f"Génération segment {segment.order}/{segments.count()}")
            
            # Lance la génération
            result = self._start_segment_generation(segment)
            
            if result.status == 'failed':
                logger.error(f"Échec segment {segment.order}: {result.error_message}")
                continue
            
            # Attend la complétion
            final_result = self._wait_for_completion(segment, result.job_id)
            
            results.append(segment)
        
        # Mise à jour statut projet
        if all(seg.status == 'completed' for seg in results):
            self.project.status = 'segments_completed'
        else:
            self.project.status = 'error'
        
        self.project.save()
        
        return results
    
    def _generate_parallel(self, segments) -> List[VideoSegment]:
        """Lance toutes les générations en parallèle puis attend"""
        
        # Lance toutes les générations
        job_ids = {}
        for segment in segments:
            result = self._start_segment_generation(segment)
            if result.status != 'failed':
                job_ids[segment.id] = result.job_id
        
        logger.info(f"{len(job_ids)} segments lancés en parallèle")
        
        # Attend que tous soient terminés
        max_wait = 600  # 10 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check tous les segments
            all_done = True
            
            for segment in segments:
                if segment.id not in job_ids:
                    continue
                
                if segment.status in ['completed', 'failed']:
                    continue
                
                # Check status
                result = self.provider.get_status(job_ids[segment.id])
                self._update_segment_from_result(segment, result)
                
                if result.status not in ['completed', 'failed']:
                    all_done = False
            
            if all_done:
                break
            
            time.sleep(5)  # Check toutes les 5 secondes
        
        # Mise à jour statut projet
        segments = list(segments)  # Refresh
        if all(seg.status == 'completed' for seg in segments):
            self.project.status = 'segments_completed'
        else:
            self.project.status = 'error'
        
        self.project.save()
        
        return segments
    
    def _start_segment_generation(self, segment: VideoSegment) -> VideoGenerationResult:
        """Lance la génération d'un segment"""
        
        segment.status = 'pending'
        segment.provider = self.provider_name
        segment.save()
        
        # Génère la vidéo
        result = self.provider.generate_clip(
            prompt=segment.prompt,
            duration=segment.duration,
            aspect_ratio="9:16"
        )
        
        # Mise à jour segment
        segment.job_id = result.job_id
        segment.status = result.status
        segment.error_message = result.error_message or ''
        segment.save()
        
        return result
    
    def _wait_for_completion(
        self, 
        segment: VideoSegment, 
        job_id: str,
        max_wait: int = 300
    ) -> VideoGenerationResult:
        """Attend qu'un segment soit généré"""
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.provider.get_status(job_id)
            
            # Mise à jour du segment
            self._update_segment_from_result(segment, result)
            
            if result.status in ['completed', 'failed']:
                return result
            
            time.sleep(5)
        
        # Timeout
        segment.status = 'failed'
        segment.error_message = 'Timeout waiting for generation'
        segment.save()
        
        return VideoGenerationResult(
            job_id=job_id,
            status='failed',
            error_message='Timeout'
        )
    
    def _update_segment_from_result(self, segment: VideoSegment, result: VideoGenerationResult):
        """Met à jour un segment depuis un résultat API"""
        
        segment.status = result.status
        segment.progress = result.progress
        segment.error_message = result.error_message or ''
        
        if result.video_url:
            segment.video_url = result.video_url
            # TODO: Download et upload sur MinIO
        
        if result.metadata:
            segment.metadata = result.metadata
        
        # Calcul du coût
        if segment.status == 'completed':
            segment.cost_usd = self.provider.estimate_cost(segment.duration)
        
        segment.save()
    
    def estimate_total_cost(self) -> float:
        """Estime le coût total de génération"""
        segments = self.project.get_selected_segments()
        total_duration = sum(seg.duration for seg in segments)
        return self.provider.estimate_cost(total_duration)
    
    def check_progress(self) -> dict:
        """Retourne la progression globale"""
        segments = self.project.segments.filter(selected=True)
        total = segments.count()
        
        if total == 0:
            return {'progress': 0, 'status': 'no_segments'}
        
        completed = segments.filter(status='completed').count()
        failed = segments.filter(status='failed').count()
        processing = segments.filter(status__in=['pending', 'processing']).count()
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'processing': processing,
            'progress': int((completed / total) * 100),
            'status': self.project.status
        }


def regenerate_segment(segment: VideoSegment, new_prompt: Optional[str] = None) -> VideoSegment:
    """
    Régénère un segment spécifique.
    
    Args:
        segment: Segment à régénérer
        new_prompt: Nouveau prompt (optionnel)
    
    Returns:
        Segment mis à jour
    """
    if new_prompt:
        segment.prompt = new_prompt
        segment.save()
    
    processor = VideoSegmentProcessor(segment.project)
    processor._start_segment_generation(segment)
    result = processor._wait_for_completion(segment, segment.job_id)
    
    return segment
