"""
URLs pour l'interface web de production vidéo.
"""

from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    # Dashboard
    path('', views.VideoProductionDashboardView.as_view(), name='dashboard'),
    
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
]
