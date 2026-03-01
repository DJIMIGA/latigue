"""
Views pour l'interface web de production vidéo.
Dashboard, wizards, monitoring temps réel.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models_extended import (
    VideoProductionJob,
    VideoProjectTemplate,
    SegmentAsset,
    VideoSegmentGeneration
)
from .forms import (
    VideoProductionJobForm,
    QuickVideoForm,
    BulkSegmentConfigForm,
    SegmentAssetUploadForm
)


# =============================================================================
# DASHBOARD PRINCIPAL
# =============================================================================

class VideoProductionDashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard principal : liste des jobs, stats, actions rapides.
    """
    model = VideoProductionJob
    template_name = 'marketing/dashboard.html'
    context_object_name = 'jobs'
    paginate_by = 20
    
    def get_queryset(self):
        qs = VideoProductionJob.objects.select_related('template', 'created_by')
        
        # Filtres
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(theme__icontains=search)
            )
        
        # Ordre
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats globales
        context['stats'] = {
            'total_jobs': VideoProductionJob.objects.count(),
            'completed': VideoProductionJob.objects.filter(
                status=VideoProductionJob.Status.COMPLETED
            ).count(),
            'in_progress': VideoProductionJob.objects.filter(
                status__in=[
                    VideoProductionJob.Status.SCRIPT_PENDING,
                    VideoProductionJob.Status.VIDEO_PENDING,
                    VideoProductionJob.Status.ASSEMBLY_PENDING,
                ]
            ).count(),
            'total_cost': VideoProductionJob.objects.aggregate(
                total=Sum('actual_cost')
            )['total'] or 0,
        }
        
        # Templates disponibles
        context['templates'] = VideoProjectTemplate.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Status choices pour filtres
        context['status_choices'] = VideoProductionJob.Status.choices
        
        return context


# =============================================================================
# CRÉATION DE JOB (WIZARD)
# =============================================================================

class VideoJobCreateView(LoginRequiredMixin, CreateView):
    """
    Étape 1 : Créer le job (titre, thème, template)
    """
    model = VideoProductionJob
    form_class = VideoProductionJobForm
    template_name = 'marketing/job_create.html'
    success_url = reverse_lazy('marketing:dashboard')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f"✅ Job créé : {self.object.title} (coût estimé: ${self.object.estimated_cost})"
        )
        
        # Rediriger vers config segments
        return redirect('marketing:job_configure_segments', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = VideoProjectTemplate.objects.filter(is_active=True)
        return context


class VideoJobConfigureSegmentsView(LoginRequiredMixin, DetailView):
    """
    Étape 2 : Configurer les segments (prompts + assets optionnels)
    """
    model = VideoProductionJob
    template_name = 'marketing/job_configure_segments.html'
    
    def get_object(self):
        job = super().get_object()
        # Vérifier ownership
        if job.created_by != self.request.user and not self.request.user.is_staff:
            raise PermissionError("Pas votre job")
        return job
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Form config segments
        if self.request.method == 'POST':
            context['segments_form'] = BulkSegmentConfigForm(
                self.request.POST,
                self.request.FILES,
                job=job
            )
        else:
            context['segments_form'] = BulkSegmentConfigForm(job=job)
        
        context['segments_count'] = job.get_config('segments_count', 6)
        context['mode'] = job.get_config('mode', 'text_to_video')
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        
        form = context['segments_form']
        
        if form.is_valid():
            # Créer/update assets pour chaque segment
            segments_data = form.get_segments_data()
            
            for seg_data in segments_data:
                # Si asset fourni, créer SegmentAsset
                if seg_data['asset']:
                    asset, created = SegmentAsset.objects.update_or_create(
                        job=self.object,
                        segment_index=seg_data['index'],
                        defaults={
                            'asset_type': 'image',
                            'file': seg_data['asset'],
                            'animation_prompt': seg_data['animation_prompt'],
                        }
                    )
                
                # Créer VideoSegmentGeneration
                generation_mode = 'image_to_video' if seg_data['asset'] else 'text_to_video'
                
                VideoSegmentGeneration.objects.update_or_create(
                    job=self.object,
                    segment_index=seg_data['index'],
                    defaults={
                        'prompt': seg_data['prompt'],
                        'generation_mode': generation_mode,
                        'provider': self.object.get_config('provider', 'luma'),
                        'duration': self.object.get_config('segment_duration', 5),
                        'aspect_ratio': self.object.get_config('aspect_ratio', '9:16'),
                        'status': 'pending',
                    }
                )
            
            # Update job status
            self.object.status = VideoProductionJob.Status.ASSETS_READY
            self.object.save()
            
            messages.success(
                request,
                f"✅ {len(segments_data)} segments configurés ! Prêt pour génération."
            )
            
            return redirect('marketing:job_detail', pk=self.object.pk)
        
        return self.render_to_response(context)


# =============================================================================
# DETAIL & MONITORING
# =============================================================================

class VideoJobDetailView(LoginRequiredMixin, DetailView):
    """
    Vue détaillée d'un job : monitoring, progression, actions.
    """
    model = VideoProductionJob
    template_name = 'marketing/job_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Segments et générations
        context['generations'] = job.generations.all().order_by('segment_index')
        context['assets'] = job.assets.all().order_by('segment_index')
        
        # Progression
        total_segments = job.generations.count()
        completed_segments = job.generations.filter(
            status=VideoSegmentGeneration.Status.COMPLETED
        ).count()
        
        if total_segments > 0:
            context['progress'] = int((completed_segments / total_segments) * 100)
        else:
            context['progress'] = 0
        
        # Coûts
        context['segments_cost'] = job.generations.aggregate(
            total=Sum('cost')
        )['total'] or 0
        
        return context


# =============================================================================
# QUICK GENERATION
# =============================================================================

@login_required
def quick_video_view(request):
    """
    Génération vidéo rapide sans passer par wizard complet.
    """
    if request.method == 'POST':
        form = QuickVideoForm(request.POST)
        
        if form.is_valid():
            # Créer job
            job = form.create_job(user=request.user)
            
            if job:
                messages.success(
                    request,
                    f"✅ Job créé : {job.title}"
                )
                
                # Option : lancer génération immédiate ou config segments ?
                auto_generate = request.POST.get('auto_generate')
                
                if auto_generate:
                    # TODO: Déclencher génération auto avec script IA
                    return redirect('marketing:job_generate', pk=job.pk)
                else:
                    return redirect('marketing:job_configure_segments', pk=job.pk)
        
    else:
        form = QuickVideoForm()
    
    return render(request, 'marketing/quick_video.html', {
        'form': form,
    })


# =============================================================================
# ACTIONS
# =============================================================================

@login_required
def job_start_generation(request, pk):
    """
    Lance la génération des segments d'un job.
    """
    job = get_object_or_404(VideoProductionJob, pk=pk)
    
    # Vérifier ownership
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "❌ Accès refusé")
        return redirect('marketing:dashboard')
    
    # Vérifier que segments sont configurés
    if not job.generations.exists():
        messages.error(
            request,
            "❌ Configurer les segments d'abord"
        )
        return redirect('marketing:job_configure_segments', pk=job.pk)
    
    # TODO: Déclencher génération asynchrone (Celery task ou management command)
    # Pour l'instant, juste update status
    job.status = VideoProductionJob.Status.VIDEO_PENDING
    job.started_at = timezone.now()
    job.save()
    
    messages.info(
        request,
        f"🎬 Génération lancée pour {job.generations.count()} segments"
    )
    
    return redirect('marketing:job_detail', pk=job.pk)


