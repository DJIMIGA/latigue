from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Service

# Create your views here.

class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
        # Optimisation : order_by pour un ordre cohérent
        queryset = Service.objects.filter(is_active=True).order_by('category', 'type', 'price')
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = dict(Service.CATEGORY_CHOICES)
        return context

class ServiceDetailView(DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'

    def get_queryset(self):
        return Service.objects.filter(is_active=True)


