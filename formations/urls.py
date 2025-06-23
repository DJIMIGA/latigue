from django.urls import path
from . import views

app_name = 'formations'

urlpatterns = [
    path('', views.FormationIndexView.as_view(), name='formation_index'),
    path('liste/', views.FormationListView.as_view(), name='formation_list'),
    path('<slug:slug>/', views.FormationDetailView.as_view(), name='formation_detail'),
] 