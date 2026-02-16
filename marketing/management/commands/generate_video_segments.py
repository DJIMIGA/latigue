"""
Commande Django pour générer une vidéo avec architecture segments.

Usage:
    python manage.py generate_video_segments --theme "Python tips" --pillar tips
    python manage.py generate_video_segments --theme "..." --provider runway --duration 45
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import time

from marketing.ai.segment_generator import generate_segmented_script, create_video_project_with_segments
from marketing.ai.video_segment_processor import VideoSegmentProcessor
from marketing.ai.video_assembler import VideoAssembler


class Command(BaseCommand):
    help = "Génère une vidéo complète avec architecture segments (nouveau workflow)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--theme',
            type=str,
            required=True,
            help='Thème de la vidéo (ex: "Python list comprehension tips")'
        )
        
        parser.add_argument(
            '--pillar',
            type=str,
            default='tips',
            choices=['education', 'demo', 'story', 'tips'],
            help='Pilier de contenu'
        )
        
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Durée totale souhaitée en secondes (défaut: 30)'
        )
        
        parser.add_argument(
            '--provider',
            type=str,
            default=None,
            choices=['luma', 'runway', 'pika', 'stability'],
            help='Provider vidéo à utiliser (défaut: config .env)'
        )
        
        parser.add_argument(
            '--parallel',
            action='store_true',
            help='Génère tous les segments en parallèle (plus rapide)'
        )
        
        parser.add_argument(
            '--no-voiceover',
            action='store_true',
            help='Ne pas ajouter de voix-off'
        )
        
        parser.add_argument(
            '--no-subtitles',
            action='store_true',
            help='Ne pas ajouter de sous-titres'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Chemin de sortie pour la vidéo finale'
        )
        
        parser.add_argument(
            '--ai-provider',
            type=str,
            default='anthropic',
            choices=['anthropic', 'openai'],
            help='Provider IA pour génération script (défaut: anthropic)'
        )
    
    def handle(self, *args, **options):
        theme = options['theme']
        pillar = options['pillar']
        duration = options['duration']
        provider = options['provider']
        parallel = options['parallel']
        ai_provider = options['ai_provider']
        
        self.stdout.write(self.style.HTTP_INFO("=" * 60))
        self.stdout.write(self.style.HTTP_INFO("🎬 GÉNÉRATION VIDÉO - ARCHITECTURE SEGMENTS"))
        self.stdout.write(self.style.HTTP_INFO("=" * 60))
        
        # Étape 1: Génération du script segmenté
        self.stdout.write(self.style.WARNING("\n📝 Étape 1/4: Génération du script segmenté"))
        self.stdout.write(f"   Theme: {theme}")
        self.stdout.write(f"   Pilier: {pillar}")
        self.stdout.write(f"   Durée: {duration}s")
        self.stdout.write(f"   IA: {ai_provider}")
        
        try:
            script_data = generate_segmented_script(
                pillar=pillar,
                theme=theme,
                total_duration=duration,
                segment_duration=5,
                provider=ai_provider
            )
            
            num_segments = len(script_data['segments'])
            self.stdout.write(self.style.SUCCESS(f"   ✓ Script généré avec {num_segments} segments"))
            
            # Affiche les segments
            for seg in script_data['segments']:
                self.stdout.write(f"     Segment {seg['order']}: {seg['text'][:50]}...")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Erreur: {str(e)}"))
            return
        
        # Étape 2: Création du projet
        self.stdout.write(self.style.WARNING("\n💾 Étape 2/4: Création du projet vidéo"))
        
        try:
            project = create_video_project_with_segments(script_data)
            self.stdout.write(self.style.SUCCESS(f"   ✓ Projet #{project.id} créé"))
            self.stdout.write(f"   URL Admin: /admin/marketing/videoproject/{project.id}/change/")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Erreur: {str(e)}"))
            return
        
        # Étape 3: Génération des segments vidéo
        self.stdout.write(self.style.WARNING("\n🎥 Étape 3/4: Génération des segments vidéo"))
        
        provider_name = provider or getattr(settings, 'VIDEO_PROVIDER', 'luma')
        self.stdout.write(f"   Provider: {provider_name}")
        self.stdout.write(f"   Mode: {'Parallèle' if parallel else 'Séquentiel'}")
        
        try:
            processor = VideoSegmentProcessor(project, provider_name=provider_name)
            
            # Estime le coût
            estimated_cost = processor.estimate_total_cost()
            self.stdout.write(f"   💰 Coût estimé: ${estimated_cost:.2f}")
            
            self.stdout.write(self.style.WARNING("   ⏳ Génération en cours (peut prendre 5-10 min)..."))
            
            start_time = time.time()
            segments = processor.generate_all_segments(parallel=parallel)
            elapsed = time.time() - start_time
            
            completed = sum(1 for seg in segments if seg.status == 'completed')
            failed = sum(1 for seg in segments if seg.status == 'failed')
            
            self.stdout.write(self.style.SUCCESS(f"   ✓ Génération terminée en {elapsed:.1f}s"))
            self.stdout.write(f"   Complétés: {completed}/{len(segments)}")
            
            if failed > 0:
                self.stdout.write(self.style.WARNING(f"   ⚠ Échecs: {failed}"))
            
            # Affiche les coûts réels
            total_cost = project.calculate_total_cost()
            self.stdout.write(f"   💰 Coût réel: ${total_cost:.2f}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Erreur: {str(e)}"))
            return
        
        # Étape 4: Assemblage final
        self.stdout.write(self.style.WARNING("\n🎬 Étape 4/4: Assemblage vidéo finale"))
        
        try:
            assembler = VideoAssembler(project)
            
            output_path = assembler.assemble(
                add_voiceover=not options['no_voiceover'],
                add_subtitles=not options['no_subtitles'],
                output_path=options.get('output')
            )
            
            self.stdout.write(self.style.SUCCESS(f"   ✓ Vidéo assemblée: {output_path}"))
            self.stdout.write(f"   Taille: {project.file_size_mb:.2f} MB")
            self.stdout.write(f"   Durée: {project.duration_seconds}s")
            
            # Nettoyage
            assembler.cleanup()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Erreur assemblage: {str(e)}"))
            return
        
        # Résumé final
        self.stdout.write(self.style.HTTP_INFO("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("✅ VIDÉO GÉNÉRÉE AVEC SUCCÈS"))
        self.stdout.write(self.style.HTTP_INFO("=" * 60))
        self.stdout.write(f"Projet ID: {project.id}")
        self.stdout.write(f"Fichier: {output_path}")
        self.stdout.write(f"Coût total: ${project.total_cost_usd or 0:.2f}")
        self.stdout.write(f"Caption: {script_data['caption']}")
        self.stdout.write(f"Hashtags: {' '.join(script_data['hashtags'])}")
        self.stdout.write(self.style.HTTP_INFO("=" * 60))
