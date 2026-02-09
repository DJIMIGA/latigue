import json
import os
import urllib.request
import urllib.error

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

SYSTEM_PROMPT = """Tu es Nour ✨, l'assistant IA du portfolio de Konimba Djimiga (bolibana.net).

Ton rôle :
- Répondre aux questions des visiteurs sur les services, formations, le blog et les compétences de Konimba
- Être sympathique, concis et chaleureux
- Parler français par défaut, mais t'adapter si le visiteur parle une autre langue

Konimba est développeur Python & Django basé à Tours, France. Il propose :
- Des services de développement web (Python, Django, APIs)
- Des formations Python et Django
- Des articles de blog sur le développement et les technologies
- Du contenu pédagogique (TikTok @djimiga1, YouTube @pythonmalien)

Sois concis (2-3 phrases max sauf si on te demande des détails). Si on te pose des questions hors sujet, ramène gentiment vers le portfolio."""


# Stockage simple des conversations en mémoire (reset au restart)
_conversations = {}
MAX_HISTORY = 10


@csrf_exempt
@require_POST
def chat_api(request):
    """API endpoint pour le chatbot Nour."""
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        session_id = body.get('session_id', 'anonymous')

        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        if len(message) > 1000:
            return JsonResponse({'error': 'Message trop long (max 1000 caractères)'}, status=400)

        if not ANTHROPIC_API_KEY:
            return JsonResponse({
                'response': "Je suis temporairement hors ligne. Contactez Konimba via WhatsApp ! 📱"
            })

        # Récupérer ou créer l'historique
        if session_id not in _conversations:
            _conversations[session_id] = []
        history = _conversations[session_id]

        # Ajouter le message utilisateur
        history.append({"role": "user", "content": message})

        # Garder seulement les N derniers messages
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
            _conversations[session_id] = history

        # Appeler l'API Anthropic
        response_text = _call_anthropic(history)

        # Ajouter la réponse à l'historique
        history.append({"role": "assistant", "content": response_text})

        return JsonResponse({
            'response': response_text,
            'session_id': session_id,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        print(f"[Chatbot] Erreur: {e}")
        return JsonResponse({
            'response': "Oups, une erreur est survenue. Réessayez ! 🙏",
        })


def _call_anthropic(messages):
    """Appelle l'API Anthropic Claude directement via urllib (pas de dépendance externe)."""
    url = "https://api.anthropic.com/v1/messages"

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 512,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }).encode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            # Extraire le texte de la réponse
            content = data.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return "..."
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        print(f"[Chatbot] API Anthropic error {e.code}: {error_body[:200]}")
        return "Désolé, je rencontre un problème technique. Réessayez dans un instant ! 🙏"
    except Exception as e:
        print(f"[Chatbot] Erreur appel API: {e}")
        return "Désolé, je suis temporairement indisponible. Contactez-nous via WhatsApp ! 📱"
