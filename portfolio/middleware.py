import os
import json
from django.conf import settings
from django.core.cache import cache


class CloudinaryUsageMiddleware:
    """
    Middleware pour surveiller l'usage Cloudinary et éviter de dépasser les limites
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_key = 'cloudinary_usage'
        self.monthly_limit = 25  # Uploads par mois
        self.api_limit = 500     # Appels API par mois
    
    def __call__(self, request):
        # Vérifier l'usage avant chaque requête
        self.check_usage_limits()
        
        response = self.get_response(request)
        return response
    
    def check_usage_limits(self):
        """
        Vérifie les limites d'usage Cloudinary
        """
        usage = self.get_current_usage()
        
        # Afficher un avertissement si on approche des limites
        if usage['uploads'] >= self.monthly_limit * 0.8:  # 80% de la limite
            print(f"⚠️ ATTENTION: {usage['uploads']}/{self.monthly_limit} uploads Cloudinary utilisés ce mois")
        
        if usage['api_calls'] >= self.api_limit * 0.8:  # 80% de la limite
            print(f"⚠️ ATTENTION: {usage['api_calls']}/{self.api_limit} appels API Cloudinary utilisés ce mois")
    
    def get_current_usage(self):
        """
        Récupère l'usage actuel depuis le cache
        """
        usage = cache.get(self.cache_key)
        
        if not usage:
            # Créer un nouveau mois
            usage = {
                'uploads': 0,
                'api_calls': 0,
                'month': self.get_current_month()
            }
            cache.set(self.cache_key, usage, 60 * 60 * 24 * 31)  # 31 jours
        
        # Vérifier si on est dans un nouveau mois
        current_month = self.get_current_month()
        if usage.get('month') != current_month:
            usage = {
                'uploads': 0,
                'api_calls': 0,
                'month': current_month
            }
            cache.set(self.cache_key, usage, 60 * 60 * 24 * 31)
        
        return usage
    
    def increment_upload_count(self):
        """
        Incrémente le compteur d'uploads
        """
        usage = self.get_current_usage()
        usage['uploads'] += 1
        cache.set(self.cache_key, usage, 60 * 60 * 24 * 31)
    
    def increment_api_count(self):
        """
        Incrémente le compteur d'appels API
        """
        usage = self.get_current_usage()
        usage['api_calls'] += 1
        cache.set(self.cache_key, usage, 60 * 60 * 24 * 31)
    
    def get_current_month(self):
        """
        Retourne le mois actuel au format YYYY-MM
        """
        from datetime import datetime
        return datetime.now().strftime('%Y-%m')
    
    def can_upload(self):
        """
        Vérifie si on peut encore uploader
        """
        usage = self.get_current_usage()
        return usage['uploads'] < self.monthly_limit
    
    def can_make_api_call(self):
        """
        Vérifie si on peut encore faire des appels API
        """
        usage = self.get_current_usage()
        return usage['api_calls'] < self.api_limit 