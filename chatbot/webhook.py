import hashlib
import hmac
import json
import os
import subprocess

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')


def verify_signature(payload_body, signature_header):
    """Vérifie la signature HMAC SHA-256 de GitHub."""
    if not WEBHOOK_SECRET:
        return False
    if not signature_header:
        return False

    expected = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


@csrf_exempt
@require_POST
def github_webhook(request):
    """Reçoit les webhooks GitHub et déclenche le déploiement."""

    # Vérifier la signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if WEBHOOK_SECRET and not verify_signature(request.body, signature):
        return HttpResponse('Signature invalide', status=403)

    # Parser le payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('JSON invalide', status=400)

    # Vérifier que c'est un push sur main
    ref = payload.get('ref', '')
    if ref != 'refs/heads/main':
        return JsonResponse({'status': 'ignoré', 'reason': f'branche {ref}'})

    # Lancer le déploiement en arrière-plan
    try:
        subprocess.Popen(
            ['/bin/bash', '/var/www/latigue/deploy.sh'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        return JsonResponse({'status': 'erreur', 'detail': str(e)}, status=500)

    pusher = payload.get('pusher', {}).get('name', 'inconnu')
    commits = len(payload.get('commits', []))

    return JsonResponse({
        'status': 'déploiement lancé',
        'pusher': pusher,
        'commits': commits,
    })
