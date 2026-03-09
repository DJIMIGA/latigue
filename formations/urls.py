from django.urls import path
from . import views

app_name = 'formations'

urlpatterns = [
    path('', views.FormationIndexView.as_view(), name='formation_index'),
    path('liste/', views.FormationListView.as_view(), name='formation_list'),
    # LMS - Espace élève
    path('espace-eleve/', views.student_dashboard, name='student_dashboard'),
    path('espace-eleve/<slug:slug>/', views.enrolled_formation_detail, name='enrolled_formation'),
    path('espace-eleve/<slug:slug>/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('espace-eleve/<slug:slug>/lecon/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('espace-eleve/lecon/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('inscription/<slug:slug>/', views.enrollment_view, name='enrollment'),
    # Existing
    path('<slug:slug>/', views.FormationDetailView.as_view(), name='formation_detail'),
]
