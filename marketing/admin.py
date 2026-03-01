"""
Django Admin customisé pour la production vidéo.
Interface admin complète avec actions en masse.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models_extended import (
    VideoProjectTemplate,
    VideoProductionJob,
    SegmentAsset,
    VideoSegmentGeneration
)


# =============================================================================
# TEMPLATES
# =============================================================================

@admin.register(VideoProjectTemplate)
class VideoProjectTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'pillar',
        'segments_info',
        'is_active',
        'jobs_count',
        'created_at',
    ]
    list_filter = ['pillar', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informations', {
            'fields': ('name', 'description', 'pillar', 'is_active')
        }),
        ('Structure', {
            'fields': ('segments_count', 'segment_duration')
        }),
        ('Configuration', {
            'fields': ('default_config',),
            'classes': ('collapse',),
            'description': 'Config JSON (provider, mode, aspect_ratio, etc.)'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def segments_info(self, obj):
        return f"{obj.segments_count}×{obj.segment_duration}s = {obj.segments_count * obj.segment_duration}s total"
    segments_info.short_description = 'Durée'
    
    def jobs_count(self, obj):
        count = obj.jobs.count()
        url = reverse('admin:marketing_videoproductionjob_changelist') + f'?template__id__exact={obj.id}'
        return format_html('<a href="{}">{} jobs</a>', url, count)
    jobs_count.short_description = 'Utilisations'


# =============================================================================
# JOBS DE PRODUCTION
# =============================================================================

class SegmentAssetInline(admin.TabularInline):
    model = SegmentAsset
    extra = 0
    fields = ['segment_index', 'asset_type', 'file', 'url', 'animation_prompt']
    readonly_fields = ['created_at']


class VideoSegmentGenerationInline(admin.TabularInline):
    model = VideoSegmentGeneration
    extra = 0
    fields = [
        'segment_index',
        'generation_mode',
        'provider',
        'status_badge',
        'progress_bar',
        'cost',
    ]
    readonly_fields = ['status_badge', 'progress_bar', 'created_at']
    
    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'queued': 'blue',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        if obj.status == 'completed':
            return '✅ 100%'
        elif obj.status == 'failed':
            return '❌'
        else:
            return f"{obj.progress_percent}%"
    progress_bar.short_description = 'Progression'


@admin.register(VideoProductionJob)
class VideoProductionJobAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'status_badge',
        'template',
        'created_by',
        'progress_bar',
        'cost_info',
        'created_at',
        'actions_buttons',
    ]
    list_filter = [
        'status',
        'template__pillar',
        'created_at',
        'created_by',
    ]
    search_fields = ['title', 'theme', 'script_text']
    readonly_fields = [
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
        'estimated_cost',
        'actual_cost',
        'progress_percent',
    ]
    
    inlines = [SegmentAssetInline, VideoSegmentGenerationInline]
    
    fieldsets = (
        ('Informations', {
            'fields': ('title', 'theme', 'template', 'created_by')
        }),
        ('Script', {
            'fields': ('script_text', 'script_metadata'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'progress_percent', 'error_log')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',),
            'description': 'Config spécifique au job (surcharge template)'
        }),
        ('Résultat', {
            'fields': ('final_video_url', 'final_video_path'),
            'classes': ('collapse',)
        }),
        ('Coûts', {
            'fields': ('estimated_cost', 'actual_cost')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_draft',
        'calculate_costs',
        'export_script',
    ]
    
    def status_badge(self, obj):
        icon = obj.get_status_display().split()[0]  # Emoji
        status_text = obj.get_status_display()
        
        colors = {
            'draft': '#6c757d',
            'script_pending': '#0dcaf0',
            'script_ready': '#0d6efd',
            'assets_pending': '#ffc107',
            'assets_ready': '#fd7e14',
            'video_pending': '#fd7e14',
            'video_ready': '#20c997',
            'assembly_pending': '#6610f2',
            'completed': '#198754',
            'failed': '#dc3545',
            'paused': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background:{}; color:white; padding:5px 10px; border-radius:5px; font-weight:bold;">{}</span>',
            color,
            status_text
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        percent = obj.progress_percent
        color = '#198754' if percent == 100 else '#0dcaf0'
        
        return format_html(
            '<div style="width:100px; background:#e9ecef; border-radius:3px; overflow:hidden;">'
            '<div style="width:{}%; background:{}; height:20px; text-align:center; color:white; font-size:12px; line-height:20px;">{}</div>'
            '</div>',
            percent,
            color,
            f'{percent}%' if percent > 20 else ''
        )
    progress_bar.short_description = 'Progression'
    
    def cost_info(self, obj):
        estimated = obj.estimated_cost
        actual = obj.actual_cost
        
        if actual > 0:
            diff = actual - estimated
            color = '#dc3545' if diff > 0 else '#198754'
            return format_html(
                '${:.2f} <span style="color:{};">(estimé: ${:.2f})</span>',
                actual,
                color,
                estimated
            )
        else:
            return f'${estimated:.2f} (estimé)'
    cost_info.short_description = 'Coût'
    
    def actions_buttons(self, obj):
        buttons = []
        
        # Lien vers job detail
        detail_url = reverse('marketing:job_detail', args=[obj.pk])
        buttons.append(f'<a href="{detail_url}" class="button">👁️ Voir</a>')
        
        # Actions selon status
        if obj.status == 'draft':
            config_url = reverse('marketing:job_configure_segments', args=[obj.pk])
            buttons.append(f'<a href="{config_url}" class="button">⚙️ Config</a>')
        
        elif obj.status in ['assets_ready', 'paused']:
            gen_url = reverse('marketing:job_generate', args=[obj.pk])
            buttons.append(f'<a href="{gen_url}" class="button">▶️ Générer</a>')
        
        return mark_safe(' '.join(buttons))
    actions_buttons.short_description = 'Actions'
    
    # Actions admin
    def mark_as_draft(self, request, queryset):
        updated = queryset.update(status=VideoProductionJob.Status.DRAFT)
        self.message_user(request, f'{updated} jobs marqués comme brouillon')
    mark_as_draft.short_description = "Marquer comme brouillon"
    
    def calculate_costs(self, request, queryset):
        for job in queryset:
            job.calculate_estimated_cost()
            job.save()
        self.message_user(request, f'Coûts recalculés pour {queryset.count()} jobs')
    calculate_costs.short_description = "Recalculer les coûts"
    
    def export_script(self, request, queryset):
        # TODO: Export scripts en fichiers texte
        self.message_user(request, 'Export à implémenter')
    export_script.short_description = "Exporter les scripts"


# =============================================================================
# ASSETS
# =============================================================================

@admin.register(SegmentAsset)
class SegmentAssetAdmin(admin.ModelAdmin):
    list_display = [
        'job',
        'segment_index',
        'asset_type',
        'preview_thumbnail',
        'animation_prompt_short',
        'created_at',
    ]
    list_filter = ['asset_type', 'created_at']
    search_fields = ['job__title', 'animation_prompt']
    readonly_fields = ['created_at']
    
    def preview_thumbnail(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:60px;" />',
                obj.file.url
            )
        elif obj.url:
            return format_html('<a href="{}" target="_blank">🔗 URL</a>', obj.url)
        return '-'
    preview_thumbnail.short_description = 'Preview'
    
    def animation_prompt_short(self, obj):
        if obj.animation_prompt:
            return obj.animation_prompt[:50] + '...' if len(obj.animation_prompt) > 50 else obj.animation_prompt
        return '-'
    animation_prompt_short.short_description = 'Animation'


# =============================================================================
# GÉNÉRATIONS
# =============================================================================

@admin.register(VideoSegmentGeneration)
class VideoSegmentGenerationAdmin(admin.ModelAdmin):
    list_display = [
        'job',
        'segment_index',
        'generation_mode',
        'provider',
        'status_badge',
        'progress_percent',
        'cost',
        'video_preview',
        'created_at',
    ]
    list_filter = [
        'status',
        'provider',
        'generation_mode',
        'created_at',
    ]
    search_fields = ['job__title', 'prompt', 'provider_job_id']
    readonly_fields = [
        'created_at',
        'started_at',
        'completed_at',
        'provider_metadata',
    ]
    
    fieldsets = (
        ('Job', {
            'fields': ('job', 'segment_index')
        }),
        ('Configuration', {
            'fields': ('generation_mode', 'provider', 'prompt', 'reference_asset')
        }),
        ('Paramètres', {
            'fields': ('duration', 'aspect_ratio', 'provider_config'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'progress_percent', 'provider_job_id', 'error_message')
        }),
        ('Résultat', {
            'fields': ('video_url', 'local_path', 'cost'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('provider_metadata', 'created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'queued': '#0dcaf0',
            'processing': '#ffc107',
            'completed': '#198754',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def video_preview(self, obj):
        if obj.video_url:
            return format_html(
                '<a href="{}" target="_blank">🎬 Voir vidéo</a>',
                obj.video_url
            )
        return '-'
    video_preview.short_description = 'Vidéo'
