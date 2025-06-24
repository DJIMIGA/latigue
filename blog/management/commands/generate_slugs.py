from django.core.management.base import BaseCommand
from blog.models import Post, Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Génère les slugs manquants pour les articles et catégories'

    def handle(self, *args, **options):
        # Générer les slugs pour les catégories
        categories_updated = 0
        for category in Category.objects.all():
            if not category.slug:
                base_slug = slugify(category.name)
                slug = base_slug
                counter = 1
                # S'assurer que le slug est unique
                while Category.objects.filter(slug=slug).exclude(id=category.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                category.slug = slug
                category.save()
                categories_updated += 1
                self.stdout.write(f"✅ Slug généré pour la catégorie '{category.name}': {slug}")

        # Générer les slugs pour les articles
        posts_updated = 0
        for post in Post.objects.all():
            if not post.slug:
                base_slug = slugify(post.title)
                slug = base_slug
                counter = 1
                # S'assurer que le slug est unique
                while Post.objects.filter(slug=slug).exclude(id=post.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                post.slug = slug
                post.save()
                posts_updated += 1
                self.stdout.write(f"✅ Slug généré pour l'article '{post.title}': {slug}")

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Génération terminée ! {categories_updated} catégories et {posts_updated} articles mis à jour.'
            )
        ) 