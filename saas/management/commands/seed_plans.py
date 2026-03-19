from django.core.management.base import BaseCommand
from saas.models import SaaSPlan


class Command(BaseCommand):
    help = 'Seed les 3 plans tarifaires SaaS'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'model_id': 'anthropic/claude-haiku-3-5-20241022',
                'max_concurrent': 2,
                'price_xof': 15000,
                'max_tokens_month': 200000,
                'features': 'Agent IA Haiku\n1 canal (WhatsApp ou Telegram)\nSupport email\n200K tokens/mois',
                'order': 1,
            },
            {
                'name': 'Business',
                'slug': 'business',
                'model_id': 'anthropic/claude-sonnet-4-5-20250929',
                'max_concurrent': 4,
                'price_xof': 50000,
                'max_tokens_month': 1000000,
                'features': 'Agent IA Sonnet 4.5\n2 canaux (WhatsApp + Telegram)\nSupport prioritaire\n1M tokens/mois\nTableau de bord usage',
                'order': 2,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'model_id': 'anthropic/claude-opus-4-6',
                'max_concurrent': 8,
                'price_xof': 150000,
                'max_tokens_month': 5000000,
                'features': 'Agent IA Opus 4.6\nTous les canaux\nSupport VIP\n5M tokens/mois\nTableau de bord avance\nAPI programmatique\nPersonnalisation avancee',
                'order': 3,
            },
        ]

        for plan_data in plans:
            plan, created = SaaSPlan.objects.update_or_create(
                slug=plan_data['slug'],
                defaults=plan_data,
            )
            action = 'Cree' if created else 'Mis a jour'
            self.stdout.write(self.style.SUCCESS(f'{action}: {plan.name} - {plan.price_xof} FCFA'))
