from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from books.models import Book


class Order(TimeStampedModel):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'درحال بررسی'
        PROCESSING = 'processing', 'درحال پردازش'
        SHIPPED = 'shipped', 'ارسال شده'
        DELIVERED = 'delivered', 'تحویل داده شده'
        CANCELLED = 'cancelled', 'لغو شده'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'پرداخت نشده'
        PAID = 'paid', 'پرداخت شده'
        FAILED = 'failed', 'ناموفق'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='User')

    status = models.CharField('Status', max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    payment_status = models.CharField('Payment Status', max_length=6, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    total_price = models.DecimalField('Total Price', max_digits=10, decimal_places=0)

    full_name = models.CharField('Full Name', max_length=200)
    phone_number = models.CharField('Phone Number', max_length=15)
    province = models.CharField('Province', max_length=50, null=True, blank=True) 
    city = models.CharField('City', max_length=50, null=True, blank=True) 
    postal_code = models.CharField('Postal Code', max_length=10, null=True, blank=True)
    address = models.CharField('Address', max_length=700, null=True, blank=True)

    order_notes = models.CharField('Order Notes', max_length=700,null=True, blank=True)

    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"OrderItem {self.id} of order {self.order.id}"


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField()
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_to
            and self.times_used < self.usage_limit
        )