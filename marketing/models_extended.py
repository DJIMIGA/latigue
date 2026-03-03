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
    MONTAGE_HYBRIDE = 'montage_hybride', 'Montage IA Hybride'


class SegmentSourceType(models.TextChoices):
    """Source d'un segment dans le montage hybride"""
    AI_GENERATED = 'ai_generated', '🤖 Généré par IA (mise en situation)'
    UPLOADED_CLIP = 'uploaded_clip', '📱 Clip filmé (face-cam)'
    SCREENSHOT = 'screenshot', '🖥️ Screenshot animé par IA'
    STOCK = 'stock', '📦 Stock footage'


class VideoProvider(models.TextChoices):
    """Providers disponibles (extensible)"""
    MINIMAX = 'minimax', 'MiniMax Hailuo'
    LUMA = 'luma', 'Luma AI'
    RUNWAY = 'runway', 'Runway Gen-3'
    PIKA = 'pika', 'Pika Labs'
    STABILITY = 'stability', 'Stability AI'
    HEYGEN = 'heygen', 'HeyGen (Avatar)'
    AUTO = 'auto', 'Auto (meilleur disponible)'


class ContentPillar(models.TextChoices):
    """4 piliers marketing"""
    EDUCATION = 'education', 'Éducation'
    DEMO = 'demo', 'Démo produit'
    STORY = 'story', 'Storytelling'
    TIPS = 'tips', 'Tips & Astuces'


class VideoTheme(models.TextChoices):
    """Thèmes de scripts vidéo"""
    ARGENT = 'argent', 'Argent'
    TEMPS = 'temps', 'Temps'
    TRANQUILLITE = 'tranquillite', 'Tranquillité'
    CROISSANCE = 'croissance', 'Croissance'
    IA = 'ia', 'Intelligence Artificielle'
    FIDELITE = 'fidelite', 'Fidélité'
    MOBILE = 'mobile', 'Mobile'
    IMPRESSION = 'impression', 'Impression Pro'
    CUSTOM = 'custom', 'Personnalisé'


class ClientLevel(models.TextChoices):
    """Niveau de maturité du client cible"""
    AUCUN_SYSTEME = 'niveau1', 'Niveau 1 - Aucun système'
    PAPIER = 'niveau2', 'Niveau 2 - Gestion papier'
    OUTILS_COMPLEXES = 'niveau3', 'Niveau 3 - Outils complexes'
    TOUS = 'tous', 'Tous niveaux'


class Platform(models.TextChoices):
    """Plateformes de diffusion"""
    TIKTOK = 'tiktok', 'TikTok'
    INSTAGRAM = 'instagram', 'Instagram Reels'
    YOUTUBE = 'youtube', 'YouTube Shorts'
    FACEBOOK = 'facebook', 'Facebook'
    LINKEDIN = 'linkedin', 'LinkedIn'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    EMAIL = 'email', 'Email'
    ALL = 'all', 'Toutes plateformes'


