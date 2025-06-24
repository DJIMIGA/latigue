from django import template
from django.utils import timezone
from datetime import datetime
import locale
import html

register = template.Library()

@register.filter
def french_date(value):
    """
    Formate une date en français avec le format "15 janvier 2024"
    """
    if not value:
        return ""
    
    # Définir la locale française
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'French_France.1252')
        except:
            # Fallback si la locale française n'est pas disponible
            return value.strftime("%d %B %Y")
    
    # Mois en français
    mois_fr = {
        1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
        5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
        9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
    }
    
    jour = value.day
    mois = mois_fr[value.month]
    annee = value.year
    
    return f"{jour} {mois} {annee}"

@register.filter
def french_datetime(value):
    """
    Formate une date et heure en français avec le format "15 janvier 2024 à 14h30"
    """
    if not value:
        return ""
    
    date_fr = french_date(value)
    heure = value.strftime("%Hh%M")
    
    return f"{date_fr} à {heure}"

@register.filter
def relative_time(value):
    """
    Affiche le temps relatif en français (il y a 2 jours, aujourd'hui, etc.)
    """
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    if diff.days == 0:
        if diff.seconds < 3600:  # moins d'une heure
            minutes = diff.seconds // 60
            if minutes < 1:
                return "à l'instant"
            elif minutes == 1:
                return "il y a 1 minute"
            else:
                return f"il y a {minutes} minutes"
        else:  # moins d'un jour
            hours = diff.seconds // 3600
            if hours == 1:
                return "il y a 1 heure"
            else:
                return f"il y a {hours} heures"
    elif diff.days == 1:
        return "hier"
    elif diff.days < 7:
        return f"il y a {diff.days} jours"
    elif diff.days < 30:
        weeks = diff.days // 7
        if weeks == 1:
            return "il y a 1 semaine"
        else:
            return f"il y a {weeks} semaines"
    elif diff.days < 365:
        months = diff.days // 30
        if months == 1:
            return "il y a 1 mois"
        else:
            return f"il y a {months} mois"
    else:
        years = diff.days // 365
        if years == 1:
            return "il y a 1 an"
        else:
            return f"il y a {years} ans"

@register.filter
def smart_date(value):
    """
    Affiche une date intelligente : relative si récente, absolue sinon
    """
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    # Si moins de 7 jours, afficher le temps relatif
    if diff.days < 7:
        return relative_time(value)
    else:
        return french_date(value)

@register.filter
def clean_html_content(value):
    """
    Nettoie le contenu HTML en décodant les entités HTML et en supprimant les balises
    """
    if not value:
        return ""
    
    # Décoder les entités HTML
    decoded = html.unescape(value)
    
    # Supprimer les balises HTML
    import re
    clean_text = re.sub(r'<[^>]+>', '', decoded)
    
    # Nettoyer les espaces multiples
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    return clean_text.strip()

@register.filter
def safe_excerpt(value, word_count=25):
    """
    Crée un extrait sécurisé du contenu en décodant les entités HTML
    """
    if not value:
        return ""
    
    # Décoder les entités HTML
    decoded = html.unescape(value)
    
    # Supprimer les balises HTML
    import re
    clean_text = re.sub(r'<[^>]+>', '', decoded)
    
    # Nettoyer les espaces multiples
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Tronquer aux mots demandés
    words = clean_text.split()
    if len(words) <= word_count:
        return clean_text.strip()
    else:
        return ' '.join(words[:word_count]) + '...' 