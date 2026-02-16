"""
Provider pour Stability AI Video (Stable Video Diffusion).
Documentation: https://platform.stability.ai/docs/
"""

import requests
from .base import VideoProvider, VideoGenerationResult


class StabilityProvider(VideoProvider):
    """
    Provider pour Stability AI Video.
    
    Pricing: ~$0.01-0.02/seconde (~$0.05-0.10 pour 5 sec)
    Quality: Bonne (moins réaliste que Runway/Luma)
    Avantage: Le moins cher
    """
    
    BASE_URL = "https://api.stability.ai/v2beta"
    
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
        """Génère un clip avec Stability Video"""
        
        # Stability utilise image → video (text-to-image puis image-to-video)
        # Pour simplifier, on utilise text-to-video direct si disponible
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7,
            "motion_bucket_id": 127,  # Intensité du mouvement
            "seed": 0,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/image-to-video",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return VideoGenerationResult(
                job_id=data.get("id"),
                status="pending",
                metadata={"provider": "stability", "prompt": prompt}
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id="",
                status="failed",
                error_message=f"Stability API error: {str(e)}"
            )
    
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """Récupère le statut d'une génération Stability"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/results/{job_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Stability renvoie la vidéo directement quand prête
            if response.status_code == 200:
                # Sauvegarder temporairement ou uploader
                video_url = f"stability_video_{job_id}.mp4"  # À implémenter
                
                return VideoGenerationResult(
                    job_id=job_id,
                    status="completed",
                    video_url=video_url,
                    progress=100
                )
            else:
                return VideoGenerationResult(
                    job_id=job_id,
                    status="processing",
                    progress=50
                )
            
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 404:
                # Job pas encore prêt
                return VideoGenerationResult(
                    job_id=job_id,
                    status="processing",
                    progress=30
                )
            
            return VideoGenerationResult(
                job_id=job_id,
                status="failed",
                error_message=f"Status check error: {str(e)}"
            )
    
    def estimate_cost(self, duration: int) -> float:
        """Estime le coût (Stability: ~$0.015/sec)"""
        return duration * 0.015
    
    def get_provider_name(self) -> str:
        return "stability"
