from django.contrib import admin
from .models import Formation

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'price', 'duration', 'is_active', 'created_at')
    list_filter = ('level', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'prerequisites', 'program')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'price')
    date_hierarchy = 'created_at' 