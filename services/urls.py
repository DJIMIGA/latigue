from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # La racine de l'app est déjà préfixée par "services/" dans latigue/urls.py
    # On expose donc simplement "/" et "/<slug>/" ici.
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
] 