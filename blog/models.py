from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category-posts', kwargs={'category_slug': self.slug})


# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=225)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    body = RichTextUploadingField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("category", related_name="posts")
    thumbnail = models.ImageField(blank=True, upload_to='blog')
    objects = models.Manager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog-detail', kwargs={'slug': self.slug})
