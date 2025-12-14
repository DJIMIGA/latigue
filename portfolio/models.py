from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.urls import reverse


class Profile(models.Model):
    """
    Modèle singleton pour gérer les informations du profil (photo, nom, etc.)
    Il ne devrait y avoir qu'une seule instance de ce modèle.
    """
    name = models.CharField(max_length=200, verbose_name="Nom complet", default="Djimiga Konimba")
    title = models.CharField(max_length=200, verbose_name="Titre professionnel", default="AppBuilder with Prompt & Supervision")
    profile_image = models.ImageField(
        upload_to='image/',
        verbose_name="Photo de profil",
        help_text="Photo de profil affichée à l'accueil (recommandé: 400x400px)",
        blank=True,
        null=True
    )
    bio = models.TextField(
        verbose_name="Biographie",
        blank=True,
        help_text="Description courte affichée sur la page d'accueil"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Profil - {self.name}"

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule instance
        if not self.pk and Profile.objects.exists():
            raise ValidationError("Il ne peut y avoir qu'une seule instance de Profile.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_profile(cls):
        """Retourne l'instance unique du profil, ou la crée si elle n'existe pas"""
        profile, created = cls.objects.get_or_create(pk=1)
        return profile


class Experience(models.Model):
    """
    Modèle pour gérer les expériences professionnelles dans la timeline
    """
    POSITION_CHOICES = [
        ('left', 'Gauche'),
        ('right', 'Droite'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre du poste")
    company = models.CharField(max_length=200, verbose_name="Entreprise/Organisation", blank=True)
    period = models.CharField(
        max_length=100, 
        verbose_name="Période",
        help_text="Ex: 2020 - Présent, 2018 - 2019"
    )
    description = models.TextField(verbose_name="Description")
    logo = models.ImageField(
        upload_to='timeline/',
        verbose_name="Logo",
        help_text="Logo de l'entreprise (recommandé: 200x200px)",
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Ordre d'affichage dans la timeline (plus petit = plus haut)"
    )
    position = models.CharField(
        max_length=10,
        choices=POSITION_CHOICES,
        default='left',
        verbose_name="Position sur la timeline",
        help_text="Position de l'élément sur la timeline"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Afficher cette expérience dans la timeline"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Expérience"
        verbose_name_plural = "Expériences"
        ordering = ['order', '-created_at']

    def __str__(self):
        company_part = f" - {self.company}" if self.company else ""
        return f"{self.title}{company_part} ({self.period})"


class Portfolio(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    technology = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to="media", blank=True, null=True)
    lien = models.URLField(blank=True, null=True)
    lien_github = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True, help_text="Généré automatiquement à partir du titre si non fourni")

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Projet Portfolio"
        verbose_name_plural = "Projets Portfolio"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Générer le slug automatiquement s'il n'est pas fourni
        if not self.slug:
            self.slug = slugify(self.title)
            # S'assurer que le slug est unique
            original_slug = self.slug
            counter = 1
            while Portfolio.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Retourne l'URL de détail du projet (si une vue de détail existe)"""
        # Pour l'instant, retourne le lien externe ou la page d'accueil
        if self.lien:
            return self.lien
        return reverse('portfolio-index')
