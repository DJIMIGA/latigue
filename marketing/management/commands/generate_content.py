"""
Commande Django pour générer une vidéo complète de bout en bout

Usage:
    python manage.py generate_content --pillar tips --theme "Python tips"
    python manage.py generate_content --pillar education --theme "automatiser son business" --voice Bella --subtitles
"""
import os
import tempfile
from django.core.management.base import BaseCommand
from django.utils import timezone

from marketing.models import ContentScript, VideoProject
from marketing.ai import (
    generate_script,
    generate_images_for_script,
    generate_voiceover_from_script,
    create_video
)
from marketing.ai.image_generator import download_and_save_images
from marketing.storage import upload_video, upload_image, upload_audio


class Command(BaseCommand):
    help = 'Génère une vidéo complète (script → images → audio → vidéo → upload)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pillar',
            type=str,
            required=True,
            choices=['education', 'demo', 'story', 'tips'],
            help='Pilier de contenu'
        )
        parser.add_argument(
            '--theme',
            type=str,
            required=True,
            help='Thème de la vidéo'
        )
        parser.add_argument(
            '--voice',
            type=str,
            default='Adam',
            help='Voix ElevenLabs (Adam, Bella, Antoni...)'
        )
        parser.add_argument(
            '--subtitles',
            action='store_true',
            help='Activer les sous-titres automatiques (Whisper)'
        )
        parser.add_argument(
            '--no-upload',
            action='store_true',
            help='Ne pas uploader sur MinIO (sauvegarder localement uniquement)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Dossier de sortie local (défaut: /tmp/video_<id>)'
        )
    
    def handle(self, *args, **options):
        pillar = options['pillar']
        theme = options['theme']
        voice = options['voice']
        with_subtitles = options['subtitles']
        no_upload = options['no_upload']
        output_dir = options['output_dir']
        
        self.stdout.write(self.style.SUCCESS(f'\n🎬 Génération vidéo : {theme}'))
        self.stdout.write(f'   Pilier : {pillar}')
        self.stdout.write(f'   Voix : {voice}')
        self.stdout.write(f'   Sous-titres : {"Oui" if with_subtitles else "Non"}')
        self.stdout.write('')
        
        try:
            # 1. Générer le script
            self.stdout.write('📝 Étape 1/5 : Génération du script...')
            script_data = generate_script(pillar, theme)
            
            # Sauvegarder le script en DB
            script = ContentScript.objects.create(
                pillar=pillar,
                theme=theme,
                script_json=script_data['script'],
                caption=script_data['caption'],
                hashtags=script_data['hashtags']
            )
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Script créé (ID: {script.id})'))
            self.stdout.write(f'   📝 Caption : {script_data["caption"][:80]}...')
            self.stdout.write(f'   🏷️ Hashtags : {script_data["hashtags"][:80]}...')
            
            # Créer le projet vidéo
            project = VideoProject.objects.create(
                script=script,
                status='script'
            )
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Projet vidéo créé (ID: {project.id})'))
            self.stdout.write('')
            
            # Créer dossier temporaire
            if output_dir is None:
                output_dir = os.path.join(tempfile.gettempdir(), f'video_{project.id}')
            
            os.makedirs(output_dir, exist_ok=True)
            self.stdout.write(f'📁 Dossier de travail : {output_dir}')
            self.stdout.write('')
            
            # 2. Générer les images
            self.stdout.write('🎨 Étape 2/5 : Génération des images (DALL-E 3)...')
            image_results = generate_images_for_script(script_data)
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(image_results)} images générées'))
            
            # Télécharger et sauvegarder les images
            image_paths = download_and_save_images(image_results, output_dir, project.id)
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(image_paths)} images sauvegardées'))
            
            # Upload vers MinIO
            image_urls = []
            if not no_upload:
                for i, img_path in enumerate(image_paths):
                    url = upload_image(img_path, project.id, i)
                    image_urls.append(url)
                
                project.images_urls = image_urls
                project.status = 'images'
                project.save()
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Images uploadées sur MinIO'))
            
            self.stdout.write('')
            
            # 3. Générer la voix-off
            self.stdout.write(f'🎤 Étape 3/5 : Génération voix-off (ElevenLabs - {voice})...')
            
            audio_path = os.path.join(output_dir, 'voiceover.mp3')
            generate_voiceover_from_script(script_data, audio_path, voice=voice)
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Voix-off générée : {audio_path}'))
            
            # Upload vers MinIO
            audio_url = None
            if not no_upload:
                audio_url = upload_audio(audio_path, project.id)
                project.audio_url = audio_url
                project.status = 'audio'
                project.save()
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Audio uploadé sur MinIO'))
            
            self.stdout.write('')
            
            # 4. Montage vidéo
            self.stdout.write('🎬 Étape 4/5 : Montage vidéo (MoviePy)...')
            
            video_path = os.path.join(output_dir, 'final.mp4')
            
            video_metadata = create_video(
                image_paths,
                audio_path,
                video_path,
                with_subtitles=with_subtitles
            )
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Vidéo créée : {video_path}'))
            self.stdout.write(f'   ⏱️ Durée : {video_metadata["duration"]:.2f}s')
            self.stdout.write(f'   💾 Taille : {video_metadata["file_size_mb"]}MB')
            self.stdout.write(f'   📐 Résolution : {video_metadata["resolution"]}')
            
            # Upload vers MinIO
            video_url = None
            if not no_upload:
                video_url = upload_video(video_path, project.id)
                project.video_url = video_url
                project.duration_seconds = int(video_metadata['duration'])
                project.file_size_mb = video_metadata['file_size_mb']
                project.status = 'video'
                project.save()
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Vidéo uploadée sur MinIO'))
            
            self.stdout.write('')
            
            # 5. Résumé final
            self.stdout.write(self.style.SUCCESS('✅ Étape 5/5 : Production terminée !'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
            self.stdout.write(self.style.SUCCESS('🎉 Vidéo générée avec succès !'))
            self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
            self.stdout.write('')
            self.stdout.write(f'📊 Projet vidéo : #{project.id}')
            self.stdout.write(f'📝 Script : #{script.id} - {theme}')
            self.stdout.write(f'📁 Fichiers locaux : {output_dir}')
            
            if not no_upload:
                self.stdout.write('')
                self.stdout.write('🌐 URLs MinIO :')
                self.stdout.write(f'   Vidéo : {video_url}')
                self.stdout.write(f'   Audio : {audio_url}')
                self.stdout.write(f'   Images : {len(image_urls)} fichiers')
            
            self.stdout.write('')
            self.stdout.write('📱 Prochaines étapes :')
            self.stdout.write('   1. Visualiser la vidéo')
            self.stdout.write('   2. Accéder à l\'admin Django : /admin/marketing/videoproject/')
            self.stdout.write('   3. Publier sur TikTok/Instagram (Phase 3)')
            self.stdout.write('')
            
            # Afficher le caption et hashtags pour copier-coller
            self.stdout.write('📋 Copier-coller pour publication :')
            self.stdout.write('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            self.stdout.write(script.caption)
            self.stdout.write('')
            self.stdout.write(script.hashtags)
            self.stdout.write('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            self.stdout.write('')
        
        except Exception as e:
            # Marquer le projet comme erreur
            if 'project' in locals():
                project.status = 'error'
                project.error_message = str(e)
                project.save()
            
            self.stdout.write(self.style.ERROR(f'\n❌ Erreur : {e}'))
            self.stdout.write(self.style.ERROR('\nLa production a échoué. Vérifiez :'))
            self.stdout.write('   - Les API keys (OPENAI_API_KEY, ELEVENLABS_API_KEY)')
            self.stdout.write('   - La connexion MinIO (MINIO_ENDPOINT)')
            self.stdout.write('   - Les dépendances (pip install -r requirements-marketing.txt)')
            self.stdout.write('   - FFmpeg installé (apt-get install ffmpeg)')
            
            import traceback
            self.stdout.write(self.style.ERROR(f'\nStacktrace :\n{traceback.format_exc()}'))
            
            raise