@login_required
def job_cancel(request, pk):
    """
    Annule un job en cours.
    """
    job = get_object_or_404(VideoProductionJob, pk=pk)
    
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "❌ Accès refusé")
        return redirect('marketing:dashboard')
    
    job.status = VideoProductionJob.Status.PAUSED
    job.save()
    
    messages.warning(request, f"⏸️ Job mis en pause")
    
    return redirect('marketing:job_detail', pk=job.pk)


# =============================================================================
# API ENDPOINTS (pour polling temps réel)
# =============================================================================

@login_required
def api_job_status(request, pk):
    """
    API endpoint : récupère status job en JSON (pour polling AJAX).
    """
    job = get_object_or_404(VideoProductionJob, pk=pk)
    
    generations = job.generations.all()
    
    data = {
        'status': job.status,
        'progress': job.progress_percent,
        'segments': {
            'total': generations.count(),
            'pending': generations.filter(status='pending').count(),
            'processing': generations.filter(status='processing').count(),
            'completed': generations.filter(status='completed').count(),
            'failed': generations.filter(status='failed').count(),
        },
        'cost': {
            'estimated': float(job.estimated_cost),
            'actual': float(job.actual_cost),
        },
        'generations': [
            {
                'index': gen.segment_index,
                'status': gen.status,
                'progress': gen.progress_percent,
                'provider': gen.provider,
                'video_url': gen.video_url,
            }
            for gen in generations.order_by('segment_index')
        ]
    }
    
    return JsonResponse(data)


@login_required
def api_segment_retry(request, job_pk, segment_index):
    """
    API endpoint : retry génération d'un segment échoué.
    """
    job = get_object_or_404(VideoProductionJob, pk=job_pk)
    generation = get_object_or_404(
        VideoSegmentGeneration,
        job=job,
        segment_index=segment_index
    )
    
    # Reset status
    generation.status = VideoSegmentGeneration.Status.PENDING
    generation.error_message = ''
    generation.save()
    
    # TODO: Re-queue pour génération
    
    return JsonResponse({
        'success': True,
        'message': f'Segment {segment_index} re-queued'
    })
