from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Count

from .models import Category, Post


# Create your views here.
class blog_index(ListView):
    model = Post
    template_name = "blog/blogpost_index.html"
    context_object_name = 'posts'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Exemple d'utilisation de related_name
        context['categories_with_count'] = Category.objects.annotate(
            post_count=Count('posts')  # posts est le related_name
        ).filter(post_count__gt=0)
        return context


class blog_Detail(DetailView):
    model = Post
    template_name = "blog/blogpost_detail.html"
    context_object_name = 'post'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Exemple 1: Récupérer tous les articles de la même catégorie
        if post.categories.exists():
            category = post.categories.first()
            # Utilisation du related_name 'posts'
            related_posts = category.posts.exclude(id=post.id)[:4]
            context['related_posts'] = related_posts
        
        # Exemple 2: Récupérer les catégories avec leur nombre d'articles
        context['categories_stats'] = Category.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0)
        
        return context


# Vue pour afficher les articles par catégorie
class CategoryPostListView(ListView):
    model = Post
    template_name = "blog/category_posts.html"
    context_object_name = 'posts'
    
    def get_queryset(self):
        # Récupérer la catégorie par slug
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        # Utiliser le related_name pour récupérer tous les articles de cette catégorie
        return self.category.posts.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
