from django.contrib import admin
from portfolio.models import Portfolio, Profile, Experience


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Administration du profil"""
    list_display = ('name', 'title', 'updated_at')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('name', 'title', 'profile_image', 'bio')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Empêcher l'ajout de plusieurs profils
        if Profile.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression du profil
        return False


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    """Administration des expériences professionnelles"""
    list_display = ('title', 'company', 'period', 'position', 'order', 'is_active', 'updated_at')
    list_filter = ('is_active', 'position', 'created_at')
    search_fields = ('title', 'company', 'description')
    list_editable = ('order', 'is_active', 'position')
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'company', 'period', 'description', 'logo')
        }),
        ('Affichage', {
            'fields': ('order', 'position', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(Portfolio)
