import uuid
import hashlib
import secrets

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations')
    contact_email = models.EmailField(verbose_name="Email de contact")
    contact_phone = models.CharField(max_length=30, blank=True, verbose_name="Telephone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:190]
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SaaSPlan(models.Model):
    MODEL_CHOICES = [
        ('anthropic/claude-haiku-3-5-20241022', 'Claude Haiku 3.5'),
        ('anthropic/claude-sonnet-4-5-20250929', 'Claude Sonnet 4.5'),
        ('anthropic/claude-opus-4-6', 'Claude Opus 4.6'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom du plan")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    model_id = models.CharField(max_length=100, choices=MODEL_CHOICES, verbose_name="Modele IA")
    max_concurrent = models.PositiveIntegerField(default=2, verbose_name="Sessions simultanees max")
    price_xof = models.PositiveIntegerField(verbose_name="Prix mensuel (FCFA)")
    features = models.TextField(blank=True, verbose_name="Fonctionnalites incluses",
                                help_text="Une fonctionnalite par ligne")
    max_tokens_month = models.PositiveIntegerField(default=500000, verbose_name="Tokens max/mois")
    api_access = models.BooleanField(default=False, verbose_name="Acces API programmatique",
                                      help_text="Permet l'utilisation de l'endpoint /saas/api/chat/")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plan SaaS"
        verbose_name_plural = "Plans SaaS"
        ordering = ['order', 'price_xof']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.price_xof} FCFA/mois"

    def get_features_list(self):
        return [f.strip() for f in self.features.split('\n') if f.strip()]


class AgentConfig(models.Model):
    STATUS_CHOICES = [
        ('provisioning', 'En creation'),
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('error', 'Erreur'),
        ('deleted', 'Supprime'),
    ]
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('both', 'WhatsApp + Telegram'),
        ('none', 'Aucun (API uniquement)'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='agent')
    plan = models.ForeignKey(SaaSPlan, on_delete=models.PROTECT, related_name='agents')
    agent_id = models.CharField(max_length=100, unique=True, verbose_name="ID Agent OpenClaw")
    agent_name = models.CharField(max_length=200, verbose_name="Nom de l'assistant")
    persona = models.TextField(blank=True, verbose_name="Personnalite / System prompt",
                               help_text="Description du role et comportement de l'agent")
    company_info = models.TextField(blank=True, verbose_name="Informations entreprise",
                                    help_text="Contenu mis dans data/info.md (produits, services, horaires, etc.)")
    channels = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='none')
    whatsapp_number = models.CharField(max_length=30, blank=True, verbose_name="Numero WhatsApp")
    telegram_id = models.CharField(max_length=30, blank=True, verbose_name="ID Telegram",
                                   help_text="ID numerique Telegram de l'utilisateur")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration Agent"
        verbose_name_plural = "Configurations Agents"

    def __str__(self):
        return f"{self.agent_name} ({self.agent_id}) - {self.organization.name}"

    @property
    def workspace_path(self):
        return f"/home/node/.openclaw/clients/{self.agent_id}"

    @property
    def agent_dir_path(self):
        return f"/home/node/.openclaw/agents/{self.agent_id}/agent"

    @property
    def host_workspace_path(self):
        from django.conf import settings as s
        return f"{s.OPENCLAW_CLIENTS_DIR}/{self.agent_id}"

    @property
    def host_agent_dir_path(self):
        from django.conf import settings as s
        return f"{s.OPENCLAW_AGENTS_DIR}/{self.agent_id}/agent"


class SaaSSubscription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('trial', 'Essai gratuit'),
        ('active', 'Actif'),
        ('expired', 'Expire'),
        ('cancelled', 'Annule'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SaaSPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    amount_xof = models.PositiveIntegerField(verbose_name="Montant (FCFA)")
    auto_renew = models.BooleanField(default=True)
    payment_token = models.CharField(max_length=255, unique=True, blank=True)
    paydunya_token = models.CharField(max_length=255, blank=True, null=True)
    linked_formation_slug = models.CharField(max_length=200, blank=True, default='', verbose_name="Formation liee (slug)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Abonnement SaaS"
        verbose_name_plural = "Abonnements SaaS"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.payment_token:
            self.payment_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        from django.utils import timezone
        if self.status not in ('active', 'trial'):
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True

    @property
    def days_remaining(self):
        from django.utils import timezone
        if not self.end_date:
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)


class UsageLog(models.Model):
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('api', 'API'),
        ('web', 'Web'),
    ]

    agent_config = models.ForeignKey(AgentConfig, on_delete=models.CASCADE, related_name='usage_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    tokens_input = models.PositiveIntegerField(default=0)
    tokens_output = models.PositiveIntegerField(default=0)
    model_used = models.CharField(max_length=100, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='api')
    response_time_ms = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Log d'utilisation"
        verbose_name_plural = "Logs d'utilisation"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent_config', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.agent_config.agent_id} - {self.timestamp}"

    @property
    def total_tokens(self):
        return self.tokens_input + self.tokens_output


class APIKey(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='api_keys')
    key_hash = models.CharField(max_length=64, unique=True)
    key_prefix = models.CharField(max_length=12, verbose_name="Prefixe visible")
    name = models.CharField(max_length=100, verbose_name="Nom de la cle")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cle API"
        verbose_name_plural = "Cles API"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @staticmethod
    def generate_key():
        """Returns (raw_key, key_hash, key_prefix)."""
        raw_key = f"djt_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]
        return raw_key, key_hash, key_prefix

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()
