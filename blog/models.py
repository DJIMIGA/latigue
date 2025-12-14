from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from PIL import Image
import os


class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-posts', kwargs={'category_slug': self.slug})


# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=225)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    body = RichTextUploadingField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("category", related_name="posts")
    thumbnail = models.ImageField(
        blank=True, 
        upload_to='blog',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Image de couverture recommandée : 1200x630px"
    )
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Description de l'image pour l'accessibilité et le SEO"
    )
    is_featured = models.BooleanField(
        default=False, 
        help_text="Article mis en avant sur la page d'accueil"
    )
    objects = models.Manager()

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Vérifier si l'image a changé (nouveau fichier uploadé)
        thumbnail_changed = False
        if self.pk:
            try:
                old_instance = Post.objects.get(pk=self.pk)
                if old_instance.thumbnail != self.thumbnail:
                    thumbnail_changed = True
            except Post.DoesNotExist:
                thumbnail_changed = True
        else:
            # Nouvelle instance, l'image est nouvelle
            thumbnail_changed = bool(self.thumbnail)
        
        # Sauvegarder d'abord pour que l'image soit disponible
        super().save(*args, **kwargs)
        
        # Optimiser l'image après la sauvegarde si elle a changé
        if thumbnail_changed and self.thumbnail:
            self.optimize_image()

    def optimize_image(self):
        """Optimise l'image de couverture (fonctionne avec S3 et stockage local)"""
        if not self.thumbnail:
            return
        
        try:
            # Ouvrir l'image depuis le storage (fonctionne avec S3 et local)
            with self.thumbnail.open('rb') as f:
                img = Image.open(f)
                img.load()  # Charger l'image complètement en mémoire
            
            # Vérifier si l'image a besoin d'optimisation
            needs_optimization = False
            if img.mode != 'RGB':
                needs_optimization = True
            if img.width > 1200:
                needs_optimization = True
            
            if not needs_optimization:
                return
            
            # Convertir en RGB si nécessaire
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si trop grande (max 1200px de large)
            if img.width > 1200:
                ratio = 1200 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
            
            # Sauvegarder l'image optimisée en mémoire
            from io import BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Sauvegarder via le storage backend (fonctionne avec S3 et local)
            from django.core.files.base import ContentFile
            file_name = self.thumbnail.name
            # Sauvegarder le fichier optimisé (remplace le fichier existant)
            # save=False évite de déclencher save() du modèle et une boucle infinie
            self.thumbnail.save(
                file_name,
                ContentFile(output.read()),
                save=False
            )
            # Note: Le fichier est déjà sauvegardé sur S3/local, pas besoin de mettre à jour le modèle
        except Exception as e:
            # En cas d'erreur, on continue sans optimiser
            print(f"Erreur lors de l'optimisation de l'image: {e}")

    def get_absolute_url(self):
        return reverse('blog-detail', kwargs={'slug': self.slug})

    def get_thumbnail_url(self):
        """Retourne l'URL de l'image de couverture ou une image par défaut"""
        if self.thumbnail:
            return self.thumbnail.url
        return '/static/portfolio/svg/default-blog.jpg'  # Image par défaut

    def get_reading_time(self):
        """Calcule le temps de lecture estimé"""
        word_count = len(self.body.split())
        reading_time = word_count / 200  # 200 mots par minute
        if reading_time < 1:
            return "~1 min"
        elif reading_time < 2:
            return "~2 min"
        elif reading_time < 5:
            return f"~{int(reading_time)} min"
        else:
            return f"~{int(reading_time)} min"
