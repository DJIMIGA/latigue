"""
Configuration partagée pour les applications d'idées.
Contient les paramètres communs et les bonnes pratiques.
"""

import os
from django.conf import settings

# Configuration des applications d'idées
IDEES_APPS_CONFIG = {
    'DEFAULT_THEME': {
        'primary_color': 'brand-500',
        'secondary_color': 'accent-500',
        'success_color': 'green-500',
        'warning_color': 'yellow-500',
        'error_color': 'red-500',
    },
    'DEFAULT_TEMPLATE': {
        'extends': 'base.html',
        'block_content': 'content',
        'responsive': True,
        'dark_mode': True,
    },
    'DEFAULT_PERMISSIONS': [
        'idees_apps.view_app',
        'idees_apps.add_app',
        'idees_apps.change_app',
        'idees_apps.delete_app',
    ],
    'MIGRATION_THRESHOLDS': {
        'users': 1000,
        'revenue': 100,  # euros par mois
        'complexity': 'high',
    },
}

def get_app_settings(app_name):
    """
    Retourne les paramètres spécifiques à une application.
    
    Args:
        app_name (str): Nom de l'application
        
    Returns:
        dict: Paramètres de l'application
    """
    app_config = IDEES_APPS_CONFIG.copy()
    
    # Paramètres spécifiques à l'app
    app_specific = {
        'APP_NAME': app_name,
        'APP_LABEL': f'idees_apps.{app_name}',
        'URL_NAMESPACE': app_name,
        'TEMPLATE_NAMESPACE': f'idees_apps/{app_name}',
        'STATIC_NAMESPACE': f'idees_apps/{app_name}',
        'CACHE_PREFIX': f'idees_{app_name}_',
        'SESSION_PREFIX': f'idees_{app_name}_',
    }
    
    app_config.update(app_specific)
    
    # Paramètres d'environnement spécifiques à l'app
    env_prefix = app_name.upper()
    for key in ['DEBUG', 'SECRET_KEY', 'ALLOWED_HOSTS']:
        env_key = f'{env_prefix}_{key}'
        if os.environ.get(env_key):
            app_config[key] = os.environ.get(env_key)
    
    return app_config

def get_app_middleware(app_name):
    """
    Retourne la liste des middlewares recommandés pour une application.
    
    Args:
        app_name (str): Nom de l'application
        
    Returns:
        list: Liste des middlewares
    """
    base_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
    
    # Middleware spécifique à l'app si nécessaire
    app_middleware = []
    
    # Middleware de monitoring si l'app est en production
    if not settings.DEBUG:
        app_middleware.append(f'idees_apps.{app_name}.middleware.MonitoringMiddleware')
    
    return base_middleware + app_middleware

def get_app_context_processors(app_name):
    """
    Retourne les context processors pour une application.
    
    Args:
        app_name (str): Nom de l'application
        
    Returns:
        list: Liste des context processors
    """
    base_processors = [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]
    
    # Context processor spécifique à l'app
    app_processors = [
        f'idees_apps.{app_name}.context_processors.app_settings',
    ]
    
    return base_processors + app_processors

# Configuration des permissions par défaut
DEFAULT_APP_PERMISSIONS = [
    ('idees_apps.view_app', 'Can view application'),
    ('idees_apps.add_app', 'Can add application'),
    ('idees_apps.change_app', 'Can change application'),
    ('idees_apps.delete_app', 'Can delete application'),
]

# Configuration des groupes par défaut
DEFAULT_APP_GROUPS = {
    'app_users': {
        'permissions': ['idees_apps.view_app'],
        'description': 'Utilisateurs de base de l\'application',
    },
    'app_editors': {
        'permissions': ['idees_apps.view_app', 'idees_apps.add_app', 'idees_apps.change_app'],
        'description': 'Éditeurs de l\'application',
    },
    'app_admins': {
        'permissions': ['idees_apps.view_app', 'idees_apps.add_app', 'idees_apps.change_app', 'idees_apps.delete_app'],
        'description': 'Administrateurs de l\'application',
    },
}

# Configuration des métriques de monitoring
MONITORING_CONFIG = {
    'metrics': [
        'users.active',
        'requests.per_minute',
        'response_time.avg',
        'error_rate',
        'revenue.monthly',
    ],
    'alerts': {
        'error_rate_threshold': 0.05,  # 5%
        'response_time_threshold': 2000,  # 2 secondes
        'user_growth_threshold': 0.2,  # 20% par mois
    },
} 