"""
Views pour le mode Montage IA Hybride.
Mix clips filmés (face-cam) + segments IA (mises en situation).
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models_extended import (
    VideoProductionJob, VideoScript, VideoSegmentGeneration, SegmentSourceType
)


@login_required
def hybrid_setup_view(request, script_pk):
    """
    Étape 1 : Configuration du montage hybride.
    - Définir personnage + décor (cohérence)
    - Choisir source de chaque segment (clip filmé ou IA)
    """
    script = get_object_or_404(VideoScript, pk=script_pk)
    full_script = script.get_full_script()
    
    # Segments avec suggestions de source
    segments_config = [
        {'index': 0, 'name': 'hook', 'label': '🎣 HOOK', 'timing': full_script['hook']['timing'],
         'text': full_script['hook']['text'], 'suggested_source': 'uploaded_clip',
         'tip': "Face-cam recommandé : accroche directe au spectateur"},
        {'index': 1, 'name': 'problem', 'label': '😤 PROBLÈME', 'timing': full_script['problem']['timing'],
         'text': full_script['problem']['text'], 'suggested_source': 'ai_generated',
         'tip': "IA recommandé : mise en situation du problème"},
        {'index': 2, 'name': 'micro_revelation', 'label': '💡 RÉVÉLATION', 'timing': full_script['micro_revelation']['timing'],
         'text': full_script['micro_revelation']['text'], 'suggested_source': 'uploaded_clip',
         'tip': "Face-cam recommandé : moment de connexion"},
        {'index': 3, 'name': 'solution', 'label': '🛠️ SOLUTION', 'timing': full_script['solution']['timing'],
         'text': full_script['solution']['text'], 'suggested_source': 'ai_generated',
         'tip': "IA ou screenshot : montrer la solution en action"},
        {'index': 4, 'name': 'proof', 'label': '📊 PREUVE', 'timing': full_script['proof']['timing'],
         'text': full_script['proof']['text'], 'suggested_source': 'ai_generated',
         'tip': "IA recommandé : mise en situation résultat positif"},
        {'index': 5, 'name': 'cta', 'label': '🎯 CTA', 'timing': full_script['cta']['timing'],
         'text': full_script['cta']['text'], 'suggested_source': 'uploaded_clip',
         'tip': "Face-cam recommandé : appel à l'action direct"},
    ]
    
    if request.method == 'POST':
        # Créer le job hybride
        job = VideoProductionJob.objects.create(
            title=request.POST.get('title', f"Montage Hybride - {script.code}"),
            theme=script.theme,
            status=VideoProductionJob.Status.DRAFT,
            created_by=request.user,
            is_hybrid=True,
            character_description=request.POST.get('character_description', ''),
            scene_description=request.POST.get('scene_description', ''),
            visual_style=request.POST.get('visual_style', 'Cinematic, warm lighting, realistic, vertical 9:16'),
            config={
                'provider': 'luma',
                'segments_count': 6,
                'segment_duration': 5,
                'aspect_ratio': '9:16',
                'script_id': script.pk,
                'mode': 'montage_hybride',
            }
        )
        
        # Créer les segments avec leur source_type
        for seg in segments_config:
            source = request.POST.get(f'source_{seg["index"]}', seg['suggested_source'])
            clip_file = request.FILES.get(f'clip_{seg["index"]}')
            scene_prompt = request.POST.get(f'scene_{seg["index"]}', seg['text'])
            
            generation = VideoSegmentGeneration.objects.create(
                job=job,
                segment_index=seg['index'],
                segment_name=seg['name'],
                source_type=source,
                prompt=scene_prompt,
                generation_mode='text_to_video' if source == 'ai_generated' else 'text_to_video',
                provider=job.get_config('provider', 'luma'),
                duration=5,
                aspect_ratio='9:16',
                status='pending' if source == 'ai_generated' else 'completed',
            )
            
            # Si clip uploadé, sauvegarder
            if clip_file and source == 'uploaded_clip':
                generation.uploaded_clip = clip_file
                generation.status = 'completed'
                generation.save()
        
        # Update job status
        job.status = VideoProductionJob.Status.ASSETS_READY
        job.save()
        
        # Incrémenter usage script
        script.increment_usage()
        
        messages.success(request, f"✅ Montage hybride créé ! {job.title}")
        return redirect('marketing:hybrid_review', pk=job.pk)
    
    return render(request, 'marketing/hybrid_setup.html', {
        'script': script,
        'segments': segments_config,
    })


@login_required
def hybrid_review_view(request, pk):
    """
    Étape 2 : Review et lancement.
    - Voir le résumé de tous les segments
    - Vérifier cohérence personnage/scène
    - Lancer la génération des segments IA
    """
    job = get_object_or_404(VideoProductionJob, pk=pk, is_hybrid=True)
    
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "❌ Accès refusé")
        return redirect('marketing:dashboard')
    
    segments = job.generations.order_by('segment_index')
    
    # Stats
    ai_segments = segments.filter(source_type='ai_generated').count()
    clip_segments = segments.filter(source_type='uploaded_clip').count()
    
    # Preview des prompts enrichis
    enriched_segments = []
    for seg in segments:
        enriched_segments.append({
            'segment': seg,
            'enriched_prompt': seg.get_enriched_prompt() if seg.source_type == 'ai_generated' else None,
        })
    
    return render(request, 'marketing/hybrid_review.html', {
        'job': job,
        'segments': enriched_segments,
        'ai_count': ai_segments,
        'clip_count': clip_segments,
        'estimated_cost': ai_segments * 5 * 0.03,  # segments IA × 5s × $0.03/s
    })


@login_required
def hybrid_generate_view(request, pk):
    """Lance la génération des segments IA uniquement (les clips sont déjà prêts)"""
    job = get_object_or_404(VideoProductionJob, pk=pk, is_hybrid=True)
    
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "❌ Accès refusé")
        return redirect('marketing:dashboard')
    
    try:
        from .ai.generation_orchestrator import GenerationOrchestrator
        
        orchestrator = GenerationOrchestrator(job)
        orchestrator.start_generation()
        
        ai_count = job.generations.filter(source_type='ai_generated').count()
        clip_count = job.generations.filter(source_type='uploaded_clip').count()
        
        messages.success(
            request,
            f"🎬 Génération lancée ! {ai_count} segments IA en cours, {clip_count} clips déjà prêts."
        )
        
    except Exception as e:
        messages.error(request, f"❌ Erreur : {str(e)}")
    
    return redirect('marketing:job_detail', pk=pk)


@login_required
def hybrid_assemble_view(request, pk):
    """Assemble tous les segments en vidéo finale"""
    job = get_object_or_404(VideoProductionJob, pk=pk, is_hybrid=True)
    
    if job.created_by != request.user and not request.user.is_staff:
        messages.error(request, "❌ Accès refusé")
        return redirect('marketing:dashboard')
    
    # Vérifier que tous les segments sont prêts
    total = job.generations.count()
    completed = job.generations.filter(status='completed').count()
    
    if completed < total:
        messages.warning(
            request,
            f"⚠️ Seulement {completed}/{total} segments prêts. Attendez la fin des générations."
        )
        return redirect('marketing:job_detail', pk=pk)
    
    try:
        from .ai.video_assembler import VideoAssembler
        
        assembler = VideoAssembler(job)
        final_path = assembler.assemble(add_subtitles=True)
        
        messages.success(
            request,
            f"🎉 Vidéo finale assemblée ! {final_path}"
        )
        
    except Exception as e:
        messages.error(request, f"❌ Erreur assemblage : {str(e)}")
    
    return redirect('marketing:job_detail', pk=pk)
