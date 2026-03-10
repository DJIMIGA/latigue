from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='service_list'),
    # Paiement services IA
    path('paiement/<slug:slug>/', views.initiate_service_payment, name='initiate_service_payment'),
    path('paiement/retour/', views.service_payment_return, name='service_payment_return'),
    path('paiement/callback/', views.service_payment_callback, name='service_payment_callback'),
    # Detail (must be last — slug catch-all)
    path('<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
]
