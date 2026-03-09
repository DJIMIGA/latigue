from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import Formation, Module, Lesson, Enrollment, LessonProgress

class FormationListView(ListView):
    model = Formation
    template_name = 'formations/formation_list.html'
    context_object_name = 'formations'
    paginate_by = 9

    def get_queryset(self):
        # Optimisation : order_by pour un ordre cohérent
        queryset = Formation.objects.filter(is_active=True).order_by('level', '-created_at')
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


@login_required
def enrollment_view(request, slug):
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user, formation=formation
    )
    return redirect('formations:student_dashboard')


@login_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(
        user=request.user, is_active=True
    ).select_related('formation')
    
    enrollment_data = []
    for enrollment in enrollments:
        enrollment_data.append({
            'enrollment': enrollment,
            'formation': enrollment.formation,
            'progress': enrollment.get_progress(),
        })
    
    return render(request, 'formations/student_dashboard.html', {
        'enrollment_data': enrollment_data,
    })


@login_required
def enrolled_formation_detail(request, slug):
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    enrollment = get_object_or_404(Enrollment, user=request.user, formation=formation, is_active=True)
    
    modules = formation.modules.prefetch_related('lessons').all()
    
    # Build progress map
    completed_ids = set(
        LessonProgress.objects.filter(
            user=request.user,
            lesson__module__formation=formation,
            completed=True
        ).values_list('lesson_id', flat=True)
    )
    
    module_data = []
    for module in modules:
        lessons = module.lessons.all()
        lesson_list = []
        for lesson in lessons:
            lesson_list.append({
                'lesson': lesson,
                'completed': lesson.id in completed_ids,
            })
        total = len(lesson_list)
        done = sum(1 for l in lesson_list if l['completed'])
        module_data.append({
            'module': module,
            'lessons': lesson_list,
            'total': total,
            'done': done,
            'progress': int((done / total) * 100) if total > 0 else 0,
        })
    
    return render(request, 'formations/enrolled_formation.html', {
        'formation': formation,
        'enrollment': enrollment,
        'module_data': module_data,
        'progress': enrollment.get_progress(),
    })


@login_required
def module_detail(request, slug, module_id):
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    get_object_or_404(Enrollment, user=request.user, formation=formation, is_active=True)
    module = get_object_or_404(Module, id=module_id, formation=formation)
    
    lessons = module.lessons.all()
    completed_ids = set(
        LessonProgress.objects.filter(
            user=request.user, lesson__in=lessons, completed=True
        ).values_list('lesson_id', flat=True)
    )
    
    lesson_list = []
    for lesson in lessons:
        lesson_list.append({
            'lesson': lesson,
            'completed': lesson.id in completed_ids,
        })
    
    total = len(lesson_list)
    done = sum(1 for l in lesson_list if l['completed'])
    
    return render(request, 'formations/module_detail.html', {
        'formation': formation,
        'module': module,
        'lesson_list': lesson_list,
        'progress': int((done / total) * 100) if total > 0 else 0,
    })


@login_required
def lesson_detail(request, slug, lesson_id):
    formation = get_object_or_404(Formation, slug=slug, is_active=True)
    enrollment = get_object_or_404(Enrollment, user=request.user, formation=formation, is_active=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__formation=formation)
    
    # Check completion
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    
    # Get all lessons in formation for nav
    all_lessons = list(
        Lesson.objects.filter(module__formation=formation).order_by('module__order', 'order')
    )
    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson.id), 0)
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
    
    # Get modules with lessons and progress for sidebar
    modules = Module.objects.filter(formation=formation).order_by('order').prefetch_related('lessons')
    completed_ids = set(
        LessonProgress.objects.filter(
            user=request.user, lesson__module__formation=formation, completed=True
        ).values_list('lesson_id', flat=True)
    )
    
    return render(request, 'formations/lesson_detail.html', {
        'formation': formation,
        'lesson': lesson,
        'module': lesson.module,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'current_index': current_index + 1,
        'total_lessons': len(all_lessons),
        'modules': modules,
        'completed_ids': completed_ids,
        'enrollment': enrollment,
    })


@login_required
def mark_lesson_complete(request, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    formation = lesson.module.formation
    
    # Verify enrollment
    get_object_or_404(Enrollment, user=request.user, formation=formation, is_active=True)
    
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.completed = not progress.completed
    progress.completed_at = timezone.now() if progress.completed else None
    progress.save()
    
    # Get overall progress
    enrollment = Enrollment.objects.get(user=request.user, formation=formation)
    
    return JsonResponse({
        'completed': progress.completed,
        'overall_progress': enrollment.get_progress(),
    })