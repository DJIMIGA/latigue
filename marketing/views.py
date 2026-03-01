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
    Peut être pré-rempli depuis un VideoScript via param GET from_script
    """
    model = VideoProductionJob
    form_class = VideoProductionJobForm
    template_name = 'marketing/job_create.html'
    success_url = reverse_lazy('marketing:dashboard')
    
    def get_initial(self):
        """Pré-remplir le form depuis un VideoScript si from_script présent"""
        initial = super().get_initial()
        
        # Pré-remplissage depuis script ?
        from_script_id = self.request.GET.get('from_script')
        if from_script_id:
            try:
                from .models_extended import VideoScript
                script = VideoScript.objects.get(pk=from_script_id)
                
                # Pré-remplir les champs
                initial['title'] = self.request.GET.get('title', f"Vidéo {script.code} - {script.title}")
                initial['theme'] = script.theme
                initial['target_duration'] = script.duration_max
                
                # Stocker script_id en session pour étape 2
                self.request.session['current_script_id'] = script.pk
                
            except VideoScript.DoesNotExist:
                messages.warning(self.request, "Script introuvable, formulaire vierge.")
        
        return initial
    
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
        
        # Ajouter script source si présent
        from_script_id = self.request.GET.get('from_script')
        if from_script_id:
            try:
                from .models_extended import VideoScript
                context['source_script'] = VideoScript.objects.get(pk=from_script_id)
            except VideoScript.DoesNotExist:
                pass
        
        return context


class VideoJobConfigureSegmentsView(LoginRequiredMixin, DetailView):
    """
    Étape 2 : Configurer les segments (prompts + assets optionnels)
    Auto-génère segments depuis VideoScript si disponible en session
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
        
        # Auto-générer segments depuis script si présent
        script_id = self.request.session.get('current_script_id')
        if script_id and not hasattr(job, '_segments_generated'):
            try:
                from .models_extended import VideoScript
                script = VideoScript.objects.get(pk=script_id)
                self._generate_segments_from_script(job, script)
                context['script_source'] = script
                context['segments_auto_generated'] = True
                # Clear session
                del self.request.session['current_script_id']
            except VideoScript.DoesNotExist:
                pass
        
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
    
    def _generate_segments_from_script(self, job, script):
        """
        Génère automatiquement les segments depuis un VideoScript.
        Crée 6 VideoSegmentGeneration : hook, problem, micro_revelation, solution, proof, cta
        """
        full_script = script.get_full_script()
        
        segments_config = [
            {
                'index': 0,
                'name': 'hook',
                'prompt': full_script['hook']['text'],
                'timing': full_script['hook']['timing'],
                'duration': 3,
            },
            {
                'index': 1,
                'name': 'problem',
                'prompt': full_script['problem']['text'],
                'timing': full_script['problem']['timing'],
                'duration': 5,
            },
            {
                'index': 2,
                'name': 'micro_revelation',
                'prompt': full_script['micro_revelation']['text'],
                'timing': full_script['micro_revelation']['timing'],
                'duration': 4,
            },
            {
                'index': 3,
                'name': 'solution',
                'prompt': full_script['solution']['text'],
                'timing': full_script['solution']['timing'],
                'duration': 13,
                'hint': full_script['solution']['hint'],
            },
            {
                'index': 4,
                'name': 'proof',
                'prompt': full_script['proof']['text'],
                'timing': full_script['proof']['timing'],
                'duration': 10,
            },
            {
                'index': 5,
                'name': 'cta',
                'prompt': full_script['cta']['text'],
                'timing': full_script['cta']['timing'],
                'duration': 5,
            },
        ]
        
        # Créer VideoSegmentGeneration pour chaque segment
        for seg in segments_config:
            VideoSegmentGeneration.objects.create(
                job=job,
                segment_index=seg['index'],
                prompt=seg['prompt'],
                generation_mode='text_to_video',
                provider=job.get_config('provider', 'luma'),
                duration=seg['duration'],
                aspect_ratio=job.get_config('aspect_ratio', '9:16'),
                status='pending',
            )
        
        # Update job status
        job.status = VideoProductionJob.Status.ASSETS_READY
        job.save()
        
        # Flag pour éviter double génération
        job._segments_generated = True
        
        messages.success(
            self.request,
            f"✨ 6 segments générés automatiquement depuis le script {script.code} !"
        )


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


