"""
Provider pour Pika Labs.
Documentation: https://docs.pika.art/
"""

import requests
from .base import VideoProvider, VideoGenerationResult


class PikaProvider(VideoProvider):
    """
    Provider pour Pika Labs.
    
    Pricing: ~$0.03/seconde (~$0.15 pour 5 sec)
    Quality: Très bonne, similaire à Luma
    """
    
    BASE_URL = "https://api.pika.art/v1"
    
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
        """Génère un clip avec Pika"""
        
        payload = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "fps": 24,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/videos",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return VideoGenerationResult(
                job_id=data.get("video_id"),
                status="pending",
                metadata={"provider": "pika", "prompt": prompt}
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id="",
                status="failed",
                error_message=f"Pika API error: {str(e)}"
            )
    
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """Récupère le statut d'une génération Pika"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/videos/{job_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            status_map = {
                "queued": "pending",
                "generating": "processing",
                "completed": "completed",
                "error": "failed"
            }
            
            status = status_map.get(data.get("status"), "pending")
            video_url = data.get("video_url") if status == "completed" else None
            
            return VideoGenerationResult(
                job_id=job_id,
                status=status,
                video_url=video_url,
                progress=self._calculate_progress(data.get("status")),
                error_message=data.get("error_message") if status == "failed" else None,
                metadata=data
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id=job_id,
                status="failed",
                error_message=f"Status check error: {str(e)}"
            )
    
    def estimate_cost(self, duration: int) -> float:
        """Estime le coût (Pika: ~$0.03/sec)"""
        return duration * 0.03
    
    def get_provider_name(self) -> str:
        return "pika"
    
    def _calculate_progress(self, status: str) -> int:
        """Calcule le pourcentage de progression"""
        progress_map = {
            "queued": 10,
            "generating": 50,
            "completed": 100,
            "error": 0
        }
        return progress_map.get(status, 0)
