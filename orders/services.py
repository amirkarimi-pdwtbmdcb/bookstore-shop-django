from django.db import transaction
from django.core.exceptions import ValidationError

from books.models import Book

from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user, cart, shipping_info):
    if not cart.items.exists():
        raise ValidationError('سبد خرید خالیه')

    order = Order.objects.create(
        user=user,
        total_price=cart.total_price,
        **shipping_info,
    )

    for cart_item in cart.items.select_related('book'):
        book = cart_item.book

        if book.book_type == Book.PHYSICAL:
            if book.stock < cart_item.quantity:
                raise ValidationError(f'موجودی «{book.title}» کافی نیست')
            book.stock -= cart_item.quantity
            book.save()

        OrderItem.objects.create(
            order=order,
            book=book,
            quantity=cart_item.quantity,
            price=book.price,
        )

    cart.items.all().delete()
    return order