class VideoScript(models.Model):
    """
    Bibliothèque de scripts vidéo pour réseaux sociaux.
    Source : VIDEOS_RESEAUX_SOCIAUX.html
    """
    # Métadonnées
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, help_text="Ex: A1, T2, IA3")
    theme = models.CharField(max_length=50, choices=VideoTheme.choices)
    client_level = models.CharField(
        max_length=20, 
        choices=ClientLevel.choices, 
        default=ClientLevel.TOUS
    )
    platform = models.CharField(
        max_length=20, 
        choices=Platform.choices, 
        default=Platform.ALL
    )
    
    # Durée recommandée
    duration_min = models.IntegerField(
        default=30, 
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        help_text="Durée minimale en secondes"
    )
    duration_max = models.IntegerField(
        default=60, 
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        help_text="Durée maximale en secondes"
    )
    
    # Structure du script (segments)
    hook = models.TextField(help_text="0-3s : Accroche")
    hook_timing = models.CharField(max_length=20, default="0-3s")
    
    problem = models.TextField(help_text="3-8s : Problème identifié")
    problem_timing = models.CharField(max_length=20, default="3-8s")
    
    micro_revelation = models.TextField(help_text="8-12s : Micro-révélation")
    micro_revelation_timing = models.CharField(max_length=20, default="8-12s")
    
    solution = models.TextField(help_text="12-25s : Solution proposée")
    solution_timing = models.CharField(max_length=20, default="12-25s")
    solution_hint = models.TextField(
        blank=True, 
        help_text="Indication visuelle pour le tournage"
    )
    
    proof = models.TextField(help_text="25-35s : Preuve sociale / Résultat")
    proof_timing = models.CharField(max_length=20, default="25-35s")
    
    cta = models.TextField(help_text="35-40s : Call to Action")
    cta_timing = models.CharField(max_length=20, default="35-40s")
    
    # Métadonnées supplémentaires
    tags = models.JSONField(
        default=list, 
        blank=True,
        help_text="Tags pour recherche : ['scanner', 'mobile', 'offline']"
    )
    hooks_alternatives = models.JSONField(
        default=list,
        blank=True,
        help_text="Hooks alternatifs pour A/B testing"
    )
    cta_alternatives = models.JSONField(
        default=list,
        blank=True,
        help_text="CTA alternatifs pour A/B testing"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0, help_text="Nb de fois utilisé")
    
    class Meta:
        ordering = ['theme', 'code']
        verbose_name = "Script Vidéo"
        verbose_name_plural = "Scripts Vidéo"
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def get_full_script(self):
        """Retourne le script complet formaté"""
        return {
            'hook': {'text': self.hook, 'timing': self.hook_timing},
            'problem': {'text': self.problem, 'timing': self.problem_timing},
            'micro_revelation': {'text': self.micro_revelation, 'timing': self.micro_revelation_timing},
            'solution': {'text': self.solution, 'timing': self.solution_timing, 'hint': self.solution_hint},
            'proof': {'text': self.proof, 'timing': self.proof_timing},
            'cta': {'text': self.cta, 'timing': self.cta_timing},
        }
    
    def increment_usage(self):
        """Incrémente le compteur d'utilisation"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


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
    
    # ===== MODE MONTAGE HYBRIDE =====
    # Cohérence personnage/scène (réutilisé dans tous les prompts IA)
    character_description = models.TextField(
        blank=True,
        help_text="Description du personnage principal (ex: 'Un commerçant africain, 35 ans, chemise bleue')"
    )
    scene_description = models.TextField(
        blank=True,
        help_text="Description du décor/environnement (ex: 'Un petit magasin de quartier, étagères colorées')"
    )
    visual_style = models.CharField(
        max_length=200,
        blank=True,
        help_text="Style visuel global (ex: 'cinématique, lumière chaude, réaliste')"
    )
    is_hybrid = models.BooleanField(
        default=False,
        help_text="Mode montage hybride (mix clips filmés + IA)"
    )
    
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
    segment_name = models.CharField(
        max_length=50, blank=True,
        help_text="Nom du segment (hook, problem, solution, etc.)"
    )
    
    # Source du segment (montage hybride)
    source_type = models.CharField(
        max_length=30,
        choices=SegmentSourceType.choices if hasattr(SegmentSourceType, 'choices') else [
            ('ai_generated', '🤖 IA'), ('uploaded_clip', '📱 Clip'), 
            ('screenshot', '🖥️ Screenshot'), ('stock', '📦 Stock')
        ],
        default='ai_generated',
        help_text="Source du contenu de ce segment"
    )
    uploaded_clip = models.FileField(
        upload_to='marketing/clips/%Y/%m/',
        blank=True, null=True,
        help_text="Clip face-cam uploadé (pour segments filmés)"
    )
    
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
    
    def get_enriched_prompt(self):
        """
        Retourne le prompt enrichi avec le contexte personnage/scène du job.
        Garantit la cohérence visuelle entre tous les segments IA.
        """
        if self.source_type == 'uploaded_clip':
            return self.prompt  # Pas besoin pour les clips filmés
        
        parts = []
        
        # Style visuel global
        if self.job.visual_style:
            parts.append(f"Style: {self.job.visual_style}.")
        
        # Personnage cohérent
        if self.job.character_description:
            parts.append(f"Character: {self.job.character_description}.")
        
        # Décor cohérent
        if self.job.scene_description:
            parts.append(f"Setting: {self.job.scene_description}.")
        
        # Scène spécifique du segment
        parts.append(f"Scene: {self.prompt}")
        
        # Format vertical TikTok
        parts.append("Vertical video 9:16, cinematic, smooth camera movement.")
        
        return " ".join(parts)
