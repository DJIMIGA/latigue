"""
Pipeline d'assemblage vidéo hybride.
Assemble clips filmés + segments IA + sous-titres + musique.
Format final : 9:16 TikTok/Reels (1080x1920)
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from django.conf import settings


# Dimensions TikTok
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30


class VideoAssembler:
    """
    Assemble les segments d'un job en une vidéo finale.
    Utilise FFmpeg directement (plus fiable que MoviePy pour le concat).
    """
    
    def __init__(self, job):
        self.job = job
        self.output_dir = os.path.join(settings.MEDIA_ROOT, 'marketing', 'output', str(job.pk))
        os.makedirs(self.output_dir, exist_ok=True)
    
    def assemble(self, add_subtitles=True, music_path=None):
        """
        Assemble tous les segments en une vidéo finale.
        
        Args:
            add_subtitles: Ajouter sous-titres depuis le script
            music_path: Chemin vers musique de fond (optionnel)
        
        Returns:
            str: Chemin du fichier vidéo final
        """
        segments = self.job.generations.order_by('segment_index')
        
        if not segments.exists():
            raise ValueError("Aucun segment à assembler")
        
        # 1. Préparer les fichiers de chaque segment
        segment_files = []
        for seg in segments:
            file_path = self._get_segment_file(seg)
            if file_path:
                # Normaliser le segment (résolution, fps, codec)
                normalized = self._normalize_segment(file_path, seg.segment_index)
                segment_files.append(normalized)
        
        if not segment_files:
            raise ValueError("Aucun fichier segment disponible")
        
        # 2. Concat avec FFmpeg
        concat_path = self._concat_segments(segment_files)
        
        # 3. Ajouter sous-titres
        if add_subtitles:
            srt_path = self._generate_srt()
            if srt_path:
                concat_path = self._burn_subtitles(concat_path, srt_path)
        
        # 4. Ajouter musique de fond
        if music_path and os.path.exists(music_path):
            concat_path = self._add_music(concat_path, music_path)
        
        # 5. Déplacer vers output final
        final_path = os.path.join(self.output_dir, f"final_{self.job.pk}.mp4")
        os.rename(concat_path, final_path)
        
        # 6. Update job
        self.job.final_video_path = final_path
        self.job.status = 'completed'
        self.job.save()
        
        return final_path
    
    def _get_segment_file(self, segment):
        """
        Récupère le fichier vidéo d'un segment.
        - uploaded_clip : fichier uploadé
        - ai_generated : télécharger depuis video_url
        """
        if segment.source_type == 'uploaded_clip' and segment.uploaded_clip:
            return segment.uploaded_clip.path
        
        if segment.video_url:
            return self._download_video(segment.video_url, segment.segment_index)
        
        if segment.local_path and os.path.exists(segment.local_path):
            return segment.local_path
        
        return None
    
    def _download_video(self, url, index):
        """Télécharge une vidéo depuis une URL"""
        import requests
        
        output_path = os.path.join(self.output_dir, f"segment_{index}_raw.mp4")
        
        if os.path.exists(output_path):
            return output_path
        
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
    
    def _normalize_segment(self, input_path, index):
        """
        Normalise un segment : résolution 1080x1920, 30fps, même codec.
        Gère les clips filmés (potentiellement différentes résolutions).
        """
        output_path = os.path.join(self.output_dir, f"segment_{index}_norm.mp4")
        
        if os.path.exists(output_path):
            return output_path
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            # Scale + pad pour forcer 9:16 sans déformer
            '-vf', (
                f'scale={TARGET_WIDTH}:{TARGET_HEIGHT}:'
                f'force_original_aspect_ratio=decrease,'
                f'pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black'
            ),
            '-r', str(TARGET_FPS),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-ar', '44100', '-ac', '2',
            '-movflags', '+faststart',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            # Si pas d'audio dans le source, ajouter silence
            cmd_no_audio = [
                'ffmpeg', '-y', '-i', input_path,
                '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                '-vf', (
                    f'scale={TARGET_WIDTH}:{TARGET_HEIGHT}:'
                    f'force_original_aspect_ratio=decrease,'
                    f'pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black'
                ),
                '-r', str(TARGET_FPS),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-ar', '44100', '-ac', '2',
                '-shortest',
                '-movflags', '+faststart',
                output_path
            ]
            subprocess.run(cmd_no_audio, capture_output=True, text=True, timeout=120)
        
        return output_path
    
    def _concat_segments(self, segment_files):
        """Concatène tous les segments normalisés"""
        concat_path = os.path.join(self.output_dir, f"concat_{self.job.pk}.mp4")
        
        # Créer fichier liste pour FFmpeg concat
        list_path = os.path.join(self.output_dir, "concat_list.txt")
        with open(list_path, 'w') as f:
            for seg_file in segment_files:
                f.write(f"file '{seg_file}'\n")
        
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', list_path,
            '-c', 'copy',
            '-movflags', '+faststart',
            concat_path
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return concat_path
    
    def _generate_srt(self):
        """
        Génère un fichier SRT depuis les prompts/scripts des segments.
        Style TikTok : texte court par segment.
        """
        srt_path = os.path.join(self.output_dir, f"subtitles_{self.job.pk}.srt")
        
        segments = self.job.generations.order_by('segment_index')
        
        current_time = 0.0
        srt_entries = []
        
        for i, seg in enumerate(segments, 1):
            start = current_time
            end = current_time + seg.duration
            
            # Texte du sous-titre (prompt = texte du script)
            text = seg.prompt.strip()
            # Limiter à 2 lignes de ~40 chars
            if len(text) > 80:
                mid = len(text) // 2
                # Trouver l'espace le plus proche du milieu
                space = text.rfind(' ', 0, mid + 10)
                if space > 0:
                    text = text[:space] + '\n' + text[space+1:]
            
            srt_entries.append(
                f"{i}\n"
                f"{self._format_srt_time(start)} --> {self._format_srt_time(end)}\n"
                f"{text}\n"
            )
            
            current_time = end
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_entries))
        
        return srt_path
    
    def _burn_subtitles(self, video_path, srt_path):
        """Brûle les sous-titres dans la vidéo (style TikTok)"""
        output_path = os.path.join(self.output_dir, f"subtitled_{self.job.pk}.mp4")
        
        # Style TikTok : blanc, gras, ombre, centré en bas
        subtitle_style = (
            "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BackColour=&H80000000,"
            "Bold=1,Outline=2,Shadow=1,Alignment=2,MarginV=80"
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy',
            '-movflags', '+faststart',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            # Si erreur sous-titres, retourner vidéo sans
            return video_path
        
        return output_path
    
    def _add_music(self, video_path, music_path, volume=0.15):
        """Ajoute musique de fond avec volume réduit"""
        output_path = os.path.join(self.output_dir, f"final_music_{self.job.pk}.mp4")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', music_path,
            '-filter_complex', (
                f'[1:a]volume={volume}[bg];'
                '[0:a][bg]amix=inputs=2:duration=first[aout]'
            ),
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-movflags', '+faststart',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return video_path
        
        return output_path
    
    @staticmethod
    def _format_srt_time(seconds):
        """Convertit secondes en format SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
