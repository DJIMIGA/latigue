"""
Views pour la bibliothèque de scripts vidéo.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import JsonResponse

from .models_extended import VideoScript, VideoTheme, ClientLevel, Platform


class VideoScriptLibraryView(LoginRequiredMixin, ListView):
    """
    Bibliothèque de scripts vidéo avec filtres et recherche.
    """
    model = VideoScript
    template_name = 'marketing/scripts_library.html'
    context_object_name = 'scripts'
    paginate_by = 20
    
    def get_queryset(self):
        qs = VideoScript.objects.all()
        
        # Recherche texte
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(code__icontains=query) |
                Q(hook__icontains=query) |
                Q(solution__icontains=query)
            )
        
        # Filtre thème
        theme = self.request.GET.get('theme')
        if theme:
            qs = qs.filter(theme=theme)
        
        # Filtre plateforme
        platform = self.request.GET.get('platform')
        if platform:
            qs = qs.filter(Q(platform=platform) | Q(platform=Platform.ALL))
        
        # Filtre niveau client
        level = self.request.GET.get('level')
        if level:
            qs = qs.filter(Q(client_level=level) | Q(client_level=ClientLevel.TOUS))
        
        # Filtre durée max
        max_duration = self.request.GET.get('max_duration')
        if max_duration:
            qs = qs.filter(duration_max__lte=int(max_duration))
        
        # Filtre tags
        tag = self.request.GET.get('tag')
        if tag:
            qs = qs.filter(tags__contains=[tag])
        
        # Tri
        sort = self.request.GET.get('sort', '-created_at')
        qs = qs.order_by(sort)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Choix pour les filtres
        context['themes'] = VideoTheme.choices
        context['platforms'] = Platform.choices
        context['client_levels'] = ClientLevel.choices
        
        # Paramètres actuels pour pré-remplir les filtres
        context['current_query'] = self.request.GET.get('q', '')
        context['current_theme'] = self.request.GET.get('theme', '')
        context['current_platform'] = self.request.GET.get('platform', '')
        context['current_level'] = self.request.GET.get('level', '')
        context['current_max_duration'] = self.request.GET.get('max_duration', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        # Stats globales
        context['total_scripts'] = VideoScript.objects.count()
        context['themes_count'] = VideoScript.objects.values('theme').distinct().count()
        
        # Tags populaires
        all_tags = []
        for script in VideoScript.objects.all():
            all_tags.extend(script.tags)
        context['popular_tags'] = list(set(all_tags))[:10]
        
        return context


class VideoScriptDetailView(LoginRequiredMixin, DetailView):
    """
    Détail d'un script vidéo avec preview complet.
    """
    model = VideoScript
    template_name = 'marketing/script_detail.html'
    context_object_name = 'script'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['full_script'] = self.object.get_full_script()
        return context


@login_required
def script_use_for_job(request, pk):
    """
    Pré-remplir un VideoProductionJob depuis un VideoScript.
    Redirige vers job_create avec params GET.
    """
    script = get_object_or_404(VideoScript, pk=pk)
    
    # Incrémenter le compteur d'utilisation
    script.increment_usage()
    
    # Construire l'URL avec paramètres
    params = {
        'from_script': script.pk,
        'title': f"Vidéo {script.code} - {script.title}",
        'theme': script.theme,
        'duration': script.duration_max,
    }
    
    from urllib.parse import urlencode
    url = f"{reverse('marketing:job_create')}?{urlencode(params)}"
    
    return redirect(url)


@login_required
def api_script_preview(request, pk):
    """
    API: Prévisualisation JSON d'un script (pour modal/AJAX).
    """
    script = get_object_or_404(VideoScript, pk=pk)
    
    return JsonResponse({
        'code': script.code,
        'title': script.title,
        'theme': script.get_theme_display(),
        'platform': script.get_platform_display(),
        'duration': f"{script.duration_min}-{script.duration_max}s",
        'full_script': script.get_full_script(),
        'tags': script.tags,
        'usage_count': script.usage_count,
    })


from django.urls import reverse
