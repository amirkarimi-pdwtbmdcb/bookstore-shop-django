from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from books.models import Book


class Cart(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='carts'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return f'Cart #{self.pk}'


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'book')

    def __str__(self):
        return f'{self.book.title} x{self.quantity}'