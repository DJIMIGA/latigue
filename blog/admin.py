from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Post
from ckeditor.widgets import CKEditorWidget


class PostAdmin(admin.ModelAdmin):
    formfield_overrides = {
        RichTextUploadingField: {'widget': CKEditorWidget},
    }
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'slug', 'categories', 'is_featured')
        }),
        ('Contenu', {
            'fields': ('body', 'markdown_file'),
            'description': 'Vous pouvez soit écrire directement dans l\'éditeur, soit uploader un fichier Markdown (.md) qui sera automatiquement converti en HTML.'
        }),
        ('Image de couverture', {
            'fields': ('thumbnail', 'alt_text')
        }),
        ('Métadonnées', {
            'fields': ('created_on', 'last_modified'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_on', 'last_modified')
    
    list_display = ('title', 'get_categories', 'is_featured', 'created_on', 'has_markdown')
    list_filter = ('is_featured', 'categories', 'created_on')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    
    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Catégories'
    
    def has_markdown(self, obj):
        if obj.markdown_file:
            return format_html('<span style="color: green;">✓ Fichier Markdown</span>')
        return format_html('<span style="color: gray;">-</span>')
    has_markdown.short_description = 'Markdown'


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
