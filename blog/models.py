from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from PIL import Image
import os
import markdown
from django.core.files.base import ContentFile


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
    body = RichTextUploadingField(blank=True, null=True, help_text="Contenu de l'article en HTML. Peut être rempli automatiquement via un fichier Markdown.")
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
    markdown_file = models.FileField(
        upload_to='blog/markdown/',
        blank=True,
        null=True,
        help_text="Optionnel : Uploader un fichier Markdown (.md) pour générer automatiquement le contenu de l'article",
        validators=[FileExtensionValidator(allowed_extensions=['md', 'markdown', 'txt'])]
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
        
        # Vérifier si un fichier markdown a été uploadé
        markdown_uploaded = False
        if self.pk:
            try:
                old_instance = Post.objects.get(pk=self.pk)
                # Vérifier si le fichier markdown a changé
                if old_instance.markdown_file != self.markdown_file:
                    markdown_uploaded = True
            except Post.DoesNotExist:
                markdown_uploaded = bool(self.markdown_file)
        else:
            # Nouvelle instance
            markdown_uploaded = bool(self.markdown_file)
        
        # Sauvegarder d'abord pour que le fichier soit disponible sur le storage
        super().save(*args, **kwargs)
        
        # Si un fichier markdown est uploadé, convertir en HTML APRÈS la sauvegarde
        if markdown_uploaded and self.markdown_file:
            self.convert_markdown_to_html()
            # Sauvegarder à nouveau pour enregistrer le HTML dans body (sans déclencher les autres hooks)
            super().save(update_fields=['body'])
        
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
        
        # Optimiser l'image après la sauvegarde si elle a changé
        if thumbnail_changed and self.thumbnail:
            self.optimize_image()
    
    def convert_markdown_to_html(self):
        """Convertit le fichier markdown en HTML et l'injecte dans le body"""
        try:
            # Lire le contenu du fichier markdown
            if self.markdown_file and self.markdown_file.name:
                # Ouvrir le fichier depuis le storage (S3 ou local)
                # FieldFile.open ne supporte pas le paramètre "encoding", on lit donc en binaire
                # puis on décode en UTF-8.
                with self.markdown_file.open('rb') as f:
                    markdown_content = f.read().decode('utf-8')
                
                if not markdown_content.strip():
                    print(f"⚠️ Le fichier Markdown est vide pour l'article: {self.title}")
                    return
                
                # Convertir markdown en HTML
                html_content = markdown.markdown(
                    markdown_content,
                    extensions=[
                        'extra',  # Tables, fenced code blocks, etc.
                        'codehilite',  # Coloration syntaxique
                        'toc',  # Table of contents
                    ],
                    extension_configs={
                        'codehilite': {
                            'css_class': 'highlight',
                            'use_pygments': True,
                        },
                        'toc': {
                            'permalink': True,
                        }
                    }
                )
                
                # Injecter le HTML dans le body
                self.body = html_content
                print(f"✅ Markdown converti en HTML pour l'article: {self.title}")
                print(f"📝 Longueur du contenu HTML: {len(html_content)} caractères")
            else:
                print(f"⚠️ Aucun fichier Markdown trouvé pour l'article: {self.title}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la conversion du markdown: {e}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, on continue sans convertir

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
