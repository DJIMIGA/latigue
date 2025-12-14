from django.core.management.base import BaseCommand
from blog.models import Post
from PIL import Image
import os


class Command(BaseCommand):
    help = 'Optimise toutes les images de couverture des articles de blog'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer l\'optimisation même si l\'image existe déjà',
        )

    def handle(self, *args, **options):
        posts = Post.objects.filter(thumbnail__isnull=False)
        
        if not posts.exists():
            self.stdout.write(
                self.style.WARNING('Aucun article avec image de couverture trouvé.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Optimisation de {posts.count()} images...')
        )

        optimized_count = 0
        error_count = 0

        for post in posts:
            try:
                if post.thumbnail:
                    # Vérifier si l'image existe
                    if not os.path.exists(post.thumbnail.path):
                        self.stdout.write(
                            self.style.ERROR(f'Image manquante pour "{post.title}"')
                        )
                        error_count += 1
                        continue

                    # Ouvrir l'image
                    img = Image.open(post.thumbnail.path)
                    
                    # Convertir en RGB si nécessaire
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Redimensionner si trop grande
                    original_size = img.size
                    if img.width > 1200:
                        ratio = 1200 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                        self.stdout.write(
                            f'  ✓ "{post.title}" : {original_size} → {img.size}'
                        )
                    else:
                        self.stdout.write(f'  ✓ "{post.title}" : {img.size} (taille OK)')
                    
                    # Sauvegarder avec compression
                    img.save(post.thumbnail.path, 'JPEG', quality=85, optimize=True)
                    optimized_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur lors de l\'optimisation de "{post.title}": {str(e)}')
                )
                error_count += 1

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Optimisation terminée !')
        )
        self.stdout.write(f'  ✓ Images optimisées : {optimized_count}')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Erreurs : {error_count}')
            )
        
        # Conseils
        self.stdout.write('\nConseils pour les futures images :')
        self.stdout.write('  • Format recommandé : JPEG ou PNG')
        self.stdout.write('  • Taille recommandée : 1200x630px')
        self.stdout.write('  • Poids maximum : 500KB')
        self.stdout.write('  • N\'oubliez pas d\'ajouter un alt_text pour l\'accessibilité') 