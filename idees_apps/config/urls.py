"""
Configuration centralisée des URLs pour les applications d'idées.
Facilite la gestion et la migration des applications.
"""

from django.urls import path, include
from django.conf import settings

def get_app_urls(app_name):
    """
    Génère automatiquement les URLs pour une application d'idée.
    
    Args:
        app_name (str): Nom de l'application
        
    Returns:
        list: Liste des patterns d'URL
    """
    return [
        path(f'idees/{app_name}/', include(f'idees_apps.{app_name}.urls', namespace=app_name)),
    ]

def get_all_idees_urls():
    """
    Retourne toutes les URLs des applications d'idées.
    
    Returns:
        list: Liste de tous les patterns d'URL
    """
    urls = []
    
    # Liste des applications d'idées (à maintenir manuellement)
    idees_apps = [
        # 'calculateur_budget',
        # 'gestionnaire_taches',
        # 'generateur_mots_de_passe',
        # etc.
    ]
    
    for app_name in idees_apps:
        urls.extend(get_app_urls(app_name))
    
    return urls

# URLs par défaut pour toutes les applications d'idées
default_app_urls = [
    path('', include('idees_apps.dashboard.urls', namespace='idees_dashboard')),
]

# Combinaison des URLs par défaut et des URLs spécifiques
urlpatterns = default_app_urls + get_all_idees_urls()

# Configuration pour la migration
MIGRATION_URL_CONFIG = {
    'redirect_patterns': {
        # 'old_app_name': 'new_app_name',
        # Exemple: 'calculateur_budget': 'budget_calculator',
    },
    'permanent_redirects': [
        # URLs qui doivent être redirigées de manière permanente
    ],
    'temporary_redirects': [
        # URLs qui doivent être redirigées temporairement
    ],
}

def get_migration_urls():
    """
    Génère les URLs de redirection pour la migration.
    
    Returns:
        list: Liste des patterns de redirection
    """
    from django.views.generic.base import RedirectView
    
    redirect_urls = []
    
    for old_app, new_app in MIGRATION_URL_CONFIG['redirect_patterns'].items():
        redirect_urls.append(
            path(f'idees/{old_app}/<path:path>', 
                 RedirectView.as_view(url=f'/idees/{new_app}/%(path)s', permanent=True),
                 name=f'{old_app}_redirect')
        )
    
    return redirect_urls 