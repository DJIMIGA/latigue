import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def setup_paydunya():
    """Configure PayDunya (meme pattern que formations/views.py)."""
    import paydunya
    paydunya.api_keys = {
        'PAYDUNYA-MASTER-KEY': settings.PAYDUNYA_MASTER_KEY,
        'PAYDUNYA-PRIVATE-KEY': settings.PAYDUNYA_PRIVATE_KEY,
        'PAYDUNYA-PUBLIC-KEY': settings.PAYDUNYA_PUBLIC_KEY,
        'PAYDUNYA-TOKEN': settings.PAYDUNYA_TOKEN,
    }
    paydunya.debug = (settings.PAYDUNYA_MODE == 'test')
    return paydunya


def create_subscription_invoice(request, subscription):
    """
    Cree une facture PayDunya pour un abonnement SaaS.
    Returns (redirect_url, error_message).
    """
    paydunya_mod = setup_paydunya()

    store = paydunya_mod.Store(name='DJIMIGA TECH - IA SaaS')
    store.tagline = 'Assistants IA pour PME'
    store.website_url = request.build_absolute_uri('/')

    invoice = paydunya_mod.Invoice(store)
    invoice.total_amount = subscription.amount_xof

    from django.urls import reverse
    invoice.return_url = request.build_absolute_uri(reverse('saas:payment_return'))
    invoice.cancel_url = request.build_absolute_uri(reverse('saas:payment_cancel'))
    invoice.callback_url = request.build_absolute_uri(reverse('saas:payment_callback'))

    items = [{
        'name': f'Abonnement {subscription.plan.name}',
        'quantity': 1,
        'unit_price': subscription.amount_xof,
        'total_price': subscription.amount_xof,
        'description': f'IA SaaS - {subscription.plan.name} - {subscription.organization.name}',
    }]

    custom_data = {
        'payment_token': str(subscription.payment_token),
        'organization_slug': subscription.organization.slug,
        'plan_slug': subscription.plan.slug,
    }

    invoice.add_items(items)
    invoice.add_custom_data(custom_data)

    successful = invoice.create()
    if successful:
        subscription.paydunya_token = invoice.token
        subscription.save(update_fields=['paydunya_token'])
        return invoice.response_text, None
    else:
        subscription.status = 'cancelled'
        subscription.save(update_fields=['status'])
        logger.error(f'PayDunya SaaS invoice failed: {invoice.response_text}')
        return None, 'Erreur lors de la creation du paiement.'


def activate_subscription(subscription):
    """Active un abonnement apres paiement reussi."""
    now = timezone.now()
    subscription.status = 'active'
    subscription.start_date = now
    subscription.end_date = now + timedelta(days=30)
    subscription.save()
    return subscription
