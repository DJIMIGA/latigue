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
    # Optimisation : utiliser only() pour ne récupérer que les champs nécessaires
    # et order_by pour un ordre cohérent
    portfolios = Portfolio.objects.all().order_by('order', '-created_at')[:12]  # Limiter à 12 projets
    profile = Profile.get_profile()  # Récupère ou crée le profil unique
    # Optimisation : order_by pour un ordre cohérent
    experiences = Experience.objects.filter(is_active=True).order_by('order', '-created_at')
    context = {
        "portfolios": portfolios,
        "profile": profile,
        "experiences": experiences,
        'MEDIA_URL': settings.MEDIA_URL}
    return render(request, "portfolio_index.html", context)


def about(request):
    profile = Profile.get_profile()
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
    }
    return render(request, "about.html", context)


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
