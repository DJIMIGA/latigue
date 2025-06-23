import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import io
import os


def optimize_image_before_upload(image_file, max_size_mb=5, max_dimension=1920):
    """
    Optimise une image avant upload vers Cloudinary pour respecter les limites
    
    Args:
        image_file: Fichier image à optimiser
        max_size_mb: Taille maximale en MB (défaut: 5MB)
        max_dimension: Dimension maximale en pixels (défaut: 1920px)
    
    Returns:
        bytes: Image optimisée
    """
    try:
        # Ouvrir l'image avec Pillow
        image = Image.open(image_file)
        
        # Convertir en RGB si nécessaire
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Redimensionner si trop grande
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Optimiser la qualité
        output = io.BytesIO()
        quality = 85  # Qualité initiale
        
        while True:
            output.seek(0)
            output.truncate()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            # Vérifier la taille
            size_mb = len(output.getvalue()) / (1024 * 1024)
            
            if size_mb <= max_size_mb or quality <= 60:
                break
            
            quality -= 5
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Erreur lors de l'optimisation: {e}")
        return image_file.read()


def upload_image_to_cloudinary(image_file, folder="general", public_id=None, optimize=True):
    """
    Upload une image vers Cloudinary avec optimisation
    
    Args:
        image_file: Fichier image à uploader
        folder: Dossier dans Cloudinary
        public_id: ID public pour l'image
        optimize: Optimiser l'image avant upload
    
    Returns:
        dict: Résultat de l'upload avec l'URL de l'image
    """
    try:
        # Configuration Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
        )
        
        # Optimiser l'image si demandé
        if optimize:
            optimized_image = optimize_image_before_upload(image_file)
            image_data = optimized_image
        else:
            image_data = image_file
        
        # Upload vers Cloudinary
        result = cloudinary.uploader.upload(
            image_data,
            folder=folder,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            eager=[
                {"width": 800, "height": 600, "crop": "fill", "quality": "auto"},
                {"width": 400, "height": 300, "crop": "fill", "quality": "auto"},
                {"width": 200, "height": 150, "crop": "fill", "quality": "auto"}
            ],
            eager_async=True
        )
        
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'eager': result.get('eager', [])
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def delete_image_from_cloudinary(public_id):
    """
    Supprime une image de Cloudinary
    
    Args:
        public_id: ID public de l'image à supprimer
    
    Returns:
        dict: Résultat de la suppression
    """
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
        )
        
        result = cloudinary.uploader.destroy(public_id)
        
        return {
            'success': True,
            'result': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_cloudinary_url(public_id, transformation=None):
    """
    Génère une URL Cloudinary avec transformations
    
    Args:
        public_id: ID public de l'image
        transformation: Transformations à appliquer (ex: "w_300,h_200,c_fill")
    
    Returns:
        str: URL de l'image avec transformations
    """
    cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
    base_url = f"https://res.cloudinary.com/{cloud_name}/image/upload"
    
    if transformation:
        return f"{base_url}/{transformation}/{public_id}"
    else:
        return f"{base_url}/{public_id}"


def optimize_image_url(url, width=None, height=None, quality="auto", format="auto"):
    """
    Optimise une URL d'image Cloudinary
    
    Args:
        url: URL de l'image Cloudinary
        width: Largeur souhaitée
        height: Hauteur souhaitée
        quality: Qualité de l'image
        format: Format de l'image
    
    Returns:
        str: URL optimisée
    """
    if not url or 'cloudinary.com' not in url:
        return url
    
    # Extraire l'ID public de l'URL
    parts = url.split('/')
    public_id = '/'.join(parts[parts.index('upload') + 1:])
    
    # Construire les transformations
    transformations = []
    
    if width:
        transformations.append(f"w_{width}")
    if height:
        transformations.append(f"h_{height}")
    if quality:
        transformations.append(f"q_{quality}")
    if format:
        transformations.append(f"f_{format}")
    
    transformation_string = ",".join(transformations)
    
    return get_cloudinary_url(public_id, transformation_string)


def get_usage_stats():
    """
    Récupère les statistiques d'usage Cloudinary (si disponible)
    """
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
        )
        
        # Note: Cette fonction nécessite un plan payant pour les statistiques détaillées
        # Pour le plan gratuit, on peut seulement compter les uploads manuellement
        
        return {
            'plan': 'Free',
            'monthly_credits': 25,
            'api_calls_limit': 500,
            'max_image_size': '10 MB',
            'max_image_mp': '25 MP'
        }
        
    except Exception as e:
        return {
            'error': str(e)
        } 