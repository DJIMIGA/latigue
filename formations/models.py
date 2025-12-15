from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField

class Formation(models.Model):
    LEVEL_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = RichTextField(verbose_name="Description")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name="Niveau")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    duration = models.CharField(max_length=100, verbose_name="Durée")
    prerequisites = RichTextField(verbose_name="Prérequis")
    program = RichTextField(verbose_name="Programme")
    image = models.ImageField(upload_to='formations/', verbose_name="Image", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'level']),  # Index composite pour les filtres
            models.Index(fields=['slug']),  # Index pour les recherches par slug
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title 