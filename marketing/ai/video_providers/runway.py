"""
Provider pour Runway Gen-3.
Documentation: https://docs.runwayml.com/
"""

import requests
from .base import VideoProvider, VideoGenerationResult


class RunwayProvider(VideoProvider):
    """
    Provider pour Runway Gen-3.
    
    Pricing: ~$0.05/seconde (~$0.25 pour 5 sec)
    Quality: Top tier, très réaliste
    """
    
    BASE_URL = "https://api.runwayml.com/v1"
    
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
        """Génère un clip avec Runway Gen-3"""
        
        payload = {
            "prompt": prompt,
            "duration": duration,
            "resolution": "1080p",
            "aspect_ratio": aspect_ratio,
            "model": "gen3",
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/generate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return VideoGenerationResult(
                job_id=data.get("id"),
                status="pending",
                metadata={"provider": "runway", "prompt": prompt}
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id="",
                status="failed",
                error_message=f"Runway API error: {str(e)}"
            )
    
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """Récupère le statut d'une génération Runway"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/tasks/{job_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            status_map = {
                "PENDING": "pending",
                "RUNNING": "processing",
                "SUCCEEDED": "completed",
                "FAILED": "failed"
            }
            
            status = status_map.get(data.get("status"), "pending")
            video_url = data.get("output", [{}])[0].get("url") if status == "completed" else None
            
            return VideoGenerationResult(
                job_id=job_id,
                status=status,
                video_url=video_url,
                progress=data.get("progress", 0),
                error_message=data.get("error") if status == "failed" else None,
                metadata=data
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id=job_id,
                status="failed",
                error_message=f"Status check error: {str(e)}"
            )
    
    def estimate_cost(self, duration: int) -> float:
        """Estime le coût (Runway: ~$0.05/sec)"""
        return duration * 0.05
    
    def get_provider_name(self) -> str:
        return "runway"
