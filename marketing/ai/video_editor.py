"""
Montage vidéo automatique avec MoviePy
"""
import os
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    TextClip, CompositeVideoClip
)
from moviepy.video.fx.resize import resize


class VideoEditor:
    """Montage vidéo automatique pour Reels/TikTok"""
    
    def __init__(self):
        """Initialise les paramètres de montage"""
        # Format vertical pour Reels/TikTok (9:16)
        self.width = 1080
        self.height = 1920
        self.fps = 30
        
        # Style sous-titres
        self.subtitle_font = 'Arial-Bold'
        self.subtitle_fontsize = 60
        self.subtitle_color = 'white'
        self.subtitle_bg_color = 'black'
        self.subtitle_position = ('center', 'center')
    
    def create_video_from_images(
        self,
        image_paths: list,
        audio_path: str,
        output_path: str,
        subtitles: list = None,
        transition_duration: float = 0.5
    ):
        """
        Crée une vidéo à partir d'images et d'un audio
        
        Args:
            image_paths: Liste de chemins d'images
            audio_path: Chemin du fichier audio (voix-off)
            output_path: Chemin de sauvegarde de la vidéo
            subtitles: Liste de dicts {'text': ..., 'start': ..., 'duration': ...}
            transition_duration: Durée des transitions entre images (secondes)
        """
        if not image_paths:
            raise ValueError("Aucune image fournie")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")
        
        # Charger l'audio pour connaître la durée totale
        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        
        print(f"🎬 Durée audio : {total_duration:.2f}s")
        print(f"🖼️ Nombre d'images : {len(image_paths)}")
        
        # Calculer la durée par image
        duration_per_image = total_duration / len(image_paths)
        
        # Créer les clips d'images
        clips = []
        for i, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                print(f"⚠️ Image ignorée (introuvable) : {img_path}")
                continue
            
            try:
                # Créer le clip d'image
                clip = ImageClip(img_path, duration=duration_per_image)
                
                # Redimensionner au format 9:16
                clip = clip.resize(height=self.height)
                
                # Si l'image est trop large, recadrer au centre
                if clip.w > self.width:
                    clip = clip.crop(
                        x_center=clip.w/2,
                        width=self.width,
                        height=self.height
                    )
                # Si l'image est trop étroite, ajouter des bandes noires
                elif clip.w < self.width:
                    clip = clip.margin(
                        left=(self.width - clip.w) // 2,
                        right=(self.width - clip.w) // 2,
                        color=(0, 0, 0)
                    )
                
                clips.append(clip)
                print(f"✅ Image {i+1}/{len(image_paths)} : {duration_per_image:.2f}s")
            
            except Exception as e:
                print(f"⚠️ Erreur image {i+1}: {e}")
        
        if not clips:
            raise ValueError("Aucun clip d'image valide créé")
        
        # Concaténer les clips
        print("🔗 Concatenation des clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Ajouter l'audio
        print("🎵 Ajout de l'audio...")
        final_clip = final_clip.set_audio(audio)
        
        # Ajouter les sous-titres si fournis
        if subtitles:
            print("📝 Ajout des sous-titres...")
            final_clip = self._add_subtitles(final_clip, subtitles)
        
        # Exporter la vidéo
        print(f"💾 Export vidéo vers {output_path}...")
        final_clip.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',  # 'ultrafast', 'fast', 'medium', 'slow'
            threads=4
        )
        
        # Libérer la mémoire
        final_clip.close()
        audio.close()
        
        print(f"✅ Vidéo créée : {output_path}")
        
        # Retourner les métadonnées
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        return {
            'duration': total_duration,
            'file_size_mb': round(file_size_mb, 2),
            'resolution': f"{self.width}x{self.height}",
            'fps': self.fps
        }
    
    def _add_subtitles(self, video_clip, subtitles: list):
        """
        Ajoute des sous-titres sur la vidéo
        
        Args:
            video_clip: Clip vidéo MoviePy
            subtitles: Liste de dicts {'text': ..., 'start': ..., 'duration': ...}
        
        Returns:
            Clip vidéo avec sous-titres
        """
        subtitle_clips = []
        
        for sub in subtitles:
            try:
                txt_clip = TextClip(
                    sub['text'],
                    fontsize=self.subtitle_fontsize,
                    color=self.subtitle_color,
                    font=self.subtitle_font,
                    method='caption',
                    size=(self.width - 100, None),  # Largeur avec marges
                    bg_color=self.subtitle_bg_color
                )
                
                # Positionner le sous-titre
                txt_clip = txt_clip.set_position(self.subtitle_position)
                txt_clip = txt_clip.set_start(sub['start'])
                txt_clip = txt_clip.set_duration(sub['duration'])
                
                subtitle_clips.append(txt_clip)
            
            except Exception as e:
                print(f"⚠️ Erreur sous-titre '{sub['text'][:30]}...' : {e}")
        
        if subtitle_clips:
            # Composer la vidéo avec les sous-titres
            return CompositeVideoClip([video_clip] + subtitle_clips)
        
        return video_clip
    
    def create_simple_video(
        self,
        image_paths: list,
        audio_path: str,
        output_path: str
    ):
        """
        Version simplifiée sans sous-titres
        
        Args:
            image_paths: Liste de chemins d'images
            audio_path: Chemin du fichier audio
            output_path: Chemin de sauvegarde
        """
        return self.create_video_from_images(
            image_paths,
            audio_path,
            output_path,
            subtitles=None
        )


