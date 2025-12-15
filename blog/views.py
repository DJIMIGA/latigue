from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Count

from .models import Category, Post


# Create your views here.
class blog_index(ListView):
    model = Post
    template_name = "blog/blogpost_index.html"
    context_object_name = 'posts'
    paginate_by = 12  # Pagination pour améliorer les performances
    
    def get_queryset(self):
        # Optimisation : prefetch_related pour éviter les requêtes N+1 sur les catégories
        return Post.objects.prefetch_related('categories').order_by('-created_on')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Optimisation : utiliser select_related si nécessaire et annotate en une seule requête
        context['categories_with_count'] = Category.objects.annotate(
            post_count=Count('posts')  # posts est le related_name
        ).filter(post_count__gt=0).order_by('name')
        return context


class blog_Detail(DetailView):
    model = Post
    template_name = "blog/blogpost_detail.html"
    context_object_name = 'post'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    
    def get_queryset(self):
        # Optimisation : prefetch_related pour charger les catégories en une seule requête
        return Post.objects.prefetch_related('categories')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Optimisation : Récupérer tous les articles de la même catégorie avec prefetch
        if post.categories.exists():
            category = post.categories.first()
            # Utilisation du related_name 'posts' avec prefetch pour éviter N+1
            related_posts = category.posts.exclude(id=post.id).prefetch_related('categories')[:4]
            context['related_posts'] = related_posts
        
        # Optimisation : Cache cette requête car elle est coûteuse
        # Récupérer les catégories avec leur nombre d'articles
        context['categories_stats'] = Category.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0).order_by('name')
        
        return context


# Vue pour afficher les articles par catégorie
class CategoryPostListView(ListView):
    model = Post
    template_name = "blog/category_posts.html"
    context_object_name = 'posts'
    paginate_by = 12  # Pagination pour améliorer les performances
    
    def get_queryset(self):
        # Récupérer la catégorie par slug
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        # Optimisation : Utiliser prefetch_related et order_by pour de meilleures performances
        return self.category.posts.prefetch_related('categories').order_by('-created_on')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
