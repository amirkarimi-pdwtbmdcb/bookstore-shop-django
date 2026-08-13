from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from books.models import Book, Category, Review, WishList
from orders.models import Order

User = get_user_model()


class UserDashboardViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)
        self.user = User.objects.create_user(username='sara', password='p', phone_number='09120000001')
        self.other_user = User.objects.create_user(username='ali', password='p', phone_number='09120000002')

    def test_requires_login(self):
        response = self.client.get(reverse('dashboard:user_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_only_shows_own_data(self):
        my_order = Order.objects.create(
            user=self.user, total_price=100000, full_name='سارا', phone_number='09120000001',
        )
        other_order = Order.objects.create(
            user=self.other_user, total_price=50000, full_name='علی', phone_number='09120000002',
        )
        WishList.objects.create(user=self.user, book=self.book)
        Review.objects.create(user=self.other_user, book=self.book, comment='خوب', rating=4)

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:user_dashboard'))

        self.assertIn(my_order, list(response.context['recent_orders']))
        self.assertNotIn(other_order, list(response.context['recent_orders']))
        self.assertEqual(response.context['wishlist_items'].count(), 1)
        self.assertEqual(response.context['reviews'].count(), 0)


class AdminDashboardViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)
        self.staff_user = User.objects.create_user(
            username='admin', password='p', phone_number='09120000001', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='sara', password='p', phone_number='09120000002',
        )

    def test_anonymous_user_cannot_access(self):
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_access(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_access(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_total_sales_only_counts_paid_orders(self):
        Order.objects.create(
            user=self.regular_user, total_price=100000, payment_status=Order.PaymentStatus.PAID,
            full_name='سارا', phone_number='09120000002',
        )
        Order.objects.create(
            user=self.regular_user, total_price=50000, payment_status=Order.PaymentStatus.UNPAID,
            full_name='سارا', phone_number='09120000002',
        )

        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('dashboard:admin_dashboard'))

        self.assertEqual(response.context['total_sales'], 100000)
        self.assertEqual(response.context['total_orders'], 2)
