from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from formations.models import Formation, Enrollment, Payment
from services.models import Service, ServiceOrder, Capacite
from blog.models import Post
from newsletter.models import Subscriber
from saas.models import Organization, AgentConfig, SaaSSubscription
from saas.services.openclaw_client import OpenClawClient


@login_required
@staff_member_required
def dashboard_home(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Business stats
    total_users = User.objects.count()
    new_users_month = User.objects.filter(date_joined__gte=month_start).count()
    total_enrollments = Enrollment.objects.count()
    new_enrollments_month = Enrollment.objects.filter(enrolled_at__gte=month_start).count() if hasattr(Enrollment, 'enrolled_at') else 0

    # Revenue (formations + ancien services + SaaS)
    formation_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    service_revenue = ServiceOrder.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    saas_revenue = SaaSSubscription.objects.filter(status='active').aggregate(total=Sum('amount_xof'))['total'] or 0
    total_revenue = formation_revenue + service_revenue + saas_revenue

    month_revenue = (
        (Payment.objects.filter(status='completed', created_at__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0) +
        (ServiceOrder.objects.filter(status='completed', created_at__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0) +
        (SaaSSubscription.objects.filter(status='active', created_at__gte=month_start).aggregate(total=Sum('amount_xof'))['total'] or 0)
    )

    # Newsletter
    total_subscribers = Subscriber.objects.count()

    # Content stats
    total_posts = Post.objects.count()
    total_services = Service.objects.count()
    total_formations = Formation.objects.count()

    # SaaS stats
    saas_clients = Organization.objects.filter(is_active=True).count()
    saas_agents_active = AgentConfig.objects.filter(status='active').count()
    saas_agents_total = AgentConfig.objects.count()
    saas_active_subs = SaaSSubscription.objects.filter(status='active').count()
    saas_mrr = SaaSSubscription.objects.filter(status='active').aggregate(total=Sum('amount_xof'))['total'] or 0

    recent_saas_subs = list(
        SaaSSubscription.objects.filter(status='active')
        .select_related('organization', 'plan')
        .order_by('-created_at')[:5]
    )

    # Gateway health
    gateway_healthy = False
    try:
        gateway_healthy = OpenClawClient().health_check()
    except Exception:
        pass

    # Activity (30 days)
    new_users_daily = list(
        User.objects.filter(date_joined__gte=thirty_days_ago)
        .values('date_joined__date')
        .annotate(count=Count('id'))
        .order_by('-date_joined__date')[:10]
    )

    recent_payments = list(
        Payment.objects.filter(status='completed')
        .select_related('user', 'formation')
        .order_by('-created_at')[:10]
    )

    recent_orders = list(
        ServiceOrder.objects.filter(status='completed')
        .select_related('user', 'service')
        .order_by('-created_at')[:5]
    )

    # Capacités IA
    capacites = Capacite.objects.filter(is_active=True).order_by('category', 'order')
    capacites_by_category = {}
    for cap in capacites:
        cat = cap.get_category_display()
        if cat not in capacites_by_category:
            capacites_by_category[cat] = []
        capacites_by_category[cat].append(cap)

    active_count = capacites.filter(status='active').count()
    configuring_count = capacites.filter(status='configuring').count()
    available_count = capacites.filter(status='available').count()

    context = {
        'total_users': total_users,
        'new_users_month': new_users_month,
        'total_enrollments': total_enrollments,
        'new_enrollments_month': new_enrollments_month,
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'total_subscribers': total_subscribers,
        'total_posts': total_posts,
        'total_services': total_services,
        'total_formations': total_formations,
        'new_users_daily': new_users_daily,
        'recent_payments': recent_payments,
        'recent_orders': recent_orders,
        'capacites_by_category': capacites_by_category,
        'active_count': active_count,
        'configuring_count': configuring_count,
        'available_count': available_count,
        'total_capacites': capacites.count(),
        # SaaS
        'saas_clients': saas_clients,
        'saas_agents_active': saas_agents_active,
        'saas_agents_total': saas_agents_total,
        'saas_active_subs': saas_active_subs,
        'saas_mrr': saas_mrr,
        'saas_revenue': saas_revenue,
        'recent_saas_subs': recent_saas_subs,
        'gateway_healthy': gateway_healthy,
    }
    return render(request, 'dashboard/home.html', context)