def transcribe_audio(audio_path: str) -> list:
    """
    Transcrit un audio en sous-titres avec Whisper (OpenAI)
    
    Args:
        audio_path: Chemin du fichier audio
    
    Returns:
        Liste de dicts {'text': ..., 'start': ..., 'duration': ...}
    
    Note:
        Nécessite `openai-whisper` installé OU utilise l'API OpenAI
    """
    try:
        import whisper
        
        # Charger le modèle Whisper (local)
        model = whisper.load_model("base")  # "tiny", "base", "small", "medium", "large"
        
        # Transcrire
        result = model.transcribe(audio_path, language="fr")
        
        # Convertir en format sous-titres
        subtitles = []
        for segment in result['segments']:
            subtitles.append({
                'text': segment['text'].strip(),
                'start': segment['start'],
                'duration': segment['end'] - segment['start']
            })
        
        return subtitles
    
    except ImportError:
        print("⚠️ Whisper non installé. Utilisation de l'API OpenAI à la place...")
        return transcribe_audio_api(audio_path)
    
    except Exception as e:
        print(f"❌ Erreur transcription : {e}")
        return []


def transcribe_audio_api(audio_path: str) -> list:
    """
    Transcrit un audio avec l'API OpenAI Whisper
    
    Args:
        audio_path: Chemin du fichier audio
    
    Returns:
        Liste de dicts {'text': ..., 'start': ..., 'duration': ...}
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        with open(audio_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                language="fr"
            )
        
        # L'API retourne des segments avec timestamps
        subtitles = []
        if hasattr(response, 'segments'):
            for segment in response.segments:
                subtitles.append({
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['end'] - segment['start']
                })
        else:
            # Format simple sans timestamps
            # Diviser en segments manuellement (approximatif)
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()
            
            text = response.text
            words = text.split()
            words_per_second = len(words) / duration
            segment_duration = 3  # 3 secondes par sous-titre
            
            current_time = 0
            while current_time < duration:
                words_in_segment = int(words_per_second * segment_duration)
                segment_text = ' '.join(words[:words_in_segment])
                words = words[words_in_segment:]
                
                if segment_text:
                    subtitles.append({
                        'text': segment_text,
                        'start': current_time,
                        'duration': min(segment_duration, duration - current_time)
                    })
                
                current_time += segment_duration
        
        return subtitles
    
    except Exception as e:
        print(f"❌ Erreur transcription API : {e}")
        return []


# Fonctions helpers pour usage rapide
def create_video(
    image_paths: list,
    audio_path: str,
    output_path: str,
    with_subtitles: bool = False
) -> dict:
    """
    Fonction rapide pour créer une vidéo
    
    Args:
        image_paths: Liste de chemins d'images
        audio_path: Chemin du fichier audio
        output_path: Chemin de sauvegarde
        with_subtitles: Activer les sous-titres automatiques (Whisper)
    
    Returns:
        {'duration': ..., 'file_size_mb': ..., 'resolution': ..., 'fps': ...}
    
    Usage:
        from marketing.ai.video_editor import create_video
        
        images = ['/tmp/img_0.png', '/tmp/img_1.png', '/tmp/img_2.png']
        audio = '/tmp/voiceover.mp3'
        
        metadata = create_video(images, audio, '/tmp/final.mp4', with_subtitles=True)
        print(f"✅ Vidéo : {metadata['duration']}s, {metadata['file_size_mb']}MB")
    """
    editor = VideoEditor()
    
    subtitles = None
    if with_subtitles:
        print("🎤 Transcription audio pour sous-titres...")
        subtitles = transcribe_audio(audio_path)
        print(f"✅ {len(subtitles)} sous-titres générés")
    
    return editor.create_video_from_images(
        image_paths,
        audio_path,
        output_path,
        subtitles=subtitles
    )


if __name__ == '__main__':
    # Test rapide
    print("🎬 VideoEditor - Module de montage vidéo")
    print("Usage:")
    print("  from marketing.ai.video_editor import create_video")
    print("  metadata = create_video(images, audio, output_path)")
    
    # Test avec des images factices (si disponibles)
    # images = ['/tmp/img_0.png', '/tmp/img_1.png', '/tmp/img_2.png']
    # audio = '/tmp/voiceover.mp3'
    # output = '/tmp/test_video.mp4'
    # create_video(images, audio, output, with_subtitles=False)
