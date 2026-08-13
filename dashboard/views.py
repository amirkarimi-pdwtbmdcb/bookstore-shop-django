from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.db.models import Sum

from orders.models import Order
from books.models import Review, WishList, Book


User = get_user_model()

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/user_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['recent_orders'] = Order.objects.filter(user=user).order_by('-created_at')[:5]
        context['wishlist_items'] = WishList.objects.filter(user=user).select_related('book')
        context['reviews'] = Review.objects.filter(user=user).select_related('book')

        return context


class AdminDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_orders'] = Order.objects.count()
        context['total_users'] = User.objects.count()

        sales = Order.objects.filter(
            payment_status=Order.PaymentStatus.PAID
        ).aggregate(total_sales=Sum('total_price'))
        context['total_sales'] = sales['total_sales'] or 0

        context['top_books'] = Book.objects.annotate(
            total_sold=Sum('order_items__quantity')
        ).order_by('-total_sold')[:10]

        context['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:10]

        return context