# =============================================================================
# ASSETS LIBRARY (Placeholders)
# =============================================================================

@login_required
def assets_library_view(request):
    """Liste des assets uploadés"""
    assets = SegmentAsset.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'marketing/assets_library.html', {'assets': assets})


@login_required
def assets_upload_view(request):
    """Upload d'assets"""
    if request.method == 'POST':
        form = SegmentAssetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.save()
            messages.success(request, f"Asset '{asset.name}' uploadé avec succès!")
            return redirect('marketing:assets_library')
    else:
        form = SegmentAssetUploadForm()
    return render(request, 'marketing/assets_upload.html', {'form': form})


@login_required
def asset_delete_view(request, pk):
    """Suppression d'un asset"""
    asset = get_object_or_404(SegmentAsset, pk=pk, created_by=request.user)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, "Asset supprimé!")
        return redirect('marketing:assets_library')
    return render(request, 'marketing/asset_confirm_delete.html', {'asset': asset})


# =============================================================================
# AI ASSISTANT (Placeholders)
# =============================================================================

@login_required
def ai_assistant_view(request):
    """Interface conversationnelle AI Assistant"""
    return render(request, 'marketing/ai_assistant.html')


@login_required
def ai_chat_view(request):
    """API chat avec Claude"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # TODO: Intégrer vraie API Claude
        response = {
            'message': f"Assistant IA (placeholder) : Vous avez dit '{user_message}'. Fonctionnalité en cours de développement.",
            'suggestions': [
                'Créer une vidéo TikTok sur le thème IA',
                'Montrer les assets disponibles',
                'Générer 5 vidéos pour la semaine'
            ]
        }
        return JsonResponse(response)
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def ai_generate_job_view(request):
    """Génération de job via prompts IA"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        
        # TODO: Parser le prompt et créer un VideoProductionJob
        return JsonResponse({
            'success': True,
            'job_id': 1,  # Placeholder
            'message': 'Job créé (placeholder)'
        })
    return JsonResponse({'error': 'POST required'}, status=400)


# =============================================================================
# USER SETTINGS (Placeholder)
# =============================================================================

@login_required
def user_settings_view(request):
    """Paramètres utilisateur (API keys, préférences)"""
    return render(request, 'marketing/user_settings.html')


# =============================================================================
# JOB ACTIONS (Placeholders manquants)
# =============================================================================

@login_required
def job_start_generation(request, pk):
    """Démarrer la génération d'un job"""
    job = get_object_or_404(VideoProductionJob, pk=pk)
    
    # TODO: Lancer la génération réelle
    job.status = 'processing'
    job.save()
    
    messages.success(request, f"Génération de '{job.title}' démarrée!")
    return redirect('marketing:job_detail', pk=pk)


@login_required
def job_cancel(request, pk):
    """Annuler un job"""
    job = get_object_or_404(VideoProductionJob, pk=pk)
    job.status = 'failed'
    job.save()
    messages.warning(request, f"Job '{job.title}' annulé.")
    return redirect('marketing:dashboard')


@login_required
def api_job_status(request, pk):
    """API: Status d'un job (polling temps réel)"""
    job = get_object_or_404(VideoProductionJob, pk=pk)
    return JsonResponse({
        'status': job.status,
        'progress': job.progress_percent,
        'current_step': job.current_step or '',
    })


@login_required
def api_segment_retry(request, job_pk, segment_index):
    """API: Retry d'un segment spécifique"""
    job = get_object_or_404(VideoProductionJob, pk=job_pk)
    
    # TODO: Implémenter retry segment
    return JsonResponse({
        'success': True,
        'message': f'Segment {segment_index} en cours de régénération'
    })
