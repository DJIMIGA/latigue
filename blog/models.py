from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20)


# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=225)
    body = RichTextUploadingField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("category", related_name="posts")
    thumbnail = models.ImageField(blank=True, upload_to='blog')
    objects = models.Manager()

    def __str__(self):
        return self.title
