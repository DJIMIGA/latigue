import json
import time
import logging
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)


class OpenClawClient:
    """Client HTTP pour le gateway OpenClaw (API compatible OpenAI)."""

    def __init__(self):
        self.base_url = settings.OPENCLAW_GATEWAY_URL.rstrip('/')
        self.token = settings.OPENCLAW_GATEWAY_TOKEN

    def _headers(self, agent_id=None):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }
        if agent_id:
            headers['x-openclaw-agent-id'] = agent_id
        return headers

    def health_check(self):
        """GET /__clawdbot__/health -- True si le gateway est actif."""
        url = f'{self.base_url}/__clawdbot__/health'
        req = urllib.request.Request(url, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f'OpenClaw health check failed: {e}')
            return False

    def chat(self, agent_id, messages, max_tokens=1024):
        """
        POST /v1/chat/completions
        Returns (response_text, usage_dict, response_time_ms).
        """
        url = f'{self.base_url}/v1/chat/completions'

        payload = json.dumps({
            'model': f'openclaw:{agent_id}',
            'messages': messages,
            'max_tokens': max_tokens,
        }).encode('utf-8')

        headers = self._headers(agent_id)
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                elapsed_ms = int((time.time() - start) * 1000)

                choices = data.get('choices', [])
                usage = data.get('usage', {})

                text = None
                if choices:
                    msg = choices[0].get('message', {})
                    text = msg.get('content')

                return text, usage, elapsed_ms

        except urllib.error.HTTPError as e:
            body = ''
            if e.fp:
                try:
                    body = e.read().decode('utf-8')[:300]
                except Exception:
                    pass
            logger.error(f'OpenClaw chat error {e.code}: {body}')
            return None, {}, int((time.time() - start) * 1000)

        except Exception as e:
            logger.error(f'OpenClaw chat exception: {e}')
            return None, {}, int((time.time() - start) * 1000)
