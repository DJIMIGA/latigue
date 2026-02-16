"""
Base abstract class pour les providers de génération vidéo.
Permet de switcher facilement entre Luma, Runway, Pika, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class VideoGenerationResult:
    """Résultat d'une génération vidéo"""
    job_id: str
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    progress: int = 0  # 0-100
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class VideoProvider(ABC):
    """
    Classe abstraite pour tous les providers de génération vidéo.
    
    Chaque provider doit implémenter ces méthodes.
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def generate_clip(
        self, 
        prompt: str, 
        duration: int = 5,
        aspect_ratio: str = "9:16",
        **kwargs
    ) -> VideoGenerationResult:
        """
        Génère un clip vidéo.
        
        Args:
            prompt: Description du clip à générer
            duration: Durée en secondes (défaut: 5)
            aspect_ratio: Ratio (défaut: 9:16 pour vertical)
            **kwargs: Paramètres spécifiques au provider
        
        Returns:
            VideoGenerationResult avec job_id et status initial
        """
        pass
    
    @abstractmethod
    def get_status(self, job_id: str) -> VideoGenerationResult:
        """
        Récupère le statut d'une génération.
        
        Args:
            job_id: ID du job de génération
        
        Returns:
            VideoGenerationResult avec status et video_url si terminé
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, duration: int) -> float:
        """
        Estime le coût pour une durée donnée.
        
        Args:
            duration: Durée en secondes
        
        Returns:
            Coût estimé en USD
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retourne le nom du provider"""
        pass
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Annule un job en cours (optionnel).
        
        Args:
            job_id: ID du job à annuler
        
        Returns:
            True si annulé avec succès
        """
        return False  # Par défaut, pas d'annulation
    
    def validate_config(self) -> bool:
        """
        Valide la configuration du provider.
        
        Returns:
            True si la config est valide
        """
        return bool(self.api_key)
