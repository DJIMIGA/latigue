"""
Command pour setup l'interface web marketing (templates, fixtures).
Usage: python manage.py setup_marketing_interface
"""

from django.core.management.base import BaseCommand
from marketing.models_extended import VideoProjectTemplate, ContentPillar


class Command(BaseCommand):
    help = 'Setup interface web marketing (templates par défaut)'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setup interface marketing...'))
        
        # Créer templates par défaut
        templates_data = [
            {
                'name': 'Reels 30s Standard',
                'description': 'Format standard TikTok/Reels/YouTube Shorts 30 secondes',
                'pillar': ContentPillar.TIPS,
                'segments_count': 6,
                'segment_duration': 5,
                'default_config': {
                    'provider': 'luma',
                    'mode': 'text_to_video',
                    'aspect_ratio': '9:16',
                }
            },
            {
                'name': 'YouTube Short 60s',
                'description': 'YouTube Shorts format long (60 secondes)',
                'pillar': ContentPillar.EDUCATION,
                'segments_count': 12,
                'segment_duration': 5,
                'default_config': {
                    'provider': 'luma',
                    'mode': 'text_to_video',
                    'aspect_ratio': '9:16',
                }
            },
            {
                'name': 'Démo Produit 45s',
                'description': 'Démo produit avec screenshots (image-to-video)',
                'pillar': ContentPillar.DEMO,
                'segments_count': 9,
                'segment_duration': 5,
                'default_config': {
                    'provider': 'luma',
                    'mode': 'image_to_video',
                    'aspect_ratio': '9:16',
                }
            },
            {
                'name': 'Story 20s Court',
                'description': 'Storytelling court format',
                'pillar': ContentPillar.STORY,
                'segments_count': 4,
                'segment_duration': 5,
                'default_config': {
                    'provider': 'luma',
                    'mode': 'text_to_video',
                    'aspect_ratio': '9:16',
                }
            },
            {
                'name': 'YouTube Horizontal 30s',
                'description': 'Format horizontal classique YouTube',
                'pillar': ContentPillar.EDUCATION,
                'segments_count': 6,
                'segment_duration': 5,
                'default_config': {
                    'provider': 'luma',
                    'mode': 'text_to_video',
                    'aspect_ratio': '16:9',
                }
            },
        ]
        
        created_count = 0
        for template_data in templates_data:
            template, created = VideoProjectTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Template créé: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Template existe déjà: {template.name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Setup terminé ! {created_count} templates créés.'
            )
        )
        self.stdout.write('')
        self.stdout.write('🌐 Interface disponible sur:')
        self.stdout.write('  - Dashboard: /marketing/')
        self.stdout.write('  - Admin: /admin/marketing/')
        self.stdout.write('')
