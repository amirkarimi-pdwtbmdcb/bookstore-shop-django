from .utils import get_or_create_cart


def cart(request):
    return {'nav_cart': get_or_create_cart(request)}
