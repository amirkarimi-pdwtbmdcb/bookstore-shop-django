from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from books.models import Book

from .models import CartItem
from .utils import get_or_create_cart


def _parse_quantity(request, default=1):
    raw = request.POST.get('quantity', default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('book')
        return context


@require_POST
def cart_add(request, book_id):
    book = get_object_or_404(Book, id=book_id, is_active=True)
    cart = get_or_create_cart(request)
    quantity = _parse_quantity(request, default=1)

    if quantity < 1:
        messages.error(request, 'تعداد وارد شده معتبر نیست.')
        return redirect('books:book_detail', slug=book.slug)

    item, created = CartItem.objects.get_or_create(
        cart=cart, book=book, defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = _parse_quantity(request, default=item.quantity)

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()

    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('cart:cart_detail')


@require_POST
def cart_clear(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return redirect('cart:cart_detail')