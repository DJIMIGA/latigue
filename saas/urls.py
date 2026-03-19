from django.urls import path
from . import views

app_name = 'saas'

urlpatterns = [
    # Dashboard client
    path('dashboard/', views.client_dashboard, name='client_dashboard'),

    # Onboarding
    path('onboarding/', views.onboarding, name='onboarding'),
    path('onboarding/create-org/', views.onboarding_create_org, name='onboarding_create_org'),
    path('onboarding/choose-plan/', views.onboarding_choose_plan, name='onboarding_choose_plan'),
    path('onboarding/payment/', views.onboarding_payment, name='onboarding_payment'),

    # Profil
    path('profile/', views.edit_profile, name='edit_profile'),

    # Changement de plan
    path('change-plan/', views.change_plan, name='change_plan'),

    # Agent
    path('agent/', views.agent_settings, name='agent_settings'),

    # Usage
    path('usage/', views.usage_view, name='usage'),

    # Payment
    path('payment/return/', views.payment_return, name='payment_return'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),

    # Admin (staff)
    path('admin-saas/', views.admin_overview, name='admin_overview'),
    path('admin-saas/subscription/<int:subscription_id>/activate/', views.admin_activate_subscription, name='admin_activate_subscription'),

    # WhatsApp QR code (AJAX)
    path('whatsapp/qr/start/', views.whatsapp_qr_start, name='whatsapp_qr_start'),
    path('whatsapp/qr/wait/', views.whatsapp_qr_wait, name='whatsapp_qr_wait'),

    # API proxy
    path('api/chat/', views.api_chat, name='api_chat'),
]
