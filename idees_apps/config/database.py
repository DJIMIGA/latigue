"""
Configuration de base de données pour l'isolation des applications d'idées.
Permet de migrer facilement une application vers sa propre base de données.
"""

import os
from django.conf import settings

def get_app_database_config(app_name):
    """
    Retourne la configuration de base de données pour une application spécifique.
    
    Args:
        app_name (str): Nom de l'application
        
    Returns:
        dict: Configuration de base de données
    """
    
    # Configuration par défaut (base de données principale)
    default_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(settings.BASE_DIR, f'idees_{app_name}.db'),
    }
    
    # Si l'application a sa propre base de données configurée
    app_db_url = os.environ.get(f'{app_name.upper()}_DATABASE_URL')
    if app_db_url:
        import dj_database_url
        return dj_database_url.parse(app_db_url)
    
    # Configuration pour PostgreSQL si disponible
    if os.environ.get(f'{app_name.upper()}_USE_POSTGRES'):
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get(f'{app_name.upper()}_DB_NAME', f'idees_{app_name}'),
            'USER': os.environ.get(f'{app_name.upper()}_DB_USER', 'postgres'),
            'PASSWORD': os.environ.get(f'{app_name.upper()}_DB_PASSWORD', ''),
            'HOST': os.environ.get(f'{app_name.upper()}_DB_HOST', 'localhost'),
            'PORT': os.environ.get(f'{app_name.upper()}_DB_PORT', '5432'),
        }
    
    return default_config

def get_router_config():
    """
    Retourne la configuration du routeur de base de données pour isoler les applications.
    """
    return {
        'idees_apps': {
            'default': 'default',  # Utilise la DB principale par défaut
            'migrated_apps': [],   # Liste des apps migrées vers leur propre DB
        }
    }

class IdeesAppRouter:
    """
    Routeur de base de données pour isoler les applications d'idées.
    """
    
    def db_for_read(self, model, **hints):
        """Détermine quelle base de données utiliser pour la lecture."""
        app_label = model._meta.app_label
        
        # Si l'app est dans idees_apps et a sa propre DB
        if app_label.startswith('idees_apps.'):
            app_name = app_label.split('.')[-1]
            if os.environ.get(f'{app_name.upper()}_USE_OWN_DB'):
                return f'idees_{app_name}'
        
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Détermine quelle base de données utiliser pour l'écriture."""
        app_label = model._meta.app_label
        
        # Si l'app est dans idees_apps et a sa propre DB
        if app_label.startswith('idees_apps.'):
            app_name = app_label.split('.')[-1]
            if os.environ.get(f'{app_name.upper()}_USE_OWN_DB'):
                return f'idees_{app_name}'
        
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Autorise les relations entre objets de la même base de données."""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Détermine où effectuer les migrations."""
        # Migrations vers la DB principale par défaut
        if db == 'default':
            return True
        
        # Migrations vers la DB spécifique de l'app
        if app_label.startswith('idees_apps.'):
            app_name = app_label.split('.')[-1]
            if db == f'idees_{app_name}':
                return True
        
        return False 