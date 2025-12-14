from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import io
import os


def optimize_image_before_upload(image_file, max_size_mb=5, max_dimension=1920):
    """
    Optimise une image avant upload vers S3 pour respecter les limites
    
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
