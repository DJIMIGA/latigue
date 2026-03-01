"""
Models étendus pour interface web production vidéo.
Architecture scalable, agnostique provider/mode.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class VideoGenerationMode(models.TextChoices):
    """Modes de génération vidéo (extensible)"""
    TEXT_TO_VIDEO = 'text_to_video', 'Text to Video'
    IMAGE_TO_VIDEO = 'image_to_video', 'Image to Video'
    VIDEO_TO_VIDEO = 'video_to_video', 'Video to Video (prolongation)'
    HYBRID = 'hybrid', 'Hybrid (mix modes)'


class VideoProvider(models.TextChoices):
    """Providers disponibles (extensible)"""
    LUMA = 'luma', 'Luma AI'
    RUNWAY = 'runway', 'Runway Gen-3'
    PIKA = 'pika', 'Pika Labs'
    STABILITY = 'stability', 'Stability AI'
    AUTO = 'auto', 'Auto (meilleur disponible)'


class ContentPillar(models.TextChoices):
    """4 piliers marketing"""
    EDUCATION = 'education', 'Éducation'
    DEMO = 'demo', 'Démo produit'
    STORY = 'story', 'Storytelling'
    TIPS = 'tips', 'Tips & Astuces'


class VideoProjectTemplate(models.Model):
    """
    Template de projet vidéo réutilisable.
    Définit la structure sans hardcoder.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Config flexible (JSON)
    default_config = models.JSONField(
        default=dict,
        help_text="Config par défaut : provider, mode, durée, ratio, etc."
    )
    
    # Structure segments
    segments_count = models.IntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    segment_duration = models.IntegerField(
        default=5,
        help_text="Durée par segment (secondes)"
    )
    
    # Metadata
    pillar = models.CharField(
        max_length=20,
        choices=ContentPillar.choices,
        default=ContentPillar.TIPS
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Template de Projet"
        verbose_name_plural = "Templates de Projets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.segments_count}×{self.segment_duration}s)"


class VideoProductionJob(models.Model):
    """
    Job de production vidéo principal.
    Orchestration de bout en bout.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', '📝 Brouillon'
        SCRIPT_PENDING = 'script_pending', '✍️ Script en cours'
        SCRIPT_READY = 'script_ready', '📄 Script prêt'
        ASSETS_PENDING = 'assets_pending', '🎨 Assets en cours'
        ASSETS_READY = 'assets_ready', '🖼️ Assets prêts'
        VIDEO_PENDING = 'video_pending', '🎬 Vidéos en cours'
        VIDEO_READY = 'video_ready', '🎞️ Vidéos prêtes'
        ASSEMBLY_PENDING = 'assembly_pending', '🔧 Assemblage en cours'
        COMPLETED = 'completed', '✅ Terminé'
        FAILED = 'failed', '❌ Échec'
        PAUSED = 'paused', '⏸️ En pause'
    
    # Identité
    title = models.CharField(max_length=300)
    theme = models.CharField(max_length=500, help_text="Sujet/thème de la vidéo")
    template = models.ForeignKey(
        VideoProjectTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs'
    )
    
    # Config runtime (override template)
    config = models.JSONField(
        default=dict,
        help_text="Config spécifique au job (surcharge template)"
    )
    
    # Statut
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT
    )
    progress_percent = models.IntegerField(default=0)
    
    # Script généré
    script_text = models.TextField(blank=True)
    script_metadata = models.JSONField(default=dict)
    
    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_jobs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Résultat final
    final_video_url = models.URLField(blank=True)
    final_video_path = models.CharField(max_length=500, blank=True)
    
    # Coûts
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Coût estimé ($)"
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Coût réel ($)"
    )
    
    # Logs
    error_log = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Job de Production"
        verbose_name_plural = "Jobs de Production"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"
    
    def get_config(self, key, default=None):
        """Récupère config avec fallback template"""
        # 1. Job config
        if key in self.config:
            return self.config[key]
        # 2. Template config
        if self.template and key in self.template.default_config:
            return self.template.default_config[key]
        # 3. Default
        return default
    
    def calculate_estimated_cost(self):
        """Calcule coût estimé selon provider/durée"""
        provider = self.get_config('provider', 'luma')
        segments = self.get_config('segments_count', 6)
        duration = self.get_config('segment_duration', 5)
        
        # Pricing par provider ($/sec)
        pricing = {
            'luma': 0.03,
            'runway': 0.05,
            'pika': 0.03,
            'stability': 0.015,
        }
        
        rate = pricing.get(provider, 0.03)
        video_cost = segments * duration * rate
        script_cost = 0.01
        voice_cost = (segments * duration / 30) * 0.02
        
        total = video_cost + script_cost + voice_cost
        self.estimated_cost = round(total, 2)
        return self.estimated_cost


class SegmentAsset(models.Model):
    """
    Asset de référence pour un segment (image, vidéo).
    Permet image-to-video et video-to-video.
    """
    
    class AssetType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Vidéo'
        SCREENSHOT = 'screenshot', 'Screenshot'
        GENERATED = 'generated', 'Généré par IA'
    
    job = models.ForeignKey(
        VideoProductionJob,
        on_delete=models.CASCADE,
        related_name='assets'
    )
    
    segment_index = models.IntegerField(
        help_text="Index du segment (0-based)"
    )
    
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.IMAGE
    )
    
    # Fichier uploadé OU URL
    file = models.FileField(
        upload_to='marketing/assets/%Y/%m/',
        blank=True,
        null=True
    )
    url = models.URLField(blank=True)
    
    # Prompt animation (pour image-to-video)
    animation_prompt = models.TextField(
        blank=True,
        help_text="Comment animer cet asset"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Asset Segment"
        verbose_name_plural = "Assets Segments"
        ordering = ['job', 'segment_index']
        unique_together = [['job', 'segment_index']]
    
    def __str__(self):
        return f"Segment {self.segment_index} - {self.get_asset_type_display()}"
    
    def get_url(self):
        """Retourne URL (uploadé ou externe)"""
        if self.file:
            return self.file.url
        return self.url


class VideoSegmentGeneration(models.Model):
    """
    Génération d'un segment vidéo individuel.
    Lié à VideoSegment existant OU standalone.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        QUEUED = 'queued', 'En file'
        PROCESSING = 'processing', 'En cours'
        COMPLETED = 'completed', 'Terminé'
        FAILED = 'failed', 'Échec'
        CANCELLED = 'cancelled', 'Annulé'
    
    job = models.ForeignKey(
        VideoProductionJob,
        on_delete=models.CASCADE,
        related_name='generations'
    )
    
    segment_index = models.IntegerField()
    
    # Mode et provider
    generation_mode = models.CharField(
        max_length=30,
        choices=VideoGenerationMode.choices,
        default=VideoGenerationMode.TEXT_TO_VIDEO
    )
    
    provider = models.CharField(
        max_length=30,
        choices=VideoProvider.choices,
        default=VideoProvider.LUMA
    )
    
    # Input
    prompt = models.TextField()
    reference_asset = models.ForeignKey(
        SegmentAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Asset de référence (pour image/video-to-video)"
    )
    
    # Paramètres
    duration = models.IntegerField(default=5)
    aspect_ratio = models.CharField(max_length=10, default='9:16')
    
    # Config provider-specific (flexible)
    provider_config = models.JSONField(
        default=dict,
        help_text="Params spécifiques au provider"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Job provider
    provider_job_id = models.CharField(max_length=200, blank=True)
    progress_percent = models.IntegerField(default=0)
    
    # Résultat
    video_url = models.URLField(blank=True)
    local_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    provider_metadata = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    # Coût
    cost = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Génération Segment"
        verbose_name_plural = "Générations Segments"
        ordering = ['job', 'segment_index']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['provider', 'provider_job_id']),
        ]
    
    def __str__(self):
        return f"Job {self.job_id} - Segment {self.segment_index} ({self.provider})"
