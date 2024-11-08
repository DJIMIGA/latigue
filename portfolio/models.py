from django.db import models


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
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title
