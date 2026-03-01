"""
Management command pour importer les scripts vidéo depuis VIDEOS_RESEAUX_SOCIAUX.html
Usage: python manage.py import_video_scripts
"""

from django.core.management.base import BaseCommand
from marketing.models_extended import VideoScript, VideoTheme, ClientLevel, Platform
from bs4 import BeautifulSoup
import re
import os


class Command(BaseCommand):
    help = 'Importe les scripts vidéo depuis VIDEOS_RESEAUX_SOCIAUX.html'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='VIDEOS_RESEAUX_SOCIAUX.html',
            help='Chemin vers le fichier HTML'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer tous les scripts existants avant import'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Fichier non trouvé : {file_path}"))
            return
        
        if options['clear']:
            count = VideoScript.objects.count()
            VideoScript.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"✓ {count} scripts supprimés"))
        
        self.stdout.write(self.style.SUCCESS(f"Lecture de {file_path}..."))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Mapping thèmes
        theme_mapping = {
            'theme-argent': VideoTheme.ARGENT,
            'theme-temps': VideoTheme.TEMPS,
            'theme-tranquillite': VideoTheme.TRANQUILLITE,
            'theme-croissance': VideoTheme.CROISSANCE,
            'theme-ia': VideoTheme.IA,
            'theme-fidelite': VideoTheme.FIDELITE,
            'theme-mobile': VideoTheme.MOBILE,
            'theme-impression': VideoTheme.IMPRESSION,
        }
        
        imported = 0
        skipped = 0
        
        for theme_id, theme_value in theme_mapping.items():
            theme_section = soup.find('details', id=theme_id)
            if not theme_section:
                continue
            
            # Trouver tous les scripts dans ce thème
            video_details = theme_section.find_all('details', recursive=False)
            
            for idx, video in enumerate(video_details[1:], 1):  # Skip le premier (c'est le container)
                summary = video.find('summary')
                if not summary:
                    continue
                
                # Extraire le titre
                title_text = summary.get_text(strip=True)
                # Format: "Video A1 - Titre"
                match = re.match(r'Video\s+([A-Z]+\d+)\s*-\s*"?([^"]+)"?', title_text)
                if not match:
                    continue
                
                code = match.group(1)
                title = match.group(2).strip('"')
                
                # Extraire les segments
                script_blocks = video.find_all('div', class_='script-block')
                
                if len(script_blocks) < 6:
                    self.stdout.write(self.style.WARNING(f"⚠ {code} : structure incomplète"))
                    skipped += 1
                    continue
                
                def extract_text(block):
                    """Extrait le texte d'un script-block"""
                    paragraphs = block.find_all('p')
                    # Ignorer les paragraphes avec class="hint"
                    texts = [p.get_text(strip=True) for p in paragraphs if 'hint' not in p.get('class', [])]
                    return ' '.join(texts)
                
                def extract_hint(block):
                    """Extrait le hint d'un script-block"""
                    hint = block.find('p', class_='hint')
                    return hint.get_text(strip=True) if hint else ''
                
                hook = extract_text(script_blocks[0])
                problem = extract_text(script_blocks[1])
                micro_revelation = extract_text(script_blocks[2])
                solution = extract_text(script_blocks[3])
                solution_hint = extract_hint(script_blocks[3])
                proof = extract_text(script_blocks[4])
                cta = extract_text(script_blocks[5])
                
                # Créer ou mettre à jour le script
                script, created = VideoScript.objects.update_or_create(
                    code=code,
                    defaults={
                        'title': title,
                        'theme': theme_value,
                        'client_level': ClientLevel.TOUS,
                        'platform': Platform.ALL,
                        'duration_min': 30,
                        'duration_max': 60,
                        'hook': hook,
                        'hook_timing': '0-3s',
                        'problem': problem,
                        'problem_timing': '3-8s',
                        'micro_revelation': micro_revelation,
                        'micro_revelation_timing': '8-12s',
                        'solution': solution,
                        'solution_timing': '12-25s',
                        'solution_hint': solution_hint,
                        'proof': proof,
                        'proof_timing': '25-35s',
                        'cta': cta,
                        'cta_timing': '35-40s',
                        'tags': self.extract_tags(title, solution),
                    }
                )
                
                action = "créé" if created else "mis à jour"
                self.stdout.write(self.style.SUCCESS(f"✓ {code} - {title} ({action})"))
                imported += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Import terminé : {imported} scripts importés, {skipped} ignorés"))
    
    def extract_tags(self, title, solution):
        """Extrait des tags depuis le titre et la solution"""
        tags = []
        text = f"{title} {solution}".lower()
        
        # Tags courants
        tag_keywords = {
            'scanner': ['scan', 'code-barr', 'barcode'],
            'mobile': ['téléphone', 'smartphone', 'app', 'mobile'],
            'ia': ['ia', 'intelligence', 'photo'],
            'offline': ['sans internet', 'hors ligne', 'offline'],
            'stock': ['stock', 'inventaire'],
            'caisse': ['caisse', 'encaiss', 'vente'],
            'fidélité': ['fidélité', 'points', 'client'],
            'rapport': ['rapport', 'dashboard', 'statistique'],
            'multi-site': ['boutique', 'site', 'multi'],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
        
        return tags
