from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
                  path("", views.portfolio_index, name="portfolio-index"),
                  path("about/", views.about, name="about"),
                  # Alias pour la page de contact afin de supporter {% url 'contact' %}
                  path("contact/", views.about, name="contact"),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                                           document_root=settings.MEDIA_ROOT)
                                                                                          