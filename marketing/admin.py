from django.contrib import admin
from django.utils.html import format_html
from .models import ContentScript, VideoProject, Publication


@admin.register(ContentScript)
class ContentScriptAdmin(admin.ModelAdmin):
    list_display = ['id', 'pillar', 'theme', 'created_at', 'video_count']
    list_filter = ['pillar', 'created_at']
    search_fields = ['theme', 'caption', 'hashtags']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Informations', {
            'fields': ['pillar', 'theme']
        }),
        ('Contenu', {
            'fields': ['script_json', 'caption', 'hashtags']
        }),
        ('Métadonnées', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    
    def video_count(self, obj):
        count = obj.videos.count()
        return format_html(
            '<span style="color: {};">{} vidéo(s)</span>',
            'green' if count > 0 else 'gray',
            count
        )
    video_count.short_description = "Vidéos"


@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'script_theme', 'status_badge', 'duration_seconds', 'created_at', 'publication_count']
    list_filter = ['status', 'created_at']
    search_fields = ['script__theme']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Script', {
            'fields': ['script']
        }),
        ('Production', {
            'fields': ['status', 'error_message']
        }),
        ('Assets', {
            'fields': ['images_urls', 'audio_url', 'video_url', 'storage_path']
        }),
        ('Métadonnées', {
            'fields': ['duration_seconds', 'file_size_mb', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def script_theme(self, obj):
        return obj.script.theme
    script_theme.short_description = "Thème"
    
    def status_badge(self, obj):
        colors = {
            'script': 'gray',
            'images': 'blue',
            'audio': 'cyan',
            'video': 'purple',
            'uploaded': 'orange',
            'published': 'green',
            'error': 'red',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = "Statut"
    
    def publication_count(self, obj):
        count = obj.publications.count()
        return format_html(
            '<span style="color: {};">{} publication(s)</span>',
            'green' if count > 0 else 'gray',
            count
        )
    publication_count.short_description = "Publications"


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'platform', 'video_theme', 'status_display', 'views', 'likes', 'published_at']
    list_filter = ['platform', 'published_at']
    search_fields = ['video__script__theme', 'platform_post_id']
    readonly_fields = ['last_analytics_update']
    
    fieldsets = [
        ('Vidéo', {
            'fields': ['video', 'platform']
        }),
        ('Publication', {
            'fields': ['platform_post_id', 'platform_url', 'scheduled_for', 'published_at']
        }),
        ('Analytics', {
            'fields': ['views', 'likes', 'comments', 'shares', 'last_analytics_update']
        }),
    ]
    
    def video_theme(self, obj):
        return obj.video.script.theme
    video_theme.short_description = "Thème"
    
    def status_display(self, obj):
        if obj.published_at:
            return format_html('<span style="color: green;">✅ Publiée</span>')
        elif obj.scheduled_for:
            return format_html('<span style="color: orange;">📅 Planifiée</span>')
        else:
            return format_html('<span style="color: gray;">⏸️ Brouillon</span>')
    status_display.short_description = "Statut"
