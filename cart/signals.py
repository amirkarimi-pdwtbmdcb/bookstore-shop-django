from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    cart_id = request.session.get('cart_id')

    if not cart_id:
        return

    try:
        guest_cart = Cart.objects.get(
            id=cart_id,
            user__isnull=True,
        )
    except Cart.DoesNotExist:
        return

    user_cart, created = Cart.objects.get_or_create(user=user)

    if created:
        guest_cart.user = user
        guest_cart.session_key = None
        guest_cart.save()
    else:
        for guest_item in guest_cart.items.all():
            user_item, item_created = user_cart.items.get_or_create(
                book=guest_item.book,
                defaults={'quantity': guest_item.quantity},
            )

            if not item_created:
                user_item.quantity += guest_item.quantity
                user_item.save()

        guest_cart.delete()

    request.session.pop('cart_id', None)
    session_key = request.session.session_key
    if not session_key:
        return

    try:
        guest_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
    except Cart.DoesNotExist:
        return

    user_cart, created = Cart.objects.get_or_create(user=user)

    if created:
        guest_cart.user = user
        guest_cart.session_key = None
        guest_cart.save()
    else:
        for guest_item in guest_cart.items.all():
            user_item, item_created = user_cart.items.get_or_create(
                book=guest_item.book,
                defaults={'quantity': guest_item.quantity}
            )
            if not item_created:
                user_item.quantity += guest_item.quantity
                user_item.save()
        guest_cart.delete()