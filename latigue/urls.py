"""
URL configuration for latigue project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from .sitemaps import (
    StaticViewSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    ServiceSitemap,
    FormationSitemap,
)

# Configuration du sitemap
sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'blog_categories': BlogCategorySitemap,
    'services': ServiceSitemap,
    'formations': FormationSitemap,
}

def health_view(request):
    """Vue légère pour healthcheck Docker / reverse proxy (pas de DB)."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path('health/', health_view),
    path('admin/', admin.site.urls),
    path('', include('portfolio.urls')),
    path('blog/', include('blog.urls')),
    path('services/', include('services.urls')),
    path('formations/', include('formations.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    # Sitemap pour le SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
