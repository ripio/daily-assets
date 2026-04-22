from django import template

register = template.Library()


@register.filter
def fmt_usd(value):
    """Format as $1,234,567 — negatives in red via template class."""
    if value is None:
        return '—'
    try:
        v = float(value)
        if v < 0:
            return f'-${abs(v):,.0f}'
        return f'${v:,.0f}'
    except (TypeError, ValueError):
        return '—'


@register.filter
def fmt_num(value, arg=4):
    """Format number with thousand separators and N decimals."""
    if value is None:
        return '—'
    try:
        decimals = int(arg)
        return f'{float(value):,.{decimals}f}'
    except (TypeError, ValueError):
        return '—'


@register.filter
def fmt_var(value):
    """Format variation with leading + for positives."""
    if value is None:
        return '—'
    try:
        v = float(value)
        prefix = '+' if v >= 0 else ''
        return f'{prefix}${v:,.0f}'
    except (TypeError, ValueError):
        return '—'
