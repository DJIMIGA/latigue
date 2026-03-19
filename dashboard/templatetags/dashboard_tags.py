from django import template

register = template.Library()

@register.filter
def currency_xof(value):
    """Format a number as XOF currency."""
    try:
        return f"{int(value):,} FCFA".replace(",", " ")
    except (ValueError, TypeError):
        return "0 FCFA"
