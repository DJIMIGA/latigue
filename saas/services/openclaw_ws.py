"""
Client WebSocket pour le gateway OpenClaw.

Utilise le protocole JSON-RPC du gateway pour :
- web.login.start : genere un QR code WhatsApp (base64 PNG)
- web.login.wait  : attend le scan du QR code

Auth simplifiee par token (sans device signature) — confirmee
par le code source du gateway (sharedAuthOk bypass).
"""
import asyncio
import json
import logging
import uuid

import websockets

from django.conf import settings

logger = logging.getLogger(__name__)

# Timeout pour la connexion WebSocket initiale
CONNECT_TIMEOUT = 10
# Timeout pour recevoir la reponse a une requete
REQUEST_TIMEOUT = 15
# Timeout pour web.login.wait (le QR doit etre scanne)
WAIT_SCAN_TIMEOUT = 90


def _ws_url():
    """Convertit l'URL HTTP du gateway en URL WebSocket."""
    url = settings.OPENCLAW_GATEWAY_URL.rstrip('/')
    return url.replace('http://', 'ws://').replace('https://', 'wss://')


def _make_req(method, params=None):
    """Construit un message JSON-RPC pour le gateway."""
    return json.dumps({
        'type': 'req',
        'id': str(uuid.uuid4()),
        'method': method,
        'params': params or {},
    })


async def _connect_and_auth(ws):
    """Attend le challenge et envoie la reponse d'auth (token only)."""
    # 1. Recevoir connect.challenge
    raw = await asyncio.wait_for(ws.recv(), timeout=CONNECT_TIMEOUT)
    msg = json.loads(raw)

    if msg.get('type') != 'event' or msg.get('event') != 'connect.challenge':
        raise RuntimeError(f"Expected connect.challenge, got: {msg.get('type')}:{msg.get('event')}")

    # 2. Envoyer connect avec token (pas de device — sharedAuth bypass)
    connect_req = {
        'type': 'req',
        'id': str(uuid.uuid4()),
        'method': 'connect',
        'params': {
            'minProtocol': 3,
            'maxProtocol': 3,
            'client': {
                'id': 'gateway-client',
                'version': '1.0.0',
                'platform': 'linux',
                'mode': 'backend',
            },
            'auth': {
                'token': settings.OPENCLAW_GATEWAY_TOKEN,
            },
        },
    }
    await ws.send(json.dumps(connect_req))

    # 3. Recevoir hello-ok
    raw = await asyncio.wait_for(ws.recv(), timeout=CONNECT_TIMEOUT)
    res = json.loads(raw)

    if res.get('type') != 'res' or not res.get('ok'):
        error = res.get('error', {})
        raise RuntimeError(f"Auth failed: {error.get('message', res)}")

    logger.debug('OpenClaw WS authenticated')
    return res


async def _call_method(ws, method, params, timeout):
    """Envoie une requete et attend la reponse correspondante."""
    req_id = str(uuid.uuid4())
    msg = {
        'type': 'req',
        'id': req_id,
        'method': method,
        'params': params,
    }
    await ws.send(json.dumps(msg))

    # Attendre la reponse avec le bon id (ignorer les events)
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"Timeout waiting for {method} response")
        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
        data = json.loads(raw)
        if data.get('type') == 'res' and data.get('id') == req_id:
            return data
        # Sinon c'est un event ou une autre reponse — on l'ignore


async def _start_login(account_id):
    """Ouvre WS, s'authentifie, appelle web.login.start, retourne le QR."""
    async with websockets.connect(_ws_url()) as ws:
        await _connect_and_auth(ws)
        res = await _call_method(ws, 'web.login.start', {
            'accountId': account_id,
            'timeoutMs': 30000,
            'force': False,
        }, timeout=REQUEST_TIMEOUT)

    if not res.get('ok'):
        error = res.get('error', {})
        raise RuntimeError(error.get('message', 'web.login.start failed'))

    payload = res.get('payload', {})
    return payload.get('qrDataUrl', '')


async def _wait_login(account_id):
    """Ouvre WS, s'authentifie, appelle web.login.wait, retourne le statut."""
    async with websockets.connect(_ws_url()) as ws:
        await _connect_and_auth(ws)
        res = await _call_method(ws, 'web.login.wait', {
            'accountId': account_id,
            'timeoutMs': WAIT_SCAN_TIMEOUT * 1000,
        }, timeout=WAIT_SCAN_TIMEOUT + 10)

    if not res.get('ok'):
        error = res.get('error', {})
        raise RuntimeError(error.get('message', 'web.login.wait failed'))

    payload = res.get('payload', {})
    return payload.get('connected', False)


# ─── API synchrone (pour les views Django) ─────────────────

def start_whatsapp_login(account_id):
    """
    Lance le login WhatsApp pour un compte.
    Retourne le QR code en data URL (data:image/png;base64,...).
    Leve une exception en cas d'erreur.
    """
    return asyncio.run(_start_login(account_id))


def wait_whatsapp_login(account_id):
    """
    Attend que le QR soit scanne.
    Retourne True si connecte, False si timeout.
    Leve une exception en cas d'erreur.
    """
    return asyncio.run(_wait_login(account_id))
