from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from books.models import Book

from .models import CartItem
from .utils import get_or_create_cart


class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = get_or_create_cart(self.request)
        return context


def cart_add(request, book_id):
    book = get_object_or_404(Book, id=book_id, is_active=True)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    item, created = CartItem.objects.get_or_create(
        cart=cart, book=book, defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    return redirect('cart:cart_detail')


def cart_update(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()

    return redirect('cart:cart_detail')


def cart_remove(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('cart:cart_detail')


def cart_clear(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return redirect('cart:cart_detail')