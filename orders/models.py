from django.db import models
from django.conf import settings

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

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"OrderItem {self.id} of order {self.order.id}"