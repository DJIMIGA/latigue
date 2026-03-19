from django.contrib import admin
from .models import Organization, SaaSPlan, AgentConfig, SaaSSubscription, UsageLog, APIKey


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'contact_email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__username', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SaaSPlan)
class SaaSPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_id', 'price_xof', 'max_concurrent', 'max_tokens_month', 'is_active', 'order')
    list_filter = ('is_active', 'model_id')
    list_editable = ('is_active', 'price_xof', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ('agent_name', 'agent_id', 'organization', 'plan', 'status', 'channels', 'created_at')
    list_filter = ('status', 'plan', 'channels')
    search_fields = ('agent_name', 'agent_id', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SaaSSubscription)
class SaaSSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'plan', 'status', 'amount_xof', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'plan', 'auto_renew')
    search_fields = ('organization__name', 'payment_token')
    readonly_fields = ('payment_token', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('agent_config', 'timestamp', 'tokens_input', 'tokens_output', 'model_used', 'channel', 'response_time_ms')
    list_filter = ('channel', 'model_used')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'key_prefix', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active',)
    search_fields = ('name', 'organization__name', 'key_prefix')
    readonly_fields = ('key_hash', 'key_prefix', 'created_at', 'last_used')
