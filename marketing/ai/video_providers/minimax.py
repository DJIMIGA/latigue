"""
Provider pour MiniMax Hailuo Video Generation.
Documentation: https://platform.minimax.io/docs/guides/video-generation

Pricing (Pay-as-you-go):
- Hailuo-2.3-Fast: $0.19/6s 768P, $0.33/6s 1080P
- Hailuo-2.3:      $0.28/6s 768P, $0.49/6s 1080P
- Hailuo-02:       $0.10/6s 512P, $0.28/6s 768P

Modes supportés:
- Text-to-Video
- Image-to-Video (first_frame_image)
- First-and-Last-Frame Video
- Subject-Reference Video (S2V-01)
"""

import requests
import time
from typing import Optional
from .base import VideoProvider, VideoGenerationResult


class MiniMaxProvider(VideoProvider):
    """
    Provider pour MiniMax Hailuo Video Generation.
    
    Le meilleur rapport qualité/prix pour la génération vidéo IA.
    Supporte 6s et 10s, résolutions 512P/768P/1080P.
    """
    
    BASE_URL = "https://api.minimax.io/v1"
    
    # Modèles disponibles
    MODELS = {
        'hailuo-2.3-fast': 'MiniMax-Hailuo-2.3-Fast',  # Rapide, moins cher
        'hailuo-2.3': 'MiniMax-Hailuo-2.3',             # Qualité standard
        'hailuo-02': 'MiniMax-Hailuo-02',               # Legacy, supporte 512P
        's2v-01': 'S2V-01',                              # Subject reference
    }
    
    # Grille tarifaire (USD)
    PRICING = {
        'MiniMax-Hailuo-2.3-Fast': {
            '768P': {6: 0.19, 10: 0.32},
            '1080P': {6: 0.33},
        },
        'MiniMax-Hailuo-2.3': {
            '768P': {6: 0.28, 10: 0.56},
            '1080P': {6: 0.49},
        },
        'MiniMax-Hailuo-02': {
            '512P': {6: 0.10, 10: 0.15},
            '768P': {6: 0.28, 10: 0.56},
            '1080P': {6: 0.49},
        },
    }
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Config par défaut
        self.default_model = kwargs.get('model', 'MiniMax-Hailuo-2.3-Fast')
        self.default_resolution = kwargs.get('resolution', '768P')
        self.default_duration = kwargs.get('duration', 6)
    
    def generate_clip(
        self, 
        prompt: str, 
        duration: int = 6,
        aspect_ratio: str = "9:16",
        **kwargs
    ) -> VideoGenerationResult:
        """
        Génère un clip avec MiniMax Hailuo.
        
        Args:
            prompt: Description du clip
            duration: 6 ou 10 secondes
            aspect_ratio: ignoré (MiniMax gère via resolution)
            **kwargs:
                model: Modèle MiniMax (défaut: Hailuo-2.3-Fast)
                resolution: 512P, 768P ou 1080P (défaut: 768P)
                first_frame_image: URL image pour mode image-to-video
                last_frame_image: URL image pour mode first-last-frame
                subject_reference: Liste de refs pour mode subject-reference
        """
        
        model = kwargs.get('model', self.default_model)
        resolution = kwargs.get('resolution', self.default_resolution)
        
        # Normaliser le nom du modèle
        if model in self.MODELS:
            model = self.MODELS[model]
        
        payload = {
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "resolution": resolution,
        }
        
        # Mode Image-to-Video
        if 'first_frame_image' in kwargs:
            payload["first_frame_image"] = kwargs['first_frame_image']
        
        # Mode First-and-Last-Frame
        if 'last_frame_image' in kwargs:
            payload["last_frame_image"] = kwargs['last_frame_image']
        
        # Mode Subject Reference
        if 'subject_reference' in kwargs:
            payload["subject_reference"] = kwargs['subject_reference']
            if model not in ('S2V-01',):
                payload["model"] = "S2V-01"
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/video_generation",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            task_id = data.get("task_id")
            
            if not task_id:
                return VideoGenerationResult(
                    job_id="",
                    status="failed",
                    error_message=f"MiniMax API error: no task_id returned. Response: {data}"
                )
            
            return VideoGenerationResult(
                job_id=task_id,
                status="pending",
                metadata={
                    "provider": "minimax",
                    "model": model,
                    "resolution": resolution,
                    "duration": duration,
                    "prompt": prompt,
                }
            )
            
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except Exception:
                    error_detail = e.response.text[:500]
            
            return VideoGenerationResult(
                job_id="",
                status="failed",
                error_message=f"MiniMax API error: {str(e)} {error_detail}"
            )
    
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """
        Récupère le statut d'une génération MiniMax.
        
        MiniMax workflow:
        1. query/video_generation → status + file_id
        2. files/retrieve → download_url
        """
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/query/video_generation",
                headers=self.headers,
                params={"task_id": job_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            status_raw = data.get("status", "Unknown")
            
            # Mapping status MiniMax → notre format
            status_map = {
                "Queueing": "pending",
                "Processing": "processing",
                "Success": "completed",
                "Fail": "failed",
                "Unknown": "pending",
            }
            
            status = status_map.get(status_raw, "pending")
            video_url = None
            file_id = data.get("file_id")
            
            # Si terminé, récupérer l'URL de download
            if status == "completed" and file_id:
                video_url = self._get_download_url(file_id)
            
            return VideoGenerationResult(
                job_id=job_id,
                status=status,
                video_url=video_url,
                progress=self._calculate_progress(status_raw),
                error_message=data.get("error_message") if status == "failed" else None,
                metadata={
                    "raw_status": status_raw,
                    "file_id": file_id,
                    **data,
                }
            )
            
        except requests.exceptions.RequestException as e:
            return VideoGenerationResult(
                job_id=job_id,
                status="failed",
                error_message=f"Status check error: {str(e)}"
            )
    
    def _get_download_url(self, file_id: str) -> Optional[str]:
        """Récupère l'URL de téléchargement depuis un file_id."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/files/retrieve",
                headers=self.headers,
                params={"file_id": file_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("file", {}).get("download_url")
        except Exception:
            return None
    
    def estimate_cost(self, duration: int) -> float:
        """
        Estime le coût pour une durée donnée.
        Utilise le modèle et la résolution par défaut.
        """
        model = self.default_model
        resolution = self.default_resolution
        
        pricing = self.PRICING.get(model, {}).get(resolution, {})
        
        # Trouver le prix le plus proche
        if duration <= 6:
            return pricing.get(6, 0.19)
        else:
            return pricing.get(10, 0.32)
    
    def estimate_cost_detailed(
        self, 
        duration: int, 
        model: str = None, 
        resolution: str = None
    ) -> float:
        """Estimation détaillée avec modèle/résolution spécifiques."""
        model = model or self.default_model
        resolution = resolution or self.default_resolution
        
        if model in self.MODELS:
            model = self.MODELS[model]
        
        pricing = self.PRICING.get(model, {}).get(resolution, {})
        
        if duration <= 6:
            return pricing.get(6, 0.19)
        else:
            return pricing.get(10, 0.32)
    
    def get_provider_name(self) -> str:
        return "minimax"
    
    def _calculate_progress(self, status: str) -> int:
        """Calcule le pourcentage de progression."""
        progress_map = {
            "Queueing": 10,
            "Processing": 50,
            "Success": 100,
            "Fail": 0,
            "Unknown": 5,
        }
        return progress_map.get(status, 0)
    
    def wait_for_completion(
        self, 
        job_id: str, 
        max_wait: int = 300,
        poll_interval: int = 10
    ) -> VideoGenerationResult:
        """
        Attend que la génération soit terminée.
        
        Args:
            job_id: task_id MiniMax
            max_wait: Temps max d'attente en secondes
            poll_interval: Intervalle entre checks (recommandé: 10s par MiniMax)
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get_status(job_id)
            
            if result.status in ["completed", "failed"]:
                return result
            
            time.sleep(poll_interval)
        
        return VideoGenerationResult(
            job_id=job_id,
            status="failed",
            error_message="Timeout waiting for MiniMax video generation"
        )
