from django.views.generic import ListView, DetailView, TemplateView
from .models import Formation

class FormationListView(ListView):
    model = Formation
    template_name = 'formations/formation_list.html'
    context_object_name = 'formations'
    paginate_by = 9

    def get_queryset(self):
        queryset = Formation.objects.filter(is_active=True)
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = dict(Formation.LEVEL_CHOICES)
        return context

class FormationDetailView(DetailView):
    model = Formation
    template_name = 'formations/formation_detail.html'
    context_object_name = 'formation'

    def get_queryset(self):
        return Formation.objects.filter(is_active=True)

class FormationIndexView(TemplateView):
    template_name = 'formations/formation_index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_formations'] = Formation.objects.filter(is_active=True).order_by('-created_at')[:3]
        context['total_formations'] = Formation.objects.filter(is_active=True).count()
        context['levels'] = dict(Formation.LEVEL_CHOICES)

        # Récupérer les 3 plans de formation pour le tableau comparatif
        plan_titles = [
            "Formule Initiation : Découvrez le code avec l'IA",
            "Formule Création : Réalisez votre première application IA",
            "Formule Maîtrise : Devenez autonome et performant avec l'IA"
        ]
        formation_plans = []
        for title in plan_titles:
            try:
                plan = Formation.objects.get(title=title, is_active=True)
                formation_plans.append(plan)
            except Formation.DoesNotExist:
                pass  # Gère le cas où une formation n'existe pas

        context['formation_plans'] = formation_plans
        
        return context 