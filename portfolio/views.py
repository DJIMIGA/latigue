from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import ContactForm
from .models import Portfolio
from .utils import upload_image_to_cloudinary, get_usage_stats
from .middleware import CloudinaryUsageMiddleware
import json


# Create your views here.
def portfolio_index(request):
    portfolios = Portfolio.objects.all()
    context = {
        "portfolios": portfolios,
        'MEDIA_URL': settings.MEDIA_URL}
    return render(request, "portfolio_index.html", context)


def about(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]
            
            # Envoyer l'email
            send_mail(
                f"Nouveau message de {name}",
                f"Nom: {name}\nEmail: {email}\nMessage: {message}",
                email,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            
            messages.success(request, "Votre message a été envoyé avec succès!")
            return redirect("about")
    else:
        form = ContactForm()
    
    return render(request, "about.html", {"form": form})


@csrf_exempt
@require_http_methods(["POST"])
def test_cloudinary_upload(request):
    """
    Vue de test pour l'upload Cloudinary
    """
    try:
        # Vérifier si on peut uploader
        middleware = CloudinaryUsageMiddleware(None)
        if not middleware.can_upload():
            return JsonResponse({
                'success': False,
                'error': 'Limite mensuelle d\'uploads atteinte (25/mois)'
            }, status=429)
        
        # Récupérer l'image depuis la requête
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Aucune image fournie'
            }, status=400)
        
        image_file = request.FILES['image']
        
        # Vérifier la taille du fichier (max 10MB pour Cloudinary)
        if image_file.size > 10 * 1024 * 1024:  # 10MB
            return JsonResponse({
                'success': False,
                'error': 'Fichier trop volumineux (max 10MB)'
            }, status=400)
        
        # Upload vers Cloudinary
        result = upload_image_to_cloudinary(
            image_file=image_file,
            folder="test",
            public_id=f"test_{image_file.name}",
            optimize=True
        )
        
        if result['success']:
            # Incrémenter le compteur d'uploads
            middleware.increment_upload_count()
            
            return JsonResponse({
                'success': True,
                'url': result['url'],
                'public_id': result['public_id'],
                'width': result['width'],
                'height': result['height'],
                'format': result['format'],
                'message': 'Image uploadée avec succès vers Cloudinary!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def cloudinary_status(request):
    """
    Vue pour afficher le statut Cloudinary
    """
    usage_stats = get_usage_stats()
    
    # Récupérer l'usage actuel
    middleware = CloudinaryUsageMiddleware(None)
    current_usage = middleware.get_current_usage()
    
    context = {
        'usage_stats': usage_stats,
        'current_usage': current_usage,
        'can_upload': middleware.can_upload(),
        'can_make_api_call': middleware.can_make_api_call(),
        'cloudinary_configured': bool(
            settings.CLOUDINARY_STORAGE.get('CLOUD_NAME') and
            settings.CLOUDINARY_STORAGE.get('API_KEY') and
            settings.CLOUDINARY_STORAGE.get('API_SECRET')
        )
    }
    
    return render(request, "cloudinary_status.html", context)
