from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import os


class MediaStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers médias (images, vidéos, documents uploadés par les utilisateurs).
    Les URLs sont signées (querystring_auth=True) pour un accès sécurisé.
    """
    location = 'media'  # Dossier racine dans votre bucket S3 pour les médias
    file_overwrite = False  # Ne pas écraser les fichiers existants par défaut
    default_acl = None  # Utilise les ACL par défaut du bucket
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_S3_REGION_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    querystring_auth = True  # Génère des URLs signées (URLs temporaires et sécurisées)
    object_parameters = settings.AWS_S3_OBJECT_PARAMETERS
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    auto_create_bucket = True  # Crée le bucket s'il n'existe pas (utile en dev)
    auto_create_acl = True  # Crée les ACL pour le bucket


class StaticStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers statiques (CSS, JavaScript, images de l'application).
    Ces fichiers sont généralement publics et n'ont pas besoin d'URLs signées.
    Note: Ce projet utilise WhiteNoise pour les fichiers statiques, cette classe est fournie pour référence.
    """
    location = 'static'  # Dossier racine dans votre bucket S3 pour les statiques
    file_overwrite = True  # Écrase les fichiers statiques existants
    default_acl = 'public-read'  # Rend les fichiers statiques publiquement lisibles
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_S3_REGION_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    querystring_auth = False  # Pas besoin d'URLs signées pour les fichiers statiques
    object_parameters = settings.AWS_S3_OBJECT_PARAMETERS
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    auto_create_bucket = True
    auto_create_acl = True


class ProductImageStorage(S3Boto3Storage):
    """
    Stockage spécifique pour les images de produits.
    Les images de produits peuvent nécessiter une gestion unique des noms de fichiers
    pour éviter les conflits et sont généralement des médias (accès sécurisé).
    """
    location = 'media/products'  # Sous-dossier spécifique pour les images de produits
    file_overwrite = False
    default_acl = None
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_S3_REGION_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    querystring_auth = True
    object_parameters = settings.AWS_S3_OBJECT_PARAMETERS
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    auto_create_bucket = True
    auto_create_acl = True

    def _generate_unique_filename(self, filename):
        """Génère un nom de fichier unique en ajoutant un compteur si nécessaire."""
        name_parts = filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) > 1 else ''
        counter = 1
        while self.exists(os.path.join(self.location, f"{base_name}_{counter}.{extension}")):
            counter += 1
        return os.path.join(self.location, f"{base_name}_{counter}.{extension}")

    def get_available_name(self, name, max_length=None):
        """Surcharge pour gérer les noms de fichiers uniques avant de les enregistrer."""
        # Retire le préfixe de la localisation pour vérifier l'existence dans le bon format
        relative_path = os.path.relpath(name, self.location) if name.startswith(self.location) else name
        if self.exists(os.path.join(self.location, relative_path)):
            return self._generate_unique_filename(relative_path)
        return name


class HeroImageStorage(S3Boto3Storage):
    """
    Stockage spécifique pour les images du "hero" (bannière principale).
    Ces images peuvent être écrasées et sont souvent publiques.
    """
    location = 'media/hero'  # Sous-dossier spécifique pour les images hero
    file_overwrite = True  # On autorise l'écrasement pour les images hero
    default_acl = None  # Utilise les paramètres de bucket par défaut
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_S3_REGION_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    querystring_auth = False  # Pas besoin d'authentification pour les images hero
    object_parameters = {
        'CacheControl': 'max-age=86400',  # Cache d'un jour
    }
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    auto_create_bucket = True
    auto_create_acl = False  # Désactive la création automatique des ACLs

