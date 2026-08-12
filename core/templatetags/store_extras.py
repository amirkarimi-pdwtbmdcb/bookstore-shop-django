from django import template

register = template.Library()


@register.filter(name='price')
def price(value):
    if value in (None, ''):
        return ''
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return value
    return f'{amount:,} تومان'


@register.filter
def in_wishlist(book, user):
    if not getattr(user, 'is_authenticated', False):
        return False
    return book.wishlisted_by.filter(user=user).exists()


@register.inclusion_tag('includes/star_rating.html')
def star_rating(value, max_stars=5):
    value = value or 0
    full = int(value)
    remainder = value - full
    half = 1 if remainder >= 0.5 else 0
    empty = max_stars - full - half
    return {
        'full_range': range(full),
        'half': half,
        'empty_range': range(empty),
        'value': value,
    }
