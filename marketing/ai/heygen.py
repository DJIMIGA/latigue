"""
Intégration HeyGen pour génération de vidéos avatar (talking head).
Documentation: https://docs.heygen.com/reference/

Workflow:
1. Créer un avatar clone (une fois) → HEYGEN_AVATAR_ID
2. Envoyer audio + avatar_id → vidéo talking head
3. Poll status → download vidéo

Pricing: ~$0.05/seconde (plan Creator)
"""

import requests
import time
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class HeyGenResult:
    """Résultat d'une opération HeyGen"""
    job_id: str
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class HeyGenProvider:
    """
    Provider pour HeyGen Avatar Video Generation.
    
    Génère des vidéos "talking head" avec un clone de votre visage.
    """
    
    BASE_URL = "https://api.heygen.com"
    
    def __init__(self, api_key: str, avatar_id: str = None):
        self.api_key = api_key
        self.avatar_id = avatar_id
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def generate_talking_video(
        self,
        audio_url: str = None,
        audio_path: str = None,
        text: str = None,
        voice_id: str = None,
        avatar_id: str = None,
        background: str = None,
        aspect_ratio: str = "9:16",
    ) -> HeyGenResult:
        """
        Génère une vidéo avatar parlant.
        
        Modes:
        1. audio_url/audio_path → lip sync sur audio existant
        2. text + voice_id → TTS + lip sync
        
        Args:
            audio_url: URL du fichier audio (.wav/.mp3)
            audio_path: Chemin local du fichier audio (upload d'abord)
            text: Texte à dire (mode TTS)
            voice_id: ID voix ElevenLabs/HeyGen (mode TTS)
            avatar_id: ID avatar (override instance default)
            background: URL ou couleur de fond
            aspect_ratio: "9:16" (portrait) ou "16:9" (paysage)
        """
        avatar_id = avatar_id or self.avatar_id
        
        if not avatar_id:
            return HeyGenResult(
                job_id="",
                status="failed",
                error_message="avatar_id requis. Configurez HEYGEN_AVATAR_ID."
            )
        
        # Construction du payload selon le mode
        if audio_url:
            # Mode audio lip sync
            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url
                    },
                    "background": self._build_background(background)
                }],
                "dimension": self._aspect_to_dimension(aspect_ratio),
            }
        elif text and voice_id:
            # Mode TTS
            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": voice_id
                    },
                    "background": self._build_background(background)
                }],
                "dimension": self._aspect_to_dimension(aspect_ratio),
            }
        else:
            return HeyGenResult(
                job_id="",
                status="failed",
                error_message="Fournir audio_url OU (text + voice_id)"
            )
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/v2/video/generate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            video_id = data.get("data", {}).get("video_id")
            
            if not video_id:
                return HeyGenResult(
                    job_id="",
                    status="failed",
                    error_message=f"No video_id: {data}"
                )
            
            return HeyGenResult(
                job_id=video_id,
                status="pending",
                metadata={"payload": payload, "response": data}
            )
            
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = str(e.response.json())
                except Exception:
                    error_detail = e.response.text[:500]
            
            return HeyGenResult(
                job_id="",
                status="failed",
                error_message=f"HeyGen API error: {e} {error_detail}"
            )
    
    def get_status(self, video_id: str) -> HeyGenResult:
        """Vérifie le statut d'une génération vidéo."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/v1/video_status.get",
                headers=self.headers,
                params={"video_id": video_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            status_raw = data.get("data", {}).get("status", "unknown")
            
            status_map = {
                "pending": "pending",
                "processing": "processing",
                "completed": "completed",
                "failed": "failed",
            }
            
            video_url = data.get("data", {}).get("video_url") if status_raw == "completed" else None
            
            return HeyGenResult(
                job_id=video_id,
                status=status_map.get(status_raw, "pending"),
                video_url=video_url,
                error_message=data.get("data", {}).get("error") if status_raw == "failed" else None,
                metadata=data
            )
            
        except requests.exceptions.RequestException as e:
            return HeyGenResult(
                job_id=video_id,
                status="failed",
                error_message=f"Status check error: {e}"
            )
    
    def list_avatars(self) -> list:
        """Liste les avatars disponibles."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/v2/avatars",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("avatars", [])
        except Exception as e:
            return []
    
    def upload_audio(self, file_path: str) -> Optional[str]:
        """Upload un fichier audio et retourne l'URL."""
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"{self.BASE_URL}/v1/asset",
                    headers={"X-Api-Key": self.api_key},
                    files={"file": f},
                    timeout=60
                )
            response.raise_for_status()
            return response.json().get("data", {}).get("url")
        except Exception as e:
            return None
    
    def wait_for_completion(
        self, 
        video_id: str, 
        max_wait: int = 600,
        poll_interval: int = 15
    ) -> HeyGenResult:
        """Attend la fin de la génération (1-5 min typiquement)."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            result = self.get_status(video_id)
            if result.status in ["completed", "failed"]:
                return result
            time.sleep(poll_interval)
        
        return HeyGenResult(
            job_id=video_id,
            status="failed",
            error_message="Timeout waiting for HeyGen generation"
        )
    
    def _build_background(self, background: Optional[str]) -> dict:
        """Construit l'objet background."""
        if not background:
            return {"type": "color", "value": "#000000"}
        if background.startswith("http"):
            return {"type": "image", "value": background}
        return {"type": "color", "value": background}
    
    def _aspect_to_dimension(self, aspect_ratio: str) -> dict:
        """Convertit aspect ratio en dimensions."""
        dimensions = {
            "9:16": {"width": 1080, "height": 1920},
            "16:9": {"width": 1920, "height": 1080},
            "1:1": {"width": 1080, "height": 1080},
        }
        return dimensions.get(aspect_ratio, dimensions["9:16"])
    
    def estimate_cost(self, duration_seconds: int) -> float:
        """Estime le coût (~$0.05/sec sur plan Creator)."""
        return duration_seconds * 0.05
