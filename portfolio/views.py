from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .forms import ContactForm
from .models import Portfolio, Profile, Experience


# Create your views here.
def portfolio_index(request):
    portfolios = Portfolio.objects.all()
    profile = Profile.get_profile()  # Récupère ou crée le profil unique
    experiences = Experience.objects.filter(is_active=True)  # Récupère les expériences actives
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
            
            # Préparer le contenu de l'email
            email_subject = f"Nouveau message depuis le site : {sujet}"
            email_body = f"""Nouveau message reçu depuis le formulaire de contact :

De : {email}
Sujet : {sujet}

Message :
{message}

---
Ce message a été envoyé depuis le site web de Djimiga Tech.
"""
            
            # Déterminer le destinataire
            recipient_email = getattr(settings, 'CONTACT_EMAIL', None)
            if not recipient_email:
                recipient_email = getattr(settings, 'EMAIL_HOST_USER', None)
            
            if not recipient_email:
                messages.error(request, "Erreur de configuration : l'adresse email de contact n'est pas configurée.")
                return redirect("about")
            
            try:
                # Envoyer l'email
                send_mail(
                    email_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )
                
                messages.success(request, "Votre message a été envoyé avec succès! Je vous répondrai dans les plus brefs délais.")
            except Exception as e:
                # Logger l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'envoi de l'email : {e}")
                
                if settings.DEBUG:
                    messages.error(request, f"Erreur lors de l'envoi de l'email (mode debug) : {e}")
                else:
                    messages.error(request, "Une erreur est survenue lors de l'envoi de votre message. Veuillez réessayer plus tard ou me contacter directement.")
            
            return redirect("about")
    else:
        form = ContactForm()

    context = {
        "form": form,
        "profile": profile,
    }
    return render(request, "about.html", context)
