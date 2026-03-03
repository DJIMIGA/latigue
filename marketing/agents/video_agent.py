"""
VideoAgent — Génère les vidéos (IA ou avatar).

Deux modes:
1. Avatar (HeyGen): audio + avatar_id → talking head video
2. IA (MiniMax/Luma): prompt → vidéo générée par segments

Le mode est déterminé par la config du job:
- job.config['video_mode'] = 'avatar' | 'ai_segments'
"""

from django.conf import settings
from django.utils import timezone
from .base import BaseAgent, AgentResult


class VideoAgent(BaseAgent):
    name = "VideoAgent"
    
    def can_run(self, job) -> bool:
        return job.status in ('assets_ready', 'script_ready')
    
    def execute(self, job) -> AgentResult:
        """Route vers le bon mode de génération."""
        mode = job.get_config('video_mode', 'ai_segments')
        
        if mode == 'avatar':
            return self._generate_avatar(job)
        else:
            return self._generate_ai_segments(job)
    
    def _generate_avatar(self, job) -> AgentResult:
        """Mode HeyGen: génère une vidéo avatar talking head."""
        from marketing.ai.heygen import HeyGenProvider
        
        api_key = getattr(settings, 'HEYGEN_API_KEY', None)
        avatar_id = job.get_config('avatar_id') or getattr(settings, 'HEYGEN_AVATAR_ID', None)
        
        if not api_key:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message="HEYGEN_API_KEY non configurée",
                errors=["missing_heygen_key"]
            )
        
        if not avatar_id:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message="HEYGEN_AVATAR_ID non configuré",
                errors=["missing_avatar_id"]
            )
        
        heygen = HeyGenProvider(api_key=api_key, avatar_id=avatar_id)
        
        # Vérifier qu'on a l'audio
        audio_path = job.get_config('audio_path')
        
        if audio_path:
            # Upload audio puis générer
            audio_url = heygen.upload_audio(audio_path)
            if not audio_url:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    message="Échec upload audio vers HeyGen",
                    errors=["audio_upload_failed"]
                )
            
            result = heygen.generate_talking_video(
                audio_url=audio_url,
                background=job.get_config('background'),
                aspect_ratio=job.get_config('aspect_ratio', '9:16')
            )
        else:
            # Mode TTS direct HeyGen (fallback)
            from marketing.agents.voice_agent import VoiceAgent
            voiceover = VoiceAgent()._extract_voiceover(job)
            
            voice_id = job.get_config('voice_id')
            if not voice_id:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    message="voice_id requis pour mode TTS HeyGen",
                    errors=["missing_voice_id"]
                )
            
            result = heygen.generate_talking_video(
                text=voiceover,
                voice_id=voice_id,
                aspect_ratio=job.get_config('aspect_ratio', '9:16')
            )
        
        if result.status == "failed":
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=f"HeyGen error: {result.error_message}",
                errors=[result.error_message]
            )
        
        # Stocker le job_id pour polling
        job.config = {
            **job.config,
            'heygen_video_id': result.job_id,
            'video_provider': 'heygen',
        }
        job.status = 'video_pending'
        job.started_at = timezone.now()
        job.save(update_fields=['config', 'status', 'started_at'])
        
        return AgentResult(
            success=True,
            agent_name=self.name,
            message=f"HeyGen job lancé: {result.job_id}",
            data={"heygen_video_id": result.job_id},
            cost_usd=heygen.estimate_cost(job.get_config('duration_max', 30))
        )
    
    def _generate_ai_segments(self, job) -> AgentResult:
        """Mode IA: génère des segments vidéo via MiniMax/Luma."""
        from marketing.ai.video_providers import get_provider
        from marketing.models_extended import VideoSegmentGeneration
        
        provider_name = job.get_config('provider', 'minimax')
        
        try:
            provider = get_provider(provider_name)
        except ValueError as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=str(e),
                errors=[str(e)]
            )
        
        # Récupérer les segments à générer
        segments = job.generations.filter(
            status__in=['pending', 'failed']
        ).order_by('segment_index')
        
        if not segments.exists():
            # Pas de segments pré-créés — les créer depuis le script
            segments = self._create_segments_from_script(job, provider_name)
            if not segments:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    message="Impossible de créer les segments depuis le script",
                    errors=["no_segments"]
                )
        
        # Lancer la génération
        launched = 0
        errors = []
        total_cost = 0
        
        for seg in segments:
            if seg.source_type == 'uploaded_clip':
                # Clip filmé — pas de génération IA
                seg.status = 'completed'
                seg.save(update_fields=['status'])
                launched += 1
                continue
            
            prompt = seg.get_enriched_prompt()
            duration = seg.duration or 6
            
            result = provider.generate_clip(
                prompt=prompt,
                duration=duration,
                **seg.provider_config
            )
            
            if result.status == "failed":
                seg.status = 'failed'
                seg.error_message = result.error_message
                seg.save(update_fields=['status', 'error_message'])
                errors.append(f"Segment {seg.segment_index}: {result.error_message}")
            else:
                seg.provider_job_id = result.job_id
                seg.status = 'processing'
                seg.started_at = timezone.now()
                seg.cost = provider.estimate_cost(duration)
                seg.save(update_fields=['provider_job_id', 'status', 'started_at', 'cost'])
                launched += 1
                total_cost += float(seg.cost)
        
        job.status = 'video_pending'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])
        
        return AgentResult(
            success=launched > 0,
            agent_name=self.name,
            message=f"{launched} segments lancés via {provider_name}" + (f", {len(errors)} erreurs" if errors else ""),
            data={"launched": launched, "provider": provider_name},
            errors=errors,
            cost_usd=total_cost
        )
    
    def _create_segments_from_script(self, job, provider_name: str):
        """Crée des VideoSegmentGeneration depuis le script du job."""
        import json
        from marketing.models_extended import VideoSegmentGeneration
        
        # Essayer de parser le script JSON
        try:
            script_data = json.loads(job.script_text)
            visual_directions = script_data.get('visual_directions', [])
        except (json.JSONDecodeError, TypeError):
            # Script texte — découper en segments
            lines = [l.strip() for l in job.script_text.split('\n') if l.strip()]
            visual_directions = lines[:6]  # Max 6 segments
        
        if not visual_directions:
            return None
        
        segments = []
        for i, direction in enumerate(visual_directions):
            seg = VideoSegmentGeneration.objects.create(
                job=job,
                segment_index=i,
                segment_name=f"segment_{i}",
                prompt=direction,
                provider=provider_name,
                duration=job.get_config('segment_duration', 6),
                generation_mode='text_to_video',
                provider_config=job.get_config('provider_config', {})
            )
            segments.append(seg)
        
        return segments
