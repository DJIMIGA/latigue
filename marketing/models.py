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


class VideoSegment(models.Model):
    """
    Segment vidéo de 5 secondes (nouveau workflow).
    Une vidéo finale = plusieurs segments assemblés.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente de génération'),
        ('processing', 'Génération en cours'),
        ('completed', 'Généré'),
        ('failed', 'Erreur'),
    ]
    
    # Relations
    project = models.ForeignKey('VideoProject', on_delete=models.CASCADE, related_name='segments')
    
    # Contenu
    order = models.IntegerField(verbose_name="Ordre dans la vidéo")
    text = models.TextField(verbose_name="Texte du segment", help_text="5 secondes max")
    prompt = models.TextField(verbose_name="Prompt pour génération vidéo")
    duration = models.IntegerField(default=5, verbose_name="Durée (secondes)")
    
    # Génération vidéo
    provider = models.CharField(max_length=20, blank=True, help_text="luma, runway, pika, stability")
    job_id = models.CharField(max_length=200, blank=True, verbose_name="ID job API")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    progress = models.IntegerField(default=0, verbose_name="Progression (%)")
    
    # Assets
    video_url = models.URLField(blank=True, verbose_name="URL vidéo générée")
    storage_path = models.CharField(max_length=500, blank=True)
    
    # Métadonnées
    cost_usd = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    generation_time_sec = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Données API brutes")
    
    # Édition
    selected = models.BooleanField(default=True, verbose_name="Sélectionné pour vidéo finale")
    notes = models.TextField(blank=True, verbose_name="Notes d'édition")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Segment vidéo"
        verbose_name_plural = "Segments vidéo"
        ordering = ['project', 'order']
        unique_together = ['project', 'order']
    
    def __str__(self):
        return f"Segment {self.order} - {self.text[:30]}..."
    
    def estimate_cost(self):
        """Estime le coût de génération selon le provider"""
        from marketing.ai.video_providers import get_provider
        
        if self.provider:
            try:
                provider = get_provider(self.provider)
                return provider.estimate_cost(self.duration)
            except:
                pass
        
        # Coût moyen par défaut
        return self.duration * 0.03


class VideoProject(models.Model):
    """Projet vidéo en cours de production"""
    
    STATUS_CHOICES = [
        ('script', 'Script créé'),
        ('segments_draft', 'Segments en brouillon'),
        ('segments_generating', 'Génération segments'),
        ('segments_completed', 'Segments générés'),
        ('audio', 'Audio généré'),
        ('assembly', 'Assemblage en cours'),
        ('completed', 'Terminé'),
        ('uploaded', 'Vidéo uploadée'),
        ('published', 'Publiée'),
        ('error', 'Erreur'),
    ]
    
    script = models.ForeignKey(ContentScript, on_delete=models.CASCADE, related_name='videos')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='script')
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    
    # Provider vidéo utilisé
    video_provider = models.CharField(max_length=20, blank=True, help_text="Provider pour les segments")
    
    # URLs des assets (legacy + nouveau workflow)
    images_urls = models.JSONField(default=list, help_text="[LEGACY] Liste des URLs des images")
    audio_url = models.URLField(blank=True, verbose_name="URL audio voix-off")
    video_url = models.URLField(blank=True, verbose_name="URL vidéo finale")
    storage_path = models.CharField(max_length=500, blank=True, help_text="Chemin S3/R2")
    
    # Métadonnées
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name="Durée (secondes)")
    file_size_mb = models.FloatField(null=True, blank=True, verbose_name="Taille fichier (MB)")
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet vidéo"
        verbose_name_plural = "Projets vidéo"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vidéo #{self.id} - {self.script.theme} ({self.get_status_display()})"
    
    def get_selected_segments(self):
        """Retourne les segments sélectionnés dans l'ordre"""
        return self.segments.filter(selected=True).order_by('order')
    
    def calculate_total_cost(self):
        """Calcule le coût total des segments"""
        total = sum(
            seg.cost_usd or seg.estimate_cost() 
            for seg in self.segments.filter(selected=True)
        )
        return total


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
