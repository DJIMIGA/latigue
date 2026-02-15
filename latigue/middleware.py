"""
Middleware personnalisé pour le projet Latigue.
"""


class HealthCheckSSLExemptMiddleware:
    """
    Pour les requêtes vers /health/, simule X-Forwarded-Proto: https
    afin que le healthcheck Docker (curl HTTP depuis le conteneur) reçoive 200
    au lieu d'une 301 HTTPS (évite healthcheck en échec et 502).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.rstrip('/') == '/health':
            request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        return self.get_response(request)
