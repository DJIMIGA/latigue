"""
Configuration du sitemap pour le référencement SEO
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post, Category
from services.models import Service
from formations.models import Formation


class StaticViewSitemap(Sitemap):
    """Sitemap pour les pages statiques"""
    priority = 1.0
    changefreq = 'monthly'

    def items(self):
        return [
            'portfolio-index',
            'about',
            'contact',
            'blog-index',
            'services:service_list',
            'formations:formation_index',
        ]

    def location(self, item):
        return reverse(item)


class BlogPostSitemap(Sitemap):
    """Sitemap pour les articles de blog"""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        # Inclure tous les articles (pas seulement ceux qui ne sont pas featured)
        return Post.objects.all().order_by('-created_on')

    def lastmod(self, obj):
        return obj.last_modified


class BlogCategorySitemap(Sitemap):
    """Sitemap pour les catégories de blog"""
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class ServiceSitemap(Sitemap):
    """Sitemap pour les services"""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Service.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class FormationSitemap(Sitemap):
    """Sitemap pour les formations"""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Formation.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

