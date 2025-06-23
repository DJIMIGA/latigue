from django import template
from django.conf import settings
from ..utils import optimize_image_url

register = template.Library()


@register.filter
def cloudinary_optimize(image_url, size="auto"):
    """
    Optimise une image Cloudinary avec une taille spécifique
    
    Usage: {{ image.url|cloudinary_optimize:"w_300,h_200" }}
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    # Extraire les paramètres de taille
    if size == "auto":
        return image_url
    
    # Appliquer les transformations
    return optimize_image_url(str(image_url), transformation=size)


@register.filter
def cloudinary_thumbnail(image_url, width=300):
    """
    Crée une miniature d'une image Cloudinary
    
    Usage: {{ image.url|cloudinary_thumbnail:300 }}
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    transformation = f"w_{width},h_{width},c_fill,q_auto"
    return optimize_image_url(str(image_url), transformation=transformation)


@register.filter
def cloudinary_resize(image_url, size="800x600"):
    """
    Redimensionne une image Cloudinary
    
    Usage: {{ image.url|cloudinary_resize:"800x600" }}
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    try:
        width, height = size.split('x')
        transformation = f"w_{width},h_{height},c_fill,q_auto"
        return optimize_image_url(str(image_url), transformation=transformation)
    except:
        return image_url


@register.filter
def cloudinary_format(image_url, format="webp"):
    """
    Convertit une image Cloudinary vers un format spécifique
    
    Usage: {{ image.url|cloudinary_format:"webp" }}
    """
    if not image_url or 'cloudinary.com' not in str(image_url):
        return image_url
    
    transformation = f"f_{format},q_auto"
    return optimize_image_url(str(image_url), transformation=transformation)


@register.simple_tag
def cloudinary_url(public_id, transformation=None):
    """
    Génère une URL Cloudinary à partir d'un ID public
    
    Usage: {% cloudinary_url "portfolio/image1" "w_300,h_200" %}
    """
    from ..utils import get_cloudinary_url
    return get_cloudinary_url(public_id, transformation) 