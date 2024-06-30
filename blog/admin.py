from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib import admin

from .models import Category, Post
from ckeditor.widgets import CKEditorWidget


class PostAdmin(admin.ModelAdmin):
    formfield_overrides = {
        RichTextUploadingField: {'widget': CKEditorWidget},
    }


admin.site.register(Post, PostAdmin)

admin.site.register(Category)
