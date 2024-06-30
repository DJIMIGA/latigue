from django.conf import settings

from django.core.mail import send_mail

from .forms import ContactForm
from django.shortcuts import render, redirect

from portfolio.models import Portfolio


# Create your views here.
def portfolio_index(request):
    portfolios = Portfolio.objects.all()
    context = {
        "portfolios": portfolios,
        'MEDIA_URL': settings.MEDIA_URL}
    return render(request, "portfolio_index.html", context)


def about(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']
            try:
                # Envoyer un e-mail
                send_mail(
                    sujet,
                    message,
                    email,
                    ['pymalien1@gmail.com'],
                    fail_silently=False,
                )
            except Exception as e:
                print(f'Error sending email: {e}')
            # Afficher un message de succès
            context = {
                'form': ContactForm(),
                'MEDIA_URL': settings.MEDIA_URL,
                'success_message': 'Votre message a été envoyé avec succès.'
            }
            return render(request, 'about.html', context)
        else:
            print("Form is invalid")
    else:
        print("Received a GET request")
        form = ContactForm()

    context = {
        'form': form,
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, "about.html", context)
