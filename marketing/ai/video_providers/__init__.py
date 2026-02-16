"""
Factory pour les providers de génération vidéo.
Permet de switcher facilement entre providers via configuration.
"""

from django.conf import settings
from typing import Optional
from .base import VideoProvider, VideoGenerationResult
from .luma import LumaProvider
from .runway import RunwayProvider
from .pika import PikaProvider
from .stability import StabilityProvider


# Registry des providers disponibles
PROVIDERS = {
    'luma': LumaProvider,
    'runway': RunwayProvider,
    'pika': PikaProvider,
    'stability': StabilityProvider,
}


def get_provider(provider_name: Optional[str] = None) -> VideoProvider:
    """
    Factory pour instancier le provider configuré.
    
    Args:
        provider_name: Nom du provider (luma|runway|pika|stability)
                      Si None, utilise VIDEO_PROVIDER depuis settings
    
    Returns:
        Instance du VideoProvider
    
    Raises:
        ValueError: Si provider inconnu ou API key manquante
    
    Example:
        # Utilise le provider par défaut (.env)
        provider = get_provider()
        
        # Force un provider spécifique
        provider = get_provider('runway')
    """
    
    # Récupère le provider depuis settings ou paramètre
    if provider_name is None:
        provider_name = getattr(settings, 'VIDEO_PROVIDER', 'luma')
    
    provider_name = provider_name.lower()
    
    # Vérifie que le provider existe
    if provider_name not in PROVIDERS:
        available = ', '.join(PROVIDERS.keys())
        raise ValueError(
            f"Provider '{provider_name}' inconnu. "
            f"Disponibles: {available}"
        )
    
    # Récupère l'API key correspondante
    api_key_var = f"{provider_name.upper()}_API_KEY"
    api_key = getattr(settings, api_key_var, None)
    
    if not api_key:
        raise ValueError(
            f"API key manquante: {api_key_var} "
            f"Configurez-la dans .env.production"
        )
    
    # Instancie le provider
    provider_class = PROVIDERS[provider_name]
    return provider_class(api_key)


def get_fallback_provider() -> Optional[VideoProvider]:
    """
    Retourne le provider de fallback si configuré.
    
    Returns:
        Instance du provider fallback ou None
    """
    fallback_name = getattr(settings, 'VIDEO_PROVIDER_FALLBACK', None)
    
    if fallback_name:
        try:
            return get_provider(fallback_name)
        except ValueError:
            return None
    
    return None


def list_available_providers() -> dict:
    """
    Liste tous les providers disponibles avec leur statut.
    
    Returns:
        Dict {provider_name: {available: bool, api_key_configured: bool}}
    """
    result = {}
    
    for name in PROVIDERS.keys():
        api_key_var = f"{name.upper()}_API_KEY"
        api_key = getattr(settings, api_key_var, None)
        
        result[name] = {
            'available': True,
            'api_key_configured': bool(api_key),
            'class': PROVIDERS[name].__name__
        }
    
    return result


# Expose les classes principales
__all__ = [
    'VideoProvider',
    'VideoGenerationResult',
    'LumaProvider',
    'RunwayProvider',
    'PikaProvider',
    'StabilityProvider',
    'get_provider',
    'get_fallback_provider',
    'list_available_providers',
]
