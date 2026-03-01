"""
URLs pour l'interface web de production vidéo.
"""

from django.urls import path
from . import views
from . import views_scripts

app_name = 'marketing'

urlpatterns = [
    # Dashboard
    path('', views.VideoProductionDashboardView.as_view(), name='dashboard'),
    
    # Scripts library
    path('scripts/', views_scripts.VideoScriptLibraryView.as_view(), name='scripts_library'),
    path('scripts/<int:pk>/', views_scripts.VideoScriptDetailView.as_view(), name='script_detail'),
    path('scripts/<int:pk>/use/', views_scripts.script_use_for_job, name='script_use_for_job'),
    path('api/scripts/<int:pk>/preview/', views_scripts.api_script_preview, name='api_script_preview'),
    
    # Job creation wizard
    path('job/create/', views.VideoJobCreateView.as_view(), name='job_create'),
    path('job/<int:pk>/configure/', views.VideoJobConfigureSegmentsView.as_view(), name='job_configure_segments'),
    
    # Job detail & monitoring
    path('job/<int:pk>/', views.VideoJobDetailView.as_view(), name='job_detail'),
    
    # Job actions
    path('job/<int:pk>/generate/', views.job_start_generation, name='job_generate'),
    path('job/<int:pk>/cancel/', views.job_cancel, name='job_cancel'),
    
    # Quick generation
    path('quick/', views.quick_video_view, name='quick_video'),
    
    # API endpoints (polling temps réel)
    path('api/job/<int:pk>/status/', views.api_job_status, name='api_job_status'),
    path('api/job/<int:job_pk>/segment/<int:segment_index>/retry/', views.api_segment_retry, name='api_segment_retry'),
    
    # Assets library
    path('assets/', views.assets_library_view, name='assets_library'),
    path('assets/upload/', views.assets_upload_view, name='assets_upload'),
    path('assets/<int:pk>/delete/', views.asset_delete_view, name='asset_delete'),
    
    # AI Assistant
    path('assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('api/ai/chat/', views.ai_chat_view, name='ai_chat'),
    path('api/ai/generate-job/', views.ai_generate_job_view, name='ai_generate_job'),
    
    # User settings
    path('settings/', views.user_settings_view, name='user_settings'),
]
