from django.db import models
from django.utils.text import slugify
from django.urls import reverse
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

    def get_absolute_url(self):
        """Retourne l'URL de détail de la formation"""
        return reverse('formations:formation_detail', kwargs={'slug': self.slug})


class Module(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200, verbose_name="Titre")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    description = models.TextField(blank=True, verbose_name="Description")
    is_free = models.BooleanField(default=False, verbose_name="Gratuit")

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"


class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('video', 'Vidéo'),
        ('text', 'Texte'),
        ('quiz', 'Quiz'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200, verbose_name="Titre")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    content = RichTextField(blank=True, verbose_name="Contenu")
    video_url = models.URLField(blank=True, verbose_name="URL Vidéo")
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="Durée (minutes)")
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default='text', verbose_name="Type")

    class Meta:
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"

    def get_youtube_embed_url(self):
        """Convertit une URL YouTube en URL embed"""
        url = self.video_url
        if not url:
            return ''
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
            return f'https://www.youtube.com/embed/{video_id}'
        if 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f'https://www.youtube.com/embed/{video_id}'
        if 'youtube.com/embed/' in url:
            return url
        return url


class Payment(models.Model):
    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('XOF', 'Franc CFA'),
    ]
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    EUR_TO_XOF_RATE = 656

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='payments')
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='XOF', verbose_name="Devise")
    payment_token = models.CharField(max_length=255, unique=True, verbose_name="Token de paiement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    paydunya_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Token PayDunya")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.formation.title} - {self.amount} {self.currency} ({self.status})"

    @classmethod
    def convert_eur_to_xof(cls, amount_eur):
        """Convertit un montant EUR en XOF (FCFA)"""
        from decimal import Decimal
        return (Decimal(str(amount_eur)) * cls.EUR_TO_XOF_RATE).quantize(Decimal('1'))

    def get_amount_xof(self):
        """Retourne le montant en XOF"""
        if self.currency == 'EUR':
            return self.convert_eur_to_xof(self.amount)
        return self.amount


class Enrollment(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='enrollments')
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ['user', 'formation']

    def __str__(self):
        return f"{self.user.username} - {self.formation.title}"

    def get_progress(self):
        """Retourne le pourcentage de progression"""
        total_lessons = Lesson.objects.filter(module__formation=self.formation).count()
        if total_lessons == 0:
            return 0
        completed = LessonProgress.objects.filter(
            user=self.user,
            lesson__module__formation=self.formation,
            completed=True
        ).count()
        return int((completed / total_lessons) * 100)


class LessonProgress(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Progression"
        verbose_name_plural = "Progressions"
        unique_together = ['user', 'lesson']

    def __str__(self):
        status = "✅" if self.completed else "⏳"
        return f"{status} {self.user.username} - {self.lesson.title}"