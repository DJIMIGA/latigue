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

    context = {
        "form": form,
        "profile": profile,
    }
    return render(request, "about.html", context)
