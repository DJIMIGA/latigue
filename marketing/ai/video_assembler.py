"""
Assembleur de segments vidéo en vidéo finale.
Combine segments + voix-off + sous-titres.
"""

import logging
from pathlib import Path
from typing import Optional
import tempfile
import requests

from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
from moviepy.video.VideoClip import TextClip

from django.conf import settings
from marketing.models import VideoProject, VideoSegment
from marketing.ai.tts_generator import generate_voiceover

logger = logging.getLogger(__name__)


class VideoAssembler:
    """
    Assemble les segments vidéo en vidéo finale.
    """
    
    def __init__(self, project: VideoProject):
        self.project = project
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def assemble(
        self,
        add_voiceover: bool = True,
        add_subtitles: bool = True,
        transition_duration: float = 0.3,
        output_path: Optional[str] = None
    ) -> str:
        """
        Assemble tous les segments en vidéo finale.
        
        Args:
            add_voiceover: Ajouter la voix-off
            add_subtitles: Ajouter les sous-titres
            transition_duration: Durée des transitions (secondes)
            output_path: Chemin de sortie (optionnel)
        
        Returns:
            Chemin de la vidéo finale
        """
        logger.info(f"Assemblage vidéo pour projet {self.project.id}")
        
        self.project.status = 'assembly'
        self.project.save()
        
        try:
            # 1. Télécharge tous les segments
            segments = self.project.get_selected_segments()
            segment_clips = self._download_segments(segments)
            
            if not segment_clips:
                raise ValueError("Aucun segment valide trouvé")
            
            # 2. Concatène les segments
            logger.info(f"Concaténation de {len(segment_clips)} segments")
            video = concatenate_videoclips(segment_clips, method="compose")
            
            # 3. Ajoute la voix-off
            if add_voiceover:
                video = self._add_voiceover(video)
            
            # 4. Ajoute les sous-titres
            if add_subtitles:
                video = self._add_subtitles(video, segments)
            
            # 5. Export
            if output_path is None:
                output_path = str(self.temp_dir / f"final_video_{self.project.id}.mp4")
            
            logger.info(f"Export vidéo finale vers {output_path}")
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=30,
                preset='medium',
                bitrate='5000k'
            )
            
            # Nettoyage
            video.close()
            for clip in segment_clips:
                clip.close()
            
            # Mise à jour projet
            self.project.status = 'completed'
            self.project.video_url = output_path  # TODO: Upload MinIO
            self.project.file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            self.project.save()
            
            logger.info(f"Vidéo assemblée avec succès: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur assemblage: {str(e)}")
            self.project.status = 'error'
            self.project.error_message = str(e)
            self.project.save()
            raise
    
    def _download_segments(self, segments) -> list:
        """Télécharge tous les segments vidéo"""
        clips = []
        
        for segment in segments:
            if not segment.video_url:
                logger.warning(f"Segment {segment.order} n'a pas de vidéo")
                continue
            
            try:
                # Télécharge le segment
                local_path = self.temp_dir / f"segment_{segment.order}.mp4"
                
                logger.info(f"Téléchargement segment {segment.order} depuis {segment.video_url}")
                response = requests.get(segment.video_url, timeout=60)
                response.raise_for_status()
                
                local_path.write_bytes(response.content)
                
                # Charge avec MoviePy
                clip = VideoFileClip(str(local_path))
                clips.append(clip)
                
            except Exception as e:
                logger.error(f"Erreur téléchargement segment {segment.order}: {e}")
                continue
        
        return clips
    
    def _add_voiceover(self, video: VideoFileClip) -> VideoFileClip:
        """Ajoute la voix-off sur toute la vidéo"""
        
        logger.info("Génération voix-off")
        
        # Récupère le texte complet
        voiceover_text = self.project.script.script_json.get('voiceover', '')
        
        if not voiceover_text:
            # Assemble les textes des segments
            segments = self.project.get_selected_segments()
            voiceover_text = ' '.join(seg.text for seg in segments)
        
        # Génère l'audio
        audio_path = generate_voiceover(voiceover_text, output_dir=str(self.temp_dir))
        
        # Ajoute à la vidéo
        audio_clip = AudioFileClip(audio_path)
        
        # Ajuste la durée si nécessaire
        if audio_clip.duration > video.duration:
            logger.warning(f"Audio plus long que vidéo ({audio_clip.duration}s vs {video.duration}s)")
            audio_clip = audio_clip.subclip(0, video.duration)
        
        video = video.set_audio(audio_clip)
        
        # Sauvegarde URL audio
        self.project.audio_url = audio_path  # TODO: Upload MinIO
        self.project.save()
        
        return video
    
    def _add_subtitles(self, video: VideoFileClip, segments) -> CompositeVideoClip:
        """Ajoute les sous-titres synchronisés"""
        
        logger.info("Ajout des sous-titres")
        
        subtitle_clips = []
        current_time = 0
        
        for segment in segments:
            # Crée un clip texte pour ce segment
            txt_clip = TextClip(
                segment.text,
                fontsize=40,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video.w * 0.9, None),
                align='center'
            )
            
            # Positionne en bas de l'écran
            txt_clip = txt_clip.set_position(('center', 0.85), relative=True)
            
            # Définit la durée et le timing
            txt_clip = txt_clip.set_start(current_time).set_duration(segment.duration)
            
            subtitle_clips.append(txt_clip)
            current_time += segment.duration
        
        # Composite vidéo + sous-titres
        final = CompositeVideoClip([video] + subtitle_clips)
        
        return final
    
    def cleanup(self):
        """Nettoie les fichiers temporaires"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Nettoyage: {self.temp_dir} supprimé")


def quick_assemble(project_id: int, **kwargs) -> str:
    """
    Helper pour assembler rapidement une vidéo.
    
    Args:
        project_id: ID du projet
        **kwargs: Options pour assembler()
    
    Returns:
        Chemin de la vidéo finale
    """
    project = VideoProject.objects.get(id=project_id)
    assembler = VideoAssembler(project)
    
    try:
        output = assembler.assemble(**kwargs)
        return output
    finally:
        assembler.cleanup()
