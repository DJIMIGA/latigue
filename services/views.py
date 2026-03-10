import uuid
import json
import logging
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

from .models import Service, ServiceOrder, Subscription

logger = logging.getLogger(__name__)


class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 9

    def get_queryset(self):
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
def initiate_service_payment(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True, category='ia_automation')

    if not service.price:
        return redirect('services:service_detail', slug=slug)

    amount_xof = int(service.price)
    payment_token = str(uuid.uuid4())

    if request.method == 'POST':
        paydunya = _setup_paydunya()
        store = paydunya.Store(name='Bolibana Services IA')
        store.tagline = 'Services IA & Automatisation'
        store.website_url = request.build_absolute_uri('/')

        invoice = paydunya.Invoice(store)
        invoice.total_amount = amount_xof

        invoice.return_url = request.build_absolute_uri(reverse('services:service_payment_return'))
        invoice.cancel_url = request.build_absolute_uri(reverse('services:service_detail', kwargs={'slug': slug}))
        invoice.callback_url = request.build_absolute_uri(reverse('services:service_payment_callback'))

        order = ServiceOrder.objects.create(
            user=request.user,
            service=service,
            order_type='installation',
            amount=service.price,
            payment_token=payment_token,
            status='pending',
        )

        from paydunya.invoice import InvoiceItem
        items = [InvoiceItem(
            name=service.title,
            quantity=1,
            unit_price=amount_xof,
            total_price=amount_xof,
            description=f"Service IA : {service.title} — Installation",
        )]
        custom_data = [
            ('payment_token', payment_token),
            ('service_slug', service.slug),
            ('user_id', str(request.user.id)),
            ('order_type', 'installation'),
        ]
        successful, response = invoice.create(items=items, custom_data=custom_data)
        if successful is True:
            order.paydunya_token = response.get('token', '')
            order.save()
            redirect_url = response.get('response_text', '')
            return redirect(redirect_url)
        else:
            order.status = 'failed'
            order.save()
            logger.error(f"PayDunya service invoice creation failed: {response}")
            return render(request, 'services/service_payment_summary.html', {
                'service': service,
                'amount_xof': amount_xof,
                'error': "Erreur lors de la création du paiement. Veuillez réessayer.",
            })

    return render(request, 'services/service_payment_summary.html', {
        'service': service,
        'amount_xof': amount_xof,
    })


@login_required
def service_payment_return(request):
    """Return URL après paiement PayDunya pour un service."""
    token = request.GET.get('token', '')
    if token:
        paydunya = _setup_paydunya()
        invoice = paydunya.Invoice()
        if invoice.confirm(token):
            order = ServiceOrder.objects.filter(paydunya_token=token).first()
            if order and order.status != 'completed':
                order.status = 'completed'
                order.save()
                _create_subscription(order)
            return render(request, 'services/service_payment_summary.html', {
                'success': True,
                'service': order.service if order else None,
            })
    return render(request, 'services/service_payment_summary.html', {
        'error': "Impossible de confirmer le paiement. Contactez-nous si le montant a été débité.",
    })


@csrf_exempt
@require_POST
def service_payment_callback(request):
    """Webhook IPN PayDunya pour services."""
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
        order = ServiceOrder.objects.filter(payment_token=payment_token).first()
        if order and order.status != 'completed':
            order.status = 'completed'
            order.paydunya_token = token
            order.save()
            _create_subscription(order)
            logger.info(f"IPN Service: Order {order.id} confirmed for user {order.user.username}")
    return HttpResponse(status=200)


def _create_subscription(order):
    """Crée ou renouvelle un abonnement après paiement confirmé."""
    now = timezone.now()
    # Check existing active subscription
    existing = Subscription.objects.filter(
        user=order.user, service=order.service, status='active'
    ).first()
    if existing and existing.end_date and existing.end_date > now:
        # Extend existing subscription
        existing.end_date = existing.end_date + timedelta(days=30)
        existing.save()
    else:
        Subscription.objects.create(
            user=order.user,
            service=order.service,
            status='active',
            start_date=now,
            end_date=now + timedelta(days=30),
            amount=order.amount,
            auto_renew=True,
        )
