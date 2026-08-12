from django.core.exceptions import ValidationError
from django.db import transaction

from books.models import Book

from .models import Order, OrderItem, Coupon


@transaction.atomic
def create_order_from_cart(user, cart, shipping_info):
    if not cart.items.exists():
        raise ValidationError('سبد خرید خالیه')

    shipping_info = dict(shipping_info)
    coupon_code = shipping_info.pop('coupon_code', None)

    total_price = cart.total_price
    coupon = None
    discount_amount = 0

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            raise ValidationError('کد تخفیف نامعتبر است')

        if not coupon.is_valid():
            raise ValidationError('کد تخفیف منقضی شده یا دیگه معتبر نیست')

        discount_amount = total_price * coupon.discount_percent / 100
        total_price -= discount_amount

    order = Order.objects.create(
        user=user,
        total_price=total_price,
        coupon=coupon,
        discount_amount=discount_amount,
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

    if coupon:
        coupon.times_used += 1
        coupon.save()

    cart.items.all().delete()
    return order