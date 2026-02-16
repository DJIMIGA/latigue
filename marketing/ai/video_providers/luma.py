"""
Provider pour Luma AI Dream Machine.
Documentation: https://docs.lumalabs.ai/
"""

import requests
import time
from typing import Optional
from .base import VideoProvider, VideoGenerationResult


class LumaProvider(VideoProvider):
    """
    Provider pour Luma AI Dream Machine.
    
    Pricing: ~$0.03/seconde (~$0.15 pour 5 sec)
    Quality: Très bonne, format vertical natif
    """
    
    BASE_URL = "https://api.lumalabs.ai/v1"
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_clip(
        self, 
        prompt: str, 
        duration: int = 5,
        aspect_ratio: str = "9:16",
        **kwargs
    ) -> VideoGenerationResult:
        """Génère un clip avec Luma AI"""
        
        # Mapping aspect ratio
        aspect_map = {
            "9:16": "vertical",
            "16:9": "horizontal",
            "1:1": "square"
        }
        
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_map.get(aspect_ratio, "vertical"),
            "duration": duration,
            **kwargs  # Permet de passer des params custom Luma
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/generations",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return VideoGenerationResult(
                job_id=data.get("id"),
                status="pending",
                metadata={"provider": "luma", "prompt": prompt}
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id="",
                status="failed",
                error_message=f"Luma API error: {str(e)}"
            )
    
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """Récupère le statut d'une génération Luma"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/generations/{job_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Mapping status Luma → notre format
            status_map = {
                "pending": "pending",
                "processing": "processing",
                "completed": "completed",
                "failed": "failed"
            }
            
            status = status_map.get(data.get("state"), "pending")
            video_url = data.get("assets", {}).get("video") if status == "completed" else None
            
            return VideoGenerationResult(
                job_id=job_id,
                status=status,
                video_url=video_url,
                progress=self._calculate_progress(data.get("state")),
                error_message=data.get("failure_reason") if status == "failed" else None,
                metadata=data
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id=job_id,
                status="failed",
                error_message=f"Status check error: {str(e)}"
            )
    
    def estimate_cost(self, duration: int) -> float:
        """Estime le coût (Luma: ~$0.03/sec)"""
        return duration * 0.03
    
    def get_provider_name(self) -> str:
        return "luma"
    
    def _calculate_progress(self, state: str) -> int:
        """Calcule le pourcentage de progression"""
        progress_map = {
            "pending": 10,
            "processing": 50,
            "completed": 100,
            "failed": 0
        }
        return progress_map.get(state, 0)
    
    def wait_for_completion(
        self, 
        job_id: str, 
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> VideoGenerationResult:
        """
        Attend que la génération soit terminée (helper optionnel).
        
        Args:
            job_id: ID du job
            max_wait: Temps max d'attente en secondes
            poll_interval: Intervalle entre chaque check
        
        Returns:
            VideoGenerationResult final
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get_status(job_id)
            
            if result.status in ["completed", "failed"]:
                return result
            
            time.sleep(poll_interval)
        
        # Timeout
        return VideoGenerationResult(
            job_id=job_id,
            status="failed",
            error_message="Timeout waiting for video generation"
        )
