from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('web_app', 'Application Web'),
        ('maintenance', 'Maintenance & Optimisation'),
    ]

    TYPE_CHOICES = [
        ('basic', 'Pack Basique'),
        ('standard', 'Pack Standard'),
        ('premium', 'Pack Premium'),
        ('custom', 'Sur Mesure'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Catégorie")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'offre")
    description = RichTextField(verbose_name="Description")
    features = RichTextField(verbose_name="Fonctionnalités incluses")
    technical_stack = models.TextField(verbose_name="Stack technique", help_text="Liste des technologies utilisées")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix de base",
        null=True,
        blank=True,
        help_text="Optionnel. Laissez vide si le tarif dépend du projet."
    )
    duration = models.CharField(max_length=100, verbose_name="Durée estimée")
    image = models.ImageField(upload_to='services/', verbose_name="Image", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Champs spécifiques pour l'e-commerce
    has_payment_integration = models.BooleanField(default=False, verbose_name="Intégration paiement")
    has_inventory_management = models.BooleanField(default=False, verbose_name="Gestion des stocks")
    has_order_management = models.BooleanField(default=False, verbose_name="Gestion des commandes")
    has_customer_accounts = models.BooleanField(default=False, verbose_name="Comptes clients")

    # Champs spécifiques pour les applications web
    has_user_authentication = models.BooleanField(default=False, verbose_name="Authentification utilisateurs")
    has_admin_dashboard = models.BooleanField(default=False, verbose_name="Tableau de bord admin")
    has_api_integration = models.BooleanField(default=False, verbose_name="Intégration API")
    has_mobile_responsive = models.BooleanField(default=True, verbose_name="Responsive mobile")

    # Champs pour la maintenance
    includes_hosting = models.BooleanField(default=False, verbose_name="Hébergement inclus")
    includes_updates = models.BooleanField(default=False, verbose_name="Mises à jour incluses")
    includes_support = models.BooleanField(default=False, verbose_name="Support inclus")
    includes_seo = models.BooleanField(default=False, verbose_name="Optimisation SEO")

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['category', 'type', 'price']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"

    def get_features_list(self):
        """Retourne une liste des fonctionnalités activées pour ce service"""
        features = []
        
        if self.category == 'ecommerce':
            if self.has_payment_integration:
                features.append("Intégration des paiements")
            if self.has_inventory_management:
                features.append("Gestion des stocks")
            if self.has_order_management:
                features.append("Gestion des commandes")
            if self.has_customer_accounts:
                features.append("Comptes clients")
        
        elif self.category == 'web_app':
            if self.has_user_authentication:
                features.append("Authentification utilisateurs")
            if self.has_admin_dashboard:
                features.append("Tableau de bord administrateur")
            if self.has_api_integration:
                features.append("Intégration API")
            if self.has_mobile_responsive:
                features.append("Design responsive")
        
        elif self.category == 'maintenance':
            if self.includes_hosting:
                features.append("Hébergement inclus")
            if self.includes_updates:
                features.append("Mises à jour régulières")
            if self.includes_support:
                features.append("Support technique")
            if self.includes_seo:
                features.append("Optimisation SEO")
        
        return features
