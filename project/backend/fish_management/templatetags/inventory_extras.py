from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Format a number as currency."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def percentage(value):
    """Format a number as percentage."""
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

@register.filter
def status_class(status):
    """Return CSS class for status."""
    status_classes = {
        'pending': 'warning',
        'approved': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'rejected': 'danger',
        'low-stock': 'warning',
        'in-stock': 'success',
        'out-of-stock': 'danger'
    }
    return status_classes.get(status, 'secondary')

@register.filter
def stock_status(item):
    """Determine stock status for an inventory item."""
    try:
        quantity = float(item.quantity)
        minimum = float(item.minimum_stock)
        
        if quantity == 0:
            return 'out-of-stock'
        elif quantity <= minimum:
            return 'low-stock'
        else:
            return 'in-stock'
    except (ValueError, TypeError, AttributeError):
        return 'unknown'

@register.filter
def format_quantity(quantity, unit):
    """Format quantity with unit."""
    try:
        if float(quantity) == int(float(quantity)):
            return f"{int(float(quantity))} {unit}"
        else:
            return f"{float(quantity):,.2f} {unit}"
    except (ValueError, TypeError):
        return f"0 {unit}"

@register.simple_tag
def calculate_efficiency(fed_quantity, mortality_count):
    """Calculate feed efficiency based on mortality."""
    try:
        fed = float(fed_quantity)
        mortality = int(mortality_count)
        
        if mortality == 0:
            return 100.0
        else:
            # Simple efficiency calculation: reduce by 5% per mortality
            efficiency = max(0, 100 - (mortality * 5))
            return efficiency
    except (ValueError, TypeError):
        return 0.0

@register.inclusion_tag('includes/stock_alert.html')
def stock_alert(item):
    """Render stock alert component."""
    return {
        'item': item,
        'is_low_stock': item.quantity <= item.minimum_stock,
        'is_out_of_stock': item.quantity == 0
    }
