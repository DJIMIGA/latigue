import uuid
import logging

from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

from .models import Formation, Module, Lesson, Enrollment, LessonProgress, Payment

logger = logging.getLogger(__name__)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(
                user=self.request.user, formation=self.object, is_active=True
            ).first()
            context['enrollment'] = enrollment
            if enrollment:
                context['progress'] = enrollment.get_progress()
        return context

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
    # Si déjà inscrit, rediriger vers le dashboard
    if Enrollment.objects.filter(user=request.user, formation=formation).exists():
        return redirect('formations:student_dashboard')
    # Si gratuit, inscription directe
    if formation.price == 0:
        Enrollment.objects.get_or_create(user=request.user, formation=formation)
        return redirect('formations:student_dashboard')
    # Sinon, rediriger vers le paiement
    return redirect('formations:initiate_payment', slug=slug)


def _setup_paydunya():
    """Configure PayDunya avec les clés depuis settings."""
    import paydunya
    paydunya.api_keys = {
        'PAYDUNYA-MASTER-KEY': settings.PAYDUNYA_MASTER_KEY,
        'PAYDUNYA-PRIVATE-KEY': settings.PAYDUNYA_PRIVATE_KEY,
        'PAYDUNYA-PUBLIC-KEY': settings.PAYDUNYA_PUBLIC_KEY,
        'PAYDUNYA-TOKEN': settings.PAYDUNYA_TOKEN,
    }
    paydunya.debug = (settings.PAYDUNYA_MODE == 'test')
    return paydunya


@login_required
def initiate_payment(request, slug):
    formation = get_object_or_404(Formation, slug=slug, is_active=True)

    # Déjà inscrit ?
    if Enrollment.objects.filter(user=request.user, formation=formation).exists():
        return redirect('formations:student_dashboard')

    # Gratuit ?
    if formation.price == 0:
        Enrollment.objects.get_or_create(user=request.user, formation=formation)
        return redirect('formations:student_dashboard')

    # Prix déjà en FCFA dans la DB
    amount_xof = int(formation.price)
    payment_token = str(uuid.uuid4())

    if request.method == 'POST':
        paydunya = _setup_paydunya()
        store = paydunya.Store(name='Bolibana Formations')
        store.tagline = 'Formations professionnelles'
        store.website_url = request.build_absolute_uri('/')

        invoice = paydunya.Invoice(store)
        invoice.add_item(
            name=formation.title,
            quantity=1,
            unit_price=amount_xof,
            total_price=amount_xof,
            description=f"Formation : {formation.title}",
        )
        invoice.total_amount = amount_xof

        # URLs de callback
        invoice.return_url = request.build_absolute_uri(reverse('formations:payment_return'))
        invoice.cancel_url = request.build_absolute_uri(reverse('formations:payment_cancel'))
        invoice.callback_url = request.build_absolute_uri(reverse('formations:payment_callback'))

        # Données custom
        invoice.add_custom_data('payment_token', payment_token)
        invoice.add_custom_data('formation_slug', formation.slug)
        invoice.add_custom_data('user_id', str(request.user.id))

        # Créer le paiement en base
        payment = Payment.objects.create(
            user=request.user,
            formation=formation,
            amount=formation.price,
            currency='XOF',
            payment_token=payment_token,
            status='pending',
        )

        success = invoice.create()
        if success:
            payment.paydunya_token = invoice.token
            payment.save()
            return redirect(invoice.url)
        else:
            payment.status = 'failed'
            payment.save()
            logger.error(f"PayDunya invoice creation failed: {invoice.response_text}")
            return render(request, 'formations/payment_summary.html', {
                'formation': formation,
                'amount_xof': amount_xof,
                'error': "Erreur lors de la création du paiement. Veuillez réessayer.",
            })

    return render(request, 'formations/payment_summary.html', {
        'formation': formation,
        'amount_xof': amount_xof,
    })


@login_required
def payment_return(request):
    """Return URL après paiement PayDunya."""
    token = request.GET.get('token', '')
    if token:
        paydunya = _setup_paydunya()
        invoice = paydunya.Invoice()
        if invoice.confirm(token):
            payment = Payment.objects.filter(paydunya_token=token).first()
            if payment and payment.status != 'completed':
                payment.status = 'completed'
                payment.save()
                Enrollment.objects.get_or_create(
                    user=payment.user, formation=payment.formation
                )
            return render(request, 'formations/payment_summary.html', {
                'success': True,
                'formation': payment.formation if payment else None,
            })
    return render(request, 'formations/payment_summary.html', {
        'error': "Impossible de confirmer le paiement. Contactez-nous si le montant a été débité.",
    })


@login_required
def payment_cancel(request):
    """Cancel URL après annulation PayDunya."""
    token = request.GET.get('token', '')
    if token:
        payment = Payment.objects.filter(paydunya_token=token).first()
        if payment and payment.status == 'pending':
            payment.status = 'cancelled'
            payment.save()
    return render(request, 'formations/payment_summary.html', {
        'cancelled': True,
    })


@csrf_exempt
@require_POST
def payment_callback(request):
    """Webhook IPN PayDunya (POST)."""
    import json
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse(status=400)

    token = data.get('data', {}).get('hash', '') or data.get('token', '')
    if not token:
        return HttpResponse(status=400)

    paydunya = _setup_paydunya()
    invoice = paydunya.Invoice()
    if invoice.confirm(token):
        custom_data = invoice.custom_data or {}
        payment_token = custom_data.get('payment_token', '')
        payment = Payment.objects.filter(payment_token=payment_token).first()
        if payment and payment.status != 'completed':
            payment.status = 'completed'
            payment.paydunya_token = token
            payment.save()
            Enrollment.objects.get_or_create(
                user=payment.user, formation=payment.formation
            )
            logger.info(f"IPN: Payment {payment.id} confirmed for user {payment.user.username}")
    return HttpResponse(status=200)


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