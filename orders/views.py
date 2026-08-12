from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from cart.utils import get_or_create_cart

from .services import create_order_from_cart
from .forms import CheckoutForm
from .models import Order


class CheckoutView(LoginRequiredMixin, generic.FormView):
    template_name = 'orders/checkout.html'
    form_class = CheckoutForm

    def get(self, request, *args, **kwargs):
        cart = get_or_create_cart(request)
        if not cart.items.exists():
            return redirect('cart:cart_detail')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('book')
        return context

    def form_valid(self, form):
        cart = get_or_create_cart(self.request)
        try:
            self.order = create_order_from_cart(
                user=self.request.user,
                cart=cart,
                shipping_info=form.cleaned_data,
            )
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.order.pk})


class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    context_object_name = 'orders'
    template_name = 'orders/order_list.html'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'orders/order_detail.html'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)