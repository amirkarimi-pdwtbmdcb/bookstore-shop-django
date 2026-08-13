from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from datetime import timedelta

from books.models import Book, Category
from cart.models import Cart, CartItem
from orders.models import Coupon, Order, OrderItem
from orders.services import create_order_from_cart

User = get_user_model()


def make_coupon(**overrides):
    now = timezone.now()
    defaults = {
        'code': 'SAVE10',
        'discount_percent': 10,
        'valid_from': now - timedelta(days=1),
        'valid_to': now + timedelta(days=1),
        'usage_limit': 5,
        'times_used': 0,
        'is_active': True,
    }
    defaults.update(overrides)
    return Coupon.objects.create(**defaults)


class CouponIsValidTests(TestCase):
    def test_active_coupon_within_date_range_and_under_limit_is_valid(self):
        coupon = make_coupon()
        self.assertTrue(coupon.is_valid())

    def test_inactive_coupon_is_invalid(self):
        coupon = make_coupon(is_active=False)
        self.assertFalse(coupon.is_valid())

    def test_not_yet_started_coupon_is_invalid(self):
        now = timezone.now()
        coupon = make_coupon(valid_from=now + timedelta(days=1), valid_to=now + timedelta(days=5))
        self.assertFalse(coupon.is_valid())

    def test_expired_coupon_is_invalid(self):
        now = timezone.now()
        coupon = make_coupon(valid_from=now - timedelta(days=5), valid_to=now - timedelta(days=1))
        self.assertFalse(coupon.is_valid())

    def test_fully_used_coupon_is_invalid(self):
        coupon = make_coupon(usage_limit=3, times_used=3)
        self.assertFalse(coupon.is_valid())


def base_shipping_info(**overrides):
    info = {
        'full_name': 'سارا احمدی',
        'phone_number': '09120000001',
        'province': 'تهران',
        'city': 'تهران',
        'postal_code': '1234567890',
        'address': 'خیابان آزادی',
        'order_notes': '',
        'coupon_code': '',
    }
    info.update(overrides)
    return info


class CreateOrderFromCartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='داستان', slug='fiction')
        self.physical_book = Book.objects.create(
            title='کتاب فیزیکی', slug='physical-book', category=self.category,
            price=100000, stock=5, book_type=Book.BookType.PHYSICAL,
        )
        self.digital_book = Book.objects.create(
            title='کتاب دیجیتال', slug='digital-book', category=self.category,
            price=50000, stock=0, book_type=Book.BookType.DIGITAL,
        )
        self.user = User.objects.create_user(username='sara', password='p', phone_number='09120000001')
        self.cart = Cart.objects.create(user=self.user)

    def test_empty_cart_raises_and_creates_nothing(self):
        with self.assertRaises(ValidationError):
            create_order_from_cart(self.user, self.cart, base_shipping_info())
        self.assertEqual(Order.objects.count(), 0)

    def test_successful_order_creates_order_and_items(self):
        CartItem.objects.create(cart=self.cart, book=self.physical_book, quantity=2)
        CartItem.objects.create(cart=self.cart, book=self.digital_book, quantity=1)

        order = create_order_from_cart(self.user, self.cart, base_shipping_info())

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, 100000 * 2 + 50000)
        self.assertEqual(order.items.count(), 2)

        physical_item = order.items.get(book=self.physical_book)
        self.assertEqual(physical_item.quantity, 2)
        # price on the OrderItem is a snapshot of the book price at purchase time
        self.assertEqual(physical_item.price, 100000)

    def test_physical_book_stock_is_decremented(self):
        CartItem.objects.create(cart=self.cart, book=self.physical_book, quantity=2)
        create_order_from_cart(self.user, self.cart, base_shipping_info())

        self.physical_book.refresh_from_db()
        self.assertEqual(self.physical_book.stock, 3)  # 5 - 2

    def test_digital_book_stock_is_untouched(self):
        CartItem.objects.create(cart=self.cart, book=self.digital_book, quantity=1)
        create_order_from_cart(self.user, self.cart, base_shipping_info())

        self.digital_book.refresh_from_db()
        self.assertEqual(self.digital_book.stock, 0)

    def test_cart_is_emptied_after_successful_order(self):
        CartItem.objects.create(cart=self.cart, book=self.physical_book, quantity=1)
        create_order_from_cart(self.user, self.cart, base_shipping_info())
        self.assertEqual(self.cart.items.count(), 0)

    def test_insufficient_stock_raises_and_rolls_everything_back(self):
        low_stock_book = Book.objects.create(
            title='کتاب کمیاب', slug='rare-book', category=self.category,
            price=200000, stock=1, book_type=Book.BookType.PHYSICAL,
        )
        CartItem.objects.create(cart=self.cart, book=self.physical_book, quantity=1)
        CartItem.objects.create(cart=self.cart, book=low_stock_book, quantity=5)

        with self.assertRaises(ValidationError):
            create_order_from_cart(self.user, self.cart, base_shipping_info())

        # nothing should have been persisted — not the order, not any item,
        # and the first book's stock should NOT have been decremented either
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.physical_book.refresh_from_db()
        self.assertEqual(self.physical_book.stock, 5)
        # and the cart should still have both items — nothing was cleared
        self.assertEqual(self.cart.items.count(), 2)


class CreateOrderFromCartWithCouponTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(
            title='کتاب', slug='book', category=self.category,
            price=200000, stock=10, book_type=Book.BookType.PHYSICAL,
        )
        self.user = User.objects.create_user(username='sara', password='p', phone_number='09120000001')
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, book=self.book, quantity=1)

        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code='SAVE10', discount_percent=10,
            valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=1),
            usage_limit=5, times_used=0, is_active=True,
        )

    def test_valid_coupon_reduces_total_price(self):
        order = create_order_from_cart(self.user, self.cart, base_shipping_info(coupon_code='SAVE10'))
        # 200000 - 10% = 180000
        self.assertEqual(order.total_price, 180000)
        self.assertEqual(order.discount_amount, 20000)
        self.assertEqual(order.coupon, self.coupon)

    def test_valid_coupon_increments_times_used(self):
        create_order_from_cart(self.user, self.cart, base_shipping_info(coupon_code='SAVE10'))
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 1)

    def test_unknown_coupon_code_raises_and_creates_nothing(self):
        with self.assertRaises(ValidationError):
            create_order_from_cart(self.user, self.cart, base_shipping_info(coupon_code='NOPE'))
        self.assertEqual(Order.objects.count(), 0)

    def test_expired_coupon_raises_and_does_not_increment_usage(self):
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.save()

        with self.assertRaises(ValidationError):
            create_order_from_cart(self.user, self.cart, base_shipping_info(coupon_code='SAVE10'))

        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 0)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_without_coupon_code_has_no_discount(self):
        order = create_order_from_cart(self.user, self.cart, base_shipping_info())
        self.assertEqual(order.discount_amount, 0)
        self.assertIsNone(order.coupon)


class CheckoutViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(
            title='کتاب', slug='book', category=category, price=100000, stock=5,
        )
        self.user = User.objects.create_user(username='sara', password='p', phone_number='09120000001')
        self.client.force_login(self.user)

    def test_checkout_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('orders:checkout'))
        self.assertNotEqual(response.status_code, 200)

    def test_empty_cart_redirects_to_cart_page(self):
        response = self.client.get(reverse('orders:checkout'))
        self.assertRedirects(response, reverse('cart:cart_detail'))

    def test_successful_checkout_creates_order_and_redirects_to_it(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=1)

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'سارا احمدی',
            'phone_number': '09120000001',
            'province': 'تهران',
            'city': 'تهران',
            'postal_code': '1234567890',
            'address': 'خیابان آزادی',
            'order_notes': '',
            'coupon_code': '',
        })

        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'pk': order.pk}))

    def test_insufficient_stock_shows_form_error_without_crashing(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=100)  # more than the 5 in stock

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'سارا احمدی',
            'phone_number': '09120000001',
            'province': 'تهران',
            'city': 'تهران',
            'postal_code': '1234567890',
            'address': 'خیابان آزادی',
            'order_notes': '',
            'coupon_code': '',
        })

        self.assertEqual(response.status_code, 200)  # re-renders the form, no crash
        self.assertFalse(Order.objects.filter(user=self.user).exists())


class OrderListDetailSecurityTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)
        self.owner = User.objects.create_user(username='owner', password='p', phone_number='09120000001')
        self.intruder = User.objects.create_user(username='intruder', password='p', phone_number='09120000002')
        self.order = Order.objects.create(
            user=self.owner, total_price=100000, full_name='سارا', phone_number='09120000001',
        )

    def test_order_list_requires_login(self):
        response = self.client.get(reverse('orders:order_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_order_list_only_shows_own_orders(self):
        self.client.force_login(self.intruder)
        response = self.client.get(reverse('orders:order_list'))
        self.assertNotIn(self.order, list(response.context['orders']))

    def test_cannot_view_another_users_order_detail(self):
        self.client.force_login(self.intruder)
        response = self.client.get(reverse('orders:order_detail', kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_their_own_order_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('orders:order_detail', kwargs={'pk': self.order.pk}))
        self.assertEqual(response.status_code, 200)
