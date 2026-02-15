from django.db import models
from django.utils import timezone


class ContentScript(models.Model):
    """Script généré par IA pour une vidéo Reels/TikTok"""
    
    PILLAR_CHOICES = [
        ('education', 'Éducation / Partage de savoir'),
        ('demo', 'Démo BoliBana Stock'),
        ('story', 'Storytelling / Parcours'),
        ('tips', 'Tips Dev & Tech'),
    ]
    
    pillar = models.CharField(max_length=20, choices=PILLAR_CHOICES, verbose_name="Pilier de contenu")
    theme = models.CharField(max_length=200, verbose_name="Thème")
    script_json = models.JSONField(help_text="Structure: {hook, content, cta, timing, voiceover, image_prompts}")
    hashtags = models.TextField(verbose_name="Hashtags")
    caption = models.TextField(verbose_name="Légende")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Script de contenu"
        verbose_name_plural = "Scripts de contenu"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_pillar_display()} - {self.theme}"


class VideoProject(models.Model):
    """Projet vidéo en cours de production"""
    
    STATUS_CHOICES = [
        ('script', 'Script créé'),
        ('images', 'Images générées'),
        ('audio', 'Audio généré'),
        ('video', 'Vidéo montée'),
        ('uploaded', 'Vidéo uploadée'),
        ('published', 'Publiée'),
        ('error', 'Erreur'),
    ]
    
    script = models.ForeignKey(ContentScript, on_delete=models.CASCADE, related_name='videos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='script')
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    
    # URLs des assets générés
    images_urls = models.JSONField(default=list, help_text="Liste des URLs des images générées")
    audio_url = models.URLField(blank=True, verbose_name="URL audio voix-off")
    video_url = models.URLField(blank=True, verbose_name="URL vidéo finale")
    storage_path = models.CharField(max_length=500, blank=True, help_text="Chemin S3/R2")
    
    # Métadonnées
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name="Durée (secondes)")
    file_size_mb = models.FloatField(null=True, blank=True, verbose_name="Taille fichier (MB)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet vidéo"
        verbose_name_plural = "Projets vidéo"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vidéo #{self.id} - {self.script.theme} ({self.get_status_display()})"


class Publication(models.Model):
    """Publication d'une vidéo sur un réseau social"""
    
    PLATFORM_CHOICES = [
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram Reels'),
        ('facebook', 'Facebook Reels'),
        ('youtube', 'YouTube Shorts'),
    ]
    
    video = models.ForeignKey(VideoProject, on_delete=models.CASCADE, related_name='publications')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_post_id = models.CharField(max_length=200, blank=True, verbose_name="ID du post")
    platform_url = models.URLField(blank=True, verbose_name="URL du post")
    
    # Analytics
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    last_analytics_update = models.DateTimeField(null=True, blank=True)
    
    # Dates
    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name="Planifiée pour")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publiée le")
    
    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "Publications"
        ordering = ['-published_at']
        unique_together = ['video', 'platform']  # Une vidéo = 1 publication par plateforme
    
    def __str__(self):
        status = "Publiée" if self.published_at else "Planifiée"
        return f"{self.get_platform_display()} - {status} - {self.video.script.theme}"
