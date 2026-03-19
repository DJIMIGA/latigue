import json
import logging
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate

from .models import Organization, SaaSPlan, AgentConfig, SaaSSubscription, UsageLog, APIKey
from .services.openclaw_client import OpenClawClient
from .services.agent_provisioner import create_agent as provision_agent, update_agent as update_agent_files, update_bindings, get_agent_bindings, is_whatsapp_connected
from .services.openclaw_ws import start_whatsapp_login, wait_whatsapp_login
from .services.paydunya_billing import create_subscription_invoice, activate_subscription, setup_paydunya

logger = logging.getLogger(__name__)


# Mapping service type → plan SaaS slug
SERVICE_TYPE_TO_PLAN = {
    'basic': 'starter',
    'standard': 'business',
    'premium': 'enterprise',
}

# Mapping formation level → plan SaaS slug
FORMATION_LEVEL_TO_PLAN = {
    'debutant': 'starter',
    'intermediaire': 'business',
    'avance': 'enterprise',
}


# ============================================================
# Inscription
# ============================================================

def signup(request):
    if request.user.is_authenticated:
        return redirect('saas:client_dashboard')

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not username or not email or not password:
            error = "Tous les champs sont obligatoires."
        elif len(password) < 8:
            error = "Le mot de passe doit contenir au moins 8 caracteres."
        elif password != password2:
            error = "Les mots de passe ne correspondent pas."
        elif not re.match(r'^[\w.+-]+@[\w.-]+\.\w+$', email):
            error = "Adresse email invalide."
        elif User.objects.filter(username=username).exists():
            error = "Ce nom d'utilisateur est deja pris."
        elif User.objects.filter(email=email).exists():
            error = "Un compte existe deja avec cet email."
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            auth_login(request, user)
            next_url = request.POST.get('next', '') or request.GET.get('next', '')
            return redirect(next_url or 'saas:client_dashboard')

    return render(request, 'auth/signup.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


# ============================================================
# Dashboard client (polyvalent : agent + formations)
# ============================================================

@login_required
def client_dashboard(request):
    org = Organization.objects.filter(owner=request.user, is_active=True).first()

    agent = None
    subscription = None
    usage_stats = {}
    gateway_healthy = False

    if org:
        agent = AgentConfig.objects.filter(organization=org).first()
        subscription = SaaSSubscription.objects.filter(
            organization=org, status__in=['active', 'trial']
        ).first()

        if agent:
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            usage_qs = UsageLog.objects.filter(
                agent_config=agent, timestamp__gte=thirty_days_ago
            )
            total_tokens = usage_qs.aggregate(
                inp=Sum('tokens_input'),
                out=Sum('tokens_output'),
            )
            usage_stats = {
                'total_calls': usage_qs.count(),
                'total_tokens': (total_tokens['inp'] or 0) + (total_tokens['out'] or 0),
                'avg_response_ms': usage_qs.aggregate(avg=Avg('response_time_ms'))['avg'] or 0,
            }

        try:
            gateway_healthy = OpenClawClient().health_check()
        except Exception:
            pass

    # Formations inscrites
    from formations.models import Enrollment
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

    context = {
        'org': org,
        'agent': agent,
        'subscription': subscription,
        'usage_stats': usage_stats,
        'gateway_healthy': gateway_healthy,
        'enrollment_data': enrollment_data,
    }
    if not org:
        context['plans'] = SaaSPlan.objects.filter(is_active=True).order_by('order')

    return render(request, 'saas/dashboard.html', context)


# ============================================================
# Onboarding (supporte from_service ET from_formation)
# ============================================================

@login_required
def onboarding(request):
    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    if org and AgentConfig.objects.filter(organization=org, status='active').exists():
        return redirect('saas:client_dashboard')

    plans = SaaSPlan.objects.filter(is_active=True).order_by('order')
    step = request.GET.get('step', '1')
    subscription_id = request.GET.get('subscription_id', '')

    subscription = None
    if subscription_id:
        subscription = SaaSSubscription.objects.filter(
            id=subscription_id, organization__owner=request.user
        ).first()

    preselected_plan = ''
    from_service = request.GET.get('from_service', '')
    from_service_obj = None
    from_formation = request.GET.get('from_formation', '')
    from_formation_obj = None

    # Pre-selection depuis /services/
    if from_service:
        from services.models import Service
        from_service_obj = Service.objects.filter(slug=from_service, category='ia_automation').first()
        if from_service_obj:
            preselected_plan = SERVICE_TYPE_TO_PLAN.get(from_service_obj.type, '')
            if not org:
                step = '1'

    # Pre-selection depuis /formations/
    if from_formation:
        from formations.models import Formation
        from_formation_obj = Formation.objects.filter(slug=from_formation, is_active=True).first()
        if from_formation_obj:
            preselected_plan = preselected_plan or FORMATION_LEVEL_TO_PLAN.get(from_formation_obj.level, '')
            if not org:
                step = '1'

    from django.conf import settings as app_settings
    return render(request, 'saas/onboarding.html', {
        'plans': plans,
        'step': step,
        'org': org,
        'subscription': subscription,
        'preselected_plan': preselected_plan,
        'from_service': from_service,
        'from_service_obj': from_service_obj,
        'from_formation': from_formation,
        'from_formation_obj': from_formation_obj,
        'trial_enabled': app_settings.SAAS_TRIAL_ENABLED,
        'trial_days': app_settings.SAAS_TRIAL_DAYS,
    })


@login_required
@require_POST
def onboarding_create_org(request):
    name = request.POST.get('name', '').strip()
    contact_email = request.POST.get('contact_email', '').strip()
    contact_phone = request.POST.get('contact_phone', '').strip()

    if not name or not contact_email:
        plans = SaaSPlan.objects.filter(is_active=True)
        return render(request, 'saas/onboarding.html', {
            'step': '1',
            'error': "Le nom et l'email sont obligatoires.",
            'plans': plans,
        })

    # Anti-doublon : verifier que l'email/telephone n'est pas deja utilise par une autre org
    existing_email = Organization.objects.filter(
        contact_email=contact_email, is_active=True
    ).exclude(owner=request.user).exists()
    if existing_email:
        plans = SaaSPlan.objects.filter(is_active=True)
        return render(request, 'saas/onboarding.html', {
            'step': '1',
            'error': "Cet email de contact est deja utilise par une autre organisation.",
            'plans': plans,
        })

    if contact_phone:
        existing_phone = Organization.objects.filter(
            contact_phone=contact_phone, is_active=True
        ).exclude(owner=request.user).exists()
        if existing_phone:
            plans = SaaSPlan.objects.filter(is_active=True)
            return render(request, 'saas/onboarding.html', {
                'step': '1',
                'error': "Ce numero de telephone est deja utilise par une autre organisation.",
                'plans': plans,
            })

    org, created = Organization.objects.get_or_create(
        owner=request.user,
        defaults={
            'name': name,
            'contact_email': contact_email,
            'contact_phone': contact_phone,
        }
    )
    if not created:
        org.name = name
        org.contact_email = contact_email
        org.contact_phone = contact_phone
        org.save()

    redirect_url = '/saas/onboarding/?step=2'
    from_service = request.POST.get('from_service', '')
    from_formation = request.POST.get('from_formation', '')
    if from_service:
        redirect_url += f'&from_service={from_service}'
    if from_formation:
        redirect_url += f'&from_formation={from_formation}'
    return redirect(redirect_url)


@login_required
@require_POST
def onboarding_choose_plan(request):
    org = get_object_or_404(Organization, owner=request.user, is_active=True)
    plan_slug = request.POST.get('plan_slug', '')
    agent_name = request.POST.get('agent_name', '').strip()
    company_info = request.POST.get('company_info', '').strip()

    plan = get_object_or_404(SaaSPlan, slug=plan_slug, is_active=True)

    if not agent_name:
        agent_name = f'Assistant {org.name}'

    # Generer un agent_id unique
    agent_id = f'client-{slugify(org.name)[:30]}'
    base_id = agent_id
    counter = 1
    while AgentConfig.objects.filter(agent_id=agent_id).exists():
        agent_id = f'{base_id}-{counter}'
        counter += 1

    # Auto-peupler WhatsApp depuis le telephone de l'organisation
    wa_number = org.contact_phone.strip() if org.contact_phone else ''
    wa_channels = 'whatsapp' if wa_number else 'none'

    agent_config, created = AgentConfig.objects.get_or_create(
        organization=org,
        defaults={
            'plan': plan,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'company_info': company_info,
            'status': 'provisioning',
            'whatsapp_number': wa_number,
            'channels': wa_channels,
        }
    )
    if not created:
        agent_config.plan = plan
        agent_config.agent_name = agent_name
        agent_config.company_info = company_info
        # Mettre a jour WhatsApp si pas encore configure
        if not agent_config.whatsapp_number and wa_number:
            agent_config.whatsapp_number = wa_number
            agent_config.channels = wa_channels
        agent_config.save()

    # Stocker la formation liee si elle vient de /formations/
    linked_formation_slug = request.POST.get('from_formation', '')

    from django.conf import settings as app_settings

    # Trial gratuit uniquement sur le plan Starter
    is_trial = app_settings.SAAS_TRIAL_ENABLED and plan.slug == 'starter'

    if is_trial:
        # Anti-doublon trial : 1 seul essai par user, email ou telephone
        already_trialed = SaaSSubscription.objects.filter(
            status__in=['trial', 'active', 'expired'],
            organization__owner=request.user,
        ).filter(
            Q(amount_xof=0) | Q(status='trial')
        ).exists()

        if not already_trialed and org.contact_email:
            already_trialed = SaaSSubscription.objects.filter(
                status__in=['trial', 'active', 'expired'],
                organization__contact_email=org.contact_email,
            ).filter(
                Q(amount_xof=0) | Q(status='trial')
            ).exists()

        if not already_trialed and org.contact_phone:
            already_trialed = SaaSSubscription.objects.filter(
                status__in=['trial', 'active', 'expired'],
                organization__contact_phone=org.contact_phone,
            ).filter(
                Q(amount_xof=0) | Q(status='trial')
            ).exists()

        if already_trialed:
            return render(request, 'saas/payment_result.html', {
                'error': "Vous avez deja beneficie d'un essai gratuit. Veuillez choisir un plan payant.",
            })

        # Mode essai gratuit — activation directe sans paiement
        now = timezone.now()
        trial_days = app_settings.SAAS_TRIAL_DAYS
        subscription = SaaSSubscription.objects.create(
            organization=org,
            plan=plan,
            status='trial',
            amount_xof=0,
            start_date=now,
            end_date=now + timezone.timedelta(days=trial_days),
            linked_formation_slug=linked_formation_slug,
        )
        _activate_agent_after_payment(subscription)
        return render(request, 'saas/payment_result.html', {
            'success': True,
            'trial': True,
            'trial_days': trial_days,
            'subscription': subscription,
        })
    else:
        # Plan payant — demande en attente de validation admin
        subscription = SaaSSubscription.objects.create(
            organization=org,
            plan=plan,
            status='pending',
            amount_xof=plan.price_xof,
            linked_formation_slug=linked_formation_slug,
        )
        return render(request, 'saas/payment_result.html', {
            'pending_validation': True,
            'subscription': subscription,
        })


@login_required
@require_POST
def onboarding_payment(request):
    subscription_id = request.POST.get('subscription_id')
    subscription = get_object_or_404(
        SaaSSubscription, id=subscription_id,
        organization__owner=request.user
    )

    redirect_url, error = create_subscription_invoice(request, subscription)
    if redirect_url:
        return redirect(redirect_url)

    return render(request, 'saas/onboarding.html', {
        'step': '3',
        'error': error,
        'subscription': subscription,
        'plans': SaaSPlan.objects.filter(is_active=True),
    })


# ============================================================
# Payment callbacks
# ============================================================

def _activate_agent_after_payment(subscription):
    """Active l'agent OpenClaw + inscription formation apres paiement."""
    # 1. Provisionner l'agent
    agent = AgentConfig.objects.filter(
        organization=subscription.organization
    ).first()
    if agent and agent.status == 'provisioning':
        try:
            provision_agent(agent)
            # Creer les bindings WhatsApp/Telegram si configures
            if agent.channels != 'none':
                update_bindings(agent)
            agent.status = 'active'
            agent.save(update_fields=['status'])
            logger.info(f'Agent {agent.agent_id} active apres paiement')
        except Exception as e:
            agent.status = 'error'
            agent.error_message = str(e)
            agent.save(update_fields=['status', 'error_message'])
            logger.error(f'Agent provisioning failed: {e}')

    # 2. Inscrire a la formation liee si applicable
    if subscription.linked_formation_slug:
        try:
            from formations.models import Formation, Enrollment
            formation = Formation.objects.filter(
                slug=subscription.linked_formation_slug, is_active=True
            ).first()
            if formation:
                Enrollment.objects.get_or_create(
                    user=subscription.organization.owner,
                    formation=formation,
                )
                logger.info(f'Enrollment cree pour {subscription.organization.owner} - {formation.title}')
        except Exception as e:
            logger.error(f'Enrollment creation failed: {e}')


@login_required
def payment_return(request):
    token = request.GET.get('token', '')
    if token:
        paydunya_mod = setup_paydunya()
        invoice = paydunya_mod.Invoice()
        if invoice.confirm(token):
            subscription = SaaSSubscription.objects.filter(
                paydunya_token=token
            ).first()
            if subscription and subscription.status != 'active':
                activate_subscription(subscription)
                _activate_agent_after_payment(subscription)
            return render(request, 'saas/payment_result.html', {
                'success': True,
                'subscription': subscription,
            })
    return render(request, 'saas/payment_result.html', {
        'error': 'Impossible de confirmer le paiement.',
    })


@login_required
def payment_cancel(request):
    return render(request, 'saas/payment_result.html', {'cancelled': True})


@csrf_exempt
@require_POST
def payment_callback(request):
    """Webhook IPN PayDunya."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse(status=400)

    token = data.get('data', {}).get('hash', '') or data.get('token', '')
    if not token:
        return HttpResponse(status=400)

    paydunya_mod = setup_paydunya()
    invoice = paydunya_mod.Invoice()
    if invoice.confirm(token):
        custom_data = invoice.custom_data or {}
        payment_token = custom_data.get('payment_token', '')
        subscription = SaaSSubscription.objects.filter(
            payment_token=payment_token
        ).first()
        if subscription and subscription.status != 'active':
            subscription.paydunya_token = token
            activate_subscription(subscription)
            _activate_agent_after_payment(subscription)
            logger.info(f'IPN SaaS: Subscription {subscription.id} activated')
    return HttpResponse(status=200)


# ============================================================
# Changement de plan
# ============================================================

@login_required
def change_plan(request):
    org = get_object_or_404(Organization, owner=request.user, is_active=True)
    agent = AgentConfig.objects.filter(organization=org).first()
    current_sub = SaaSSubscription.objects.filter(
        organization=org, status__in=['active', 'trial']
    ).first()
    plans = SaaSPlan.objects.filter(is_active=True).order_by('order')

    error = ''

    if request.method == 'POST':
        plan_slug = request.POST.get('plan_slug', '')
        new_plan = SaaSPlan.objects.filter(slug=plan_slug, is_active=True).first()

        if not new_plan:
            error = "Plan invalide."
        elif current_sub and current_sub.plan == new_plan and current_sub.status == 'active':
            error = "Vous etes deja sur ce plan."
        else:
            new_sub = SaaSSubscription.objects.create(
                organization=org,
                plan=new_plan,
                status='pending',
                amount_xof=new_plan.price_xof,
            )

            # Mettre a jour le plan de l'agent
            if agent:
                agent.plan = new_plan
                agent.save(update_fields=['plan'])

            return render(request, 'saas/payment_result.html', {
                'pending_validation': True,
                'subscription': new_sub,
                'is_change': True,
            })

    return render(request, 'saas/change_plan.html', {
        'org': org,
        'agent': agent,
        'current_sub': current_sub,
        'plans': plans,
        'error': error,
    })


# ============================================================
# Profil utilisateur
# ============================================================

@login_required
def edit_profile(request):
    success = ''
    error = ''

    if request.method == 'POST':
        action = request.POST.get('action', 'update_info')

        if action == 'update_info':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not email or not re.match(r'^[\w.+-]+@[\w.-]+\.\w+$', email):
                error = "Adresse email invalide."
            elif User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                error = "Un autre compte utilise deja cet email."
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save(update_fields=['first_name', 'last_name', 'email'])
                success = "Vos informations ont ete mises a jour."

        elif action == 'change_password':
            current = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            new_pw2 = request.POST.get('new_password2', '')

            if not request.user.check_password(current):
                error = "Mot de passe actuel incorrect."
            elif len(new_pw) < 8:
                error = "Le nouveau mot de passe doit contenir au moins 8 caracteres."
            elif new_pw != new_pw2:
                error = "Les mots de passe ne correspondent pas."
            else:
                request.user.set_password(new_pw)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                success = "Mot de passe modifie avec succes."

    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    subscription = None
    agent = None
    if org:
        subscription = SaaSSubscription.objects.filter(
            organization=org, status__in=['active', 'trial']
        ).first()
        agent = AgentConfig.objects.filter(organization=org).first()

    return render(request, 'saas/profile.html', {
        'org': org,
        'subscription': subscription,
        'agent': agent,
        'success': success,
        'error': error,
    })


# ============================================================
# Agent settings
# ============================================================

@login_required
def agent_settings(request):
    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    if not org:
        return redirect('saas:onboarding')
    agent = AgentConfig.objects.filter(organization=org).first()
    if not agent:
        return redirect('saas:onboarding')

    channels_success = ''
    channels_error = ''

    if request.method == 'POST':
        action = request.POST.get('action', 'update_agent')

        if action == 'update_channels':
            channels = request.POST.get('channels', agent.channels)
            telegram_id = request.POST.get('telegram_id', '').strip()
            whatsapp_number = request.POST.get('whatsapp_number', agent.whatsapp_number or '').strip()

            # Validation : seul Telegram necessite un ID (acces prive du proprio)
            if channels in ('telegram', 'both') and not telegram_id:
                channels_error = "L'ID Telegram est requis pour activer ce canal."
            elif telegram_id and not re.match(r'^\d{5,15}$', telegram_id):
                channels_error = "L'ID Telegram doit etre un nombre (ex: 7573032790)."
            else:
                agent.channels = channels
                agent.telegram_id = telegram_id
                agent.whatsapp_number = whatsapp_number
                agent.save(update_fields=['channels', 'telegram_id', 'whatsapp_number'])
                try:
                    update_bindings(agent)
                    channels_success = "Canaux mis a jour avec succes."
                except Exception as e:
                    logger.error(f'Bindings update failed: {e}')
                    channels_error = f"Erreur lors de la mise a jour des bindings: {e}"
        else:
            # update_agent (default)
            agent.agent_name = request.POST.get('agent_name', agent.agent_name).strip()
            agent.persona = request.POST.get('persona', agent.persona).strip()
            agent.company_info = request.POST.get('company_info', agent.company_info).strip()
            agent.save()
            try:
                update_agent_files(agent)
            except Exception as e:
                logger.error(f'Agent update failed: {e}')
            return redirect('saas:agent_settings')

    # Lire les bindings actuels depuis openclaw.json
    current_bindings = []
    try:
        current_bindings = get_agent_bindings(agent.agent_id)
    except Exception:
        pass

    # Statut WhatsApp du client (multi-account)
    wa_connected = False
    try:
        wa_connected = is_whatsapp_connected(agent.agent_id)
    except Exception:
        pass

    # Numero WhatsApp du client (pour le QR code wa.me)
    wa_number = agent.whatsapp_number or ''
    wa_number_clean = wa_number.lstrip('+')
    wa_link = f'https://wa.me/{wa_number_clean}' if wa_number_clean else ''

    return render(request, 'saas/agent_settings.html', {
        'org': org,
        'agent': agent,
        'current_bindings': current_bindings,
        'channels_success': channels_success,
        'channels_error': channels_error,
        'wa_connected': wa_connected,
        'wa_link': wa_link,
        'has_api_access': agent.plan.api_access,
    })


# ============================================================
# Usage
# ============================================================

@login_required
def usage_view(request):
    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    if not org:
        return redirect('saas:onboarding')
    agent = AgentConfig.objects.filter(organization=org).first()
    if not agent:
        return redirect('saas:onboarding')

    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    daily_usage = (
        UsageLog.objects.filter(agent_config=agent, timestamp__gte=thirty_days_ago)
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(calls=Count('id'), tokens_in=Sum('tokens_input'), tokens_out=Sum('tokens_output'))
        .order_by('date')
    )

    now = timezone.now()
    total_tokens_month = UsageLog.objects.filter(
        agent_config=agent,
        timestamp__month=now.month,
        timestamp__year=now.year,
    ).aggregate(
        inp=Sum('tokens_input'), out=Sum('tokens_output')
    )
    tokens_used = (total_tokens_month['inp'] or 0) + (total_tokens_month['out'] or 0)

    return render(request, 'saas/usage.html', {
        'org': org,
        'agent': agent,
        'daily_usage': list(daily_usage),
        'tokens_used': tokens_used,
        'plan': agent.plan,
    })


# ============================================================
# Admin overview (staff)
# ============================================================

@login_required
@staff_member_required
@require_POST
def admin_activate_subscription(request, subscription_id):
    """Admin valide une demande d'abonnement et provisionne l'agent."""
    subscription = get_object_or_404(SaaSSubscription, id=subscription_id, status='pending')
    action = request.POST.get('action', 'activate')

    if action == 'reject':
        subscription.status = 'cancelled'
        subscription.save(update_fields=['status'])
        agent = AgentConfig.objects.filter(organization=subscription.organization).first()
        if agent and agent.status == 'provisioning':
            agent.status = 'deleted'
            agent.save(update_fields=['status'])
        logger.info(f'Admin: subscription {subscription.id} rejected for {subscription.organization.name}')
    else:
        now = timezone.now()
        subscription.status = 'active'
        subscription.start_date = now
        subscription.end_date = now + timezone.timedelta(days=30)
        subscription.save(update_fields=['status', 'start_date', 'end_date'])
        _activate_agent_after_payment(subscription)
        logger.info(f'Admin: subscription {subscription.id} activated for {subscription.organization.name}')

    return redirect('saas:admin_overview')


@login_required
@staff_member_required
def admin_overview(request):
    organizations = Organization.objects.filter(is_active=True).select_related('owner')
    db_agents = AgentConfig.objects.select_related('organization', 'plan')
    active_subs = SaaSSubscription.objects.filter(status__in=['active', 'trial']).select_related('organization', 'plan')
    pending_subs = SaaSSubscription.objects.filter(status='pending').select_related('organization', 'plan')

    total_revenue = active_subs.aggregate(total=Sum('amount_xof'))['total'] or 0

    gateway_healthy = False
    try:
        gateway_healthy = OpenClawClient().health_check()
    except Exception:
        pass

    # Lire les agents live depuis openclaw.json
    from django.conf import settings
    live_agents = []
    try:
        with open(settings.OPENCLAW_CONFIG_PATH, 'r') as f:
            oc_config = json.load(f)
        db_agent_ids = set(db_agents.values_list('agent_id', flat=True))
        for ag in oc_config.get('agents', {}).get('list', []):
            agent_id = ag.get('id', '')
            model_cfg = ag.get('model', oc_config.get('agents', {}).get('defaults', {}).get('model', {}))
            model_name = model_cfg.get('primary', 'N/A') if isinstance(model_cfg, dict) else str(model_cfg)
            # Simplifier le nom du modele
            model_short = model_name.split('/')[-1] if '/' in model_name else model_name
            live_agents.append({
                'id': agent_id,
                'name': ag.get('name', '') or ag.get('identity', {}).get('name', agent_id),
                'emoji': ag.get('identity', {}).get('emoji', '🤖'),
                'model': model_short,
                'workspace': ag.get('workspace', ''),
                'is_default': ag.get('default', False),
                'in_db': agent_id in db_agent_ids,
            })
    except Exception:
        pass

    # Channels et bindings depuis openclaw.json
    channels_info = []
    try:
        for ch_name, ch_conf in oc_config.get('channels', {}).items():
            channels_info.append({
                'name': ch_name,
                'dm_policy': ch_conf.get('dmPolicy', 'N/A'),
                'group_policy': ch_conf.get('groupPolicy', 'N/A'),
            })
    except Exception:
        pass

    bindings_info = []
    try:
        for b in oc_config.get('bindings', []):
            bindings_info.append({
                'agent_id': b.get('agentId', ''),
                'channel': b.get('match', {}).get('channel', ''),
                'number': b.get('match', {}).get('from', ''),
            })
    except Exception:
        pass

    return render(request, 'saas/admin_overview.html', {
        'organizations': organizations,
        'db_agents': db_agents,
        'live_agents': live_agents,
        'subscriptions': active_subs,
        'total_revenue': total_revenue,
        'gateway_healthy': gateway_healthy,
        'total_clients': organizations.count(),
        'active_db_agents': db_agents.filter(status='active').count(),
        'total_live_agents': len(live_agents),
        'channels_info': channels_info,
        'bindings_info': bindings_info,
        'pending_subs': pending_subs,
    })


# ============================================================
# WhatsApp QR code (AJAX endpoints)
# ============================================================

@login_required
@require_POST
def whatsapp_qr_start(request):
    """Lance le login WhatsApp et retourne le QR code en base64."""
    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    if not org:
        return JsonResponse({'error': 'Pas d\'organisation'}, status=403)
    agent = AgentConfig.objects.filter(organization=org, status='active').first()
    if not agent:
        return JsonResponse({'error': 'Pas d\'agent actif'}, status=404)
    if agent.channels not in ('whatsapp', 'both'):
        return JsonResponse({'error': 'WhatsApp non active'}, status=400)

    try:
        qr_data_url = start_whatsapp_login(agent.agent_id)
        if not qr_data_url:
            return JsonResponse({'error': 'QR code vide — reessayez'}, status=500)
        return JsonResponse({'qr_data_url': qr_data_url})
    except Exception as e:
        logger.error(f'WhatsApp QR start failed for {agent.agent_id}: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def whatsapp_qr_wait(request):
    """Attend que le QR WhatsApp soit scanne (long-polling ~90s max)."""
    org = Organization.objects.filter(owner=request.user, is_active=True).first()
    if not org:
        return JsonResponse({'error': 'Pas d\'organisation'}, status=403)
    agent = AgentConfig.objects.filter(organization=org, status='active').first()
    if not agent:
        return JsonResponse({'error': 'Pas d\'agent actif'}, status=404)

    try:
        connected = wait_whatsapp_login(agent.agent_id)
        return JsonResponse({'connected': connected})
    except Exception as e:
        logger.error(f'WhatsApp QR wait failed for {agent.agent_id}: {e}')
        return JsonResponse({'error': str(e), 'connected': False}, status=500)


# ============================================================
# API proxy (pour acces programmatique via API key)
# ============================================================

@csrf_exempt
@require_POST
def api_chat(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return JsonResponse({'error': 'Missing API key'}, status=401)

    raw_key = auth[7:].strip()
    key_hash = APIKey.hash_key(raw_key)
    api_key = APIKey.objects.filter(key_hash=key_hash, is_active=True).first()
    if not api_key:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    api_key.last_used = timezone.now()
    api_key.save(update_fields=['last_used'])

    org = api_key.organization
    agent = AgentConfig.objects.filter(organization=org, status='active').first()
    if not agent:
        return JsonResponse({'error': 'No active agent'}, status=404)

    subscription = SaaSSubscription.objects.filter(
        organization=org, status__in=['active', 'trial']
    ).first()
    if not subscription or not subscription.is_active:
        return JsonResponse({'error': 'No active subscription'}, status=403)

    if not agent.plan.api_access:
        return JsonResponse({'error': 'API access requires Enterprise plan'}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    messages = body.get('messages', [])
    if not messages:
        return JsonResponse({'error': 'No messages'}, status=400)

    client = OpenClawClient()
    text, usage, elapsed_ms = client.chat(agent.agent_id, messages)

    if usage:
        UsageLog.objects.create(
            agent_config=agent,
            tokens_input=usage.get('prompt_tokens', usage.get('input_tokens', 0)),
            tokens_output=usage.get('completion_tokens', usage.get('output_tokens', 0)),
            model_used=agent.plan.model_id,
            channel='api',
            response_time_ms=elapsed_ms,
        )

    if text:
        return JsonResponse({'response': text, 'usage': usage})
    return JsonResponse({'error': 'Gateway error'}, status=502)
