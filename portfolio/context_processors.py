"""
Context processors pour rendre des variables disponibles dans tous les templates
"""
from django.conf import settings


def seo_context(request):
    """
    Ajoute des variables SEO dans le contexte de tous les templates
    """
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        'SITE_URL': request.build_absolute_uri('/')[:-1],  # URL du site sans le slash final
    }


