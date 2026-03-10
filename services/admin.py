from django.contrib import admin
from .models import Service, ServiceOrder, Subscription


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'type', 'price', 'duration', 'is_active')
    list_filter = ('category', 'type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'features', 'technical_stack')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'price')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'category', 'type', 'description', 'features', 'technical_stack', 'price', 'duration', 'image', 'is_active')
        }),
        ('Fonctionnalités E-commerce', {
            'fields': ('has_payment_integration', 'has_inventory_management', 'has_order_management', 'has_customer_accounts'),
            'classes': ('collapse',),
            'description': 'Ces options ne sont pertinentes que pour les services de type E-commerce'
        }),
        ('Fonctionnalités Application Web', {
            'fields': ('has_user_authentication', 'has_admin_dashboard', 'has_api_integration', 'has_mobile_responsive'),
            'classes': ('collapse',),
            'description': 'Ces options ne sont pertinentes que pour les services de type Application Web'
        }),
        ('Services de Maintenance', {
            'fields': ('includes_hosting', 'includes_updates', 'includes_support', 'includes_seo'),
            'classes': ('collapse',),
            'description': 'Ces options ne sont pertinentes que pour les services de type Maintenance'
        }),
    )


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'order_type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'order_type', 'service', 'created_at')
    search_fields = ('user__username', 'user__email', 'payment_token', 'paydunya_token')
    readonly_fields = ('payment_token', 'paydunya_token', 'created_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'service')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'status', 'amount', 'start_date', 'end_date', 'auto_renew', 'created_at')
    list_filter = ('status', 'auto_renew', 'service', 'created_at')
    search_fields = ('user__username', 'user__email', 'service__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'service')
