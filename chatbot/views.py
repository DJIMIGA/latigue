import json
import asyncio
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# WebSocket client pour communiquer avec le gateway OpenClaw
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


GATEWAY_URL = os.environ.get('OPENCLAW_GATEWAY_URL', 'ws://127.0.0.1:18789')
GATEWAY_TOKEN = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '')

# Contexte système pour Nour quand il parle aux visiteurs du portfolio
SYSTEM_CONTEXT = (
    "Tu es Nour ✨, l'assistant IA du portfolio de Konimba Djimiga (bolibana.net). "
    "Tu es sympathique, utile et tu parles français. "
    "Tu peux répondre aux questions sur les services, formations, le blog, "
    "et les compétences de Konimba (Python, Django, développement web). "
    "Sois concis et chaleureux. Si on te pose des questions hors sujet, "
    "ramène gentiment la conversation vers le portfolio."
)


async def _send_to_gateway(message: str, session_id: str) -> str:
    """Envoie un message au gateway OpenClaw via WebSocket et attend la réponse."""
    if not HAS_WEBSOCKETS:
        return "Le chat est temporairement indisponible. Contactez-nous via WhatsApp !"

    try:
        connect_params = {
            "auth": {"token": GATEWAY_TOKEN}
        }

        async with websockets.connect(
            GATEWAY_URL,
            additional_headers={},
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            # Handshake avec auth
            connect_msg = {
                "id": 1,
                "method": "connect",
                "params": connect_params,
            }
            await ws.send(json.dumps(connect_msg))
            
            # Attendre la réponse de connexion
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            connect_result = json.loads(response)
            
            if "error" in connect_result:
                return "Connexion échouée. Réessayez plus tard."

            # Envoyer le message
            chat_msg = {
                "id": 2,
                "method": "chat.send",
                "params": {
                    "message": message,
                    "sessionKey": f"visitor:{session_id}",
                },
            }
            await ws.send(json.dumps(chat_msg))

            # Collecter la réponse (streaming)
            full_response = ""
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(raw)
                    
                    # Réponse directe
                    if data.get("id") == 2 and "result" in data:
                        result = data["result"]
                        if isinstance(result, dict) and result.get("text"):
                            return result["text"]
                    
                    # Événements de streaming
                    if "method" in data and data["method"] == "chat":
                        params = data.get("params", {})
                        if params.get("type") == "text":
                            full_response += params.get("data", "")
                        elif params.get("type") == "done":
                            return full_response or "..."
                            
                except asyncio.TimeoutError:
                    return full_response or "Désolé, la réponse a pris trop de temps."

    except Exception as e:
        print(f"[Chatbot] Erreur gateway: {e}")
        return "Oups, je suis temporairement indisponible. Essayez via WhatsApp ! 📱"


@csrf_exempt
@require_POST
def chat_api(request):
    """API endpoint pour le chatbot."""
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        session_id = body.get('session_id', 'anonymous')

        if not message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        if len(message) > 1000:
            return JsonResponse({'error': 'Message trop long (max 1000 caractères)'}, status=400)

        # Envoyer au gateway OpenClaw
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response_text = loop.run_until_complete(_send_to_gateway(message, session_id))
        finally:
            loop.close()

        return JsonResponse({
            'response': response_text,
            'session_id': session_id,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        print(f"[Chatbot] Erreur: {e}")
        return JsonResponse({
            'response': "Désolé, une erreur est survenue. Réessayez ! 🙏",
        })
