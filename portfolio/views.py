from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .forms import ContactForm
from .models import Portfolio, Profile, Experience


# Create your views here.
def portfolio_index(request):
    from services.models import Service
    from formations.models import Formation

    services = Service.objects.filter(category='ia_automation', is_active=True).order_by('price')
    formations = Formation.objects.filter(is_active=True).order_by('price')

    context = {
        'services': services,
        'formations': formations,
    }
    return render(request, "portfolio_index.html", context)


def about(request):
    profile = Profile.get_profile()
    portfolios = Portfolio.objects.all().order_by('order', '-created_at')[:12]
    experiences = Experience.objects.filter(is_active=True).order_by('order', '-created_at')

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            sujet = form.cleaned_data["sujet"]
            message = form.cleaned_data["message"]
            
            # Envoyer l'email
            send_mail(
                f"Nouveau message : {sujet}",
                f"Email: {email}\nSujet: {sujet}\nMessage: {message}",
                email,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            
            messages.success(request, "Votre message a été envoyé avec succès!")
            return redirect("about")
    else:
        form = ContactForm()

    context = {
        "form": form,
        "profile": profile,
        "portfolios": portfolios,
        "experiences": experiences,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "about.html", context)


def brand_kit(request):
    """Page Brand Kit Djimiga Tech — standalone HTML."""
    return render(request, "brand-kit.html")


@require_http_methods(["GET"])
def robots_txt(request):
    """Vue pour servir robots.txt depuis le dossier static"""
    robots_content = """# robots.txt pour bolibana.net / latigue
# Permet aux moteurs de recherche d'indexer le site

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /ckeditor/
Disallow: /staticfiles/

# Sitemap
Sitemap: https://bolibana.net/sitemap.xml
"""
    return HttpResponse(robots_content, content_type="text/plain")
