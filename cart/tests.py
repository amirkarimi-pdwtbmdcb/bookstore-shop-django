from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from books.models import Book, Category
from cart.models import Cart, CartItem

User = get_user_model()


class CartModelTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book1 = Book.objects.create(title='کتاب ۱', slug='book-1', category=category, price=100000)
        self.book2 = Book.objects.create(title='کتاب ۲', slug='book-2', category=category, price=50000)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')
        self.cart = Cart.objects.create(user=self.user)

    def test_empty_cart_totals_are_zero(self):
        self.assertEqual(self.cart.total_price, 0)
        self.assertEqual(self.cart.total_items, 0)

    def test_total_price_sums_book_price_times_quantity(self):
        CartItem.objects.create(cart=self.cart, book=self.book1, quantity=2)
        CartItem.objects.create(cart=self.cart, book=self.book2, quantity=1)
        # 100000*2 + 50000*1 = 250000
        self.assertEqual(self.cart.total_price, 250000)

    def test_total_items_sums_quantities(self):
        CartItem.objects.create(cart=self.cart, book=self.book1, quantity=2)
        CartItem.objects.create(cart=self.cart, book=self.book2, quantity=3)
        self.assertEqual(self.cart.total_items, 5)


class MergeCartOnLoginTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book1 = Book.objects.create(title='کتاب ۱', slug='book-1', category=category, price=100000)
        self.book2 = Book.objects.create(title='کتاب ۲', slug='book-2', category=category, price=50000)
        self.user = User.objects.create_user(
            username='sara', password='a-strong-pass-1', phone_number='09120000001'
        )

    def _add_to_guest_cart(self, book, quantity):
        self.client.post(reverse('cart:cart_add', kwargs={'book_id': book.id}), {'quantity': quantity})

    def _login(self):
        return self.client.post(reverse('accounts:login'), {
            'username': 'sara', 'password': 'a-strong-pass-1',
        })

    def test_guest_cart_becomes_users_cart_when_user_has_none(self):
        self._add_to_guest_cart(self.book1, 2)
        guest_cart = Cart.objects.get(user__isnull=True)

        self._login()

        guest_cart.refresh_from_db()
        self.assertEqual(guest_cart.user, self.user)
        self.assertIsNone(guest_cart.session_key)
        self.assertEqual(guest_cart.items.get(book=self.book1).quantity, 2)

    def test_guest_cart_merges_into_existing_user_cart(self):
        # user already has a cart with book1 x1 from a previous session
        existing_cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=existing_cart, book=self.book1, quantity=1)

        # as a guest (different session), they add book1 again plus book2
        self._add_to_guest_cart(self.book1, 2)
        self._add_to_guest_cart(self.book2, 1)

        self._login()

        existing_cart.refresh_from_db()
        # book1 quantities should be summed: 1 (existing) + 2 (guest) = 3
        self.assertEqual(existing_cart.items.get(book=self.book1).quantity, 3)
        # book2 should simply be added since it wasn't in the user's cart
        self.assertEqual(existing_cart.items.get(book=self.book2).quantity, 1)

        # the now-empty guest cart should have been deleted
        self.assertFalse(Cart.objects.filter(user__isnull=True).exists())


class CartAddViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)

    def test_anonymous_user_can_add_to_cart(self):
        response = self.client.post(
            reverse('cart:cart_add', kwargs={'book_id': self.book.id}), {'quantity': 2}
        )
        self.assertRedirects(response, reverse('cart:cart_detail'))
        cart = Cart.objects.get(user__isnull=True)
        self.assertEqual(cart.items.get(book=self.book).quantity, 2)

    def test_adding_same_book_again_increments_quantity(self):
        url = reverse('cart:cart_add', kwargs={'book_id': self.book.id})
        self.client.post(url, {'quantity': 2})
        self.client.post(url, {'quantity': 3})

        cart = Cart.objects.get(user__isnull=True)
        self.assertEqual(cart.items.get(book=self.book).quantity, 5)

    def test_cannot_add_inactive_book(self):
        self.book.is_active = False
        self.book.save()
        response = self.client.post(
            reverse('cart:cart_add', kwargs={'book_id': self.book.id}), {'quantity': 1}
        )
        self.assertEqual(response.status_code, 404)


class CartUpdateRemoveTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, book=self.book, quantity=2)
        self.client.force_login(self.user)

    def test_update_quantity(self):
        self.client.post(reverse('cart:cart_update', kwargs={'item_id': self.item.id}), {'quantity': 5})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 5)

    def test_update_to_zero_deletes_item(self):
        self.client.post(reverse('cart:cart_update', kwargs={'item_id': self.item.id}), {'quantity': 0})
        self.assertFalse(CartItem.objects.filter(id=self.item.id).exists())

    def test_remove_item(self):
        self.client.post(reverse('cart:cart_remove', kwargs={'item_id': self.item.id}))
        self.assertFalse(CartItem.objects.filter(id=self.item.id).exists())

    def test_clear_cart(self):
        self.client.post(reverse('cart:cart_clear'))
        self.assertEqual(self.cart.items.count(), 0)

    def test_cannot_update_another_users_cart_item(self):
        other_user = User.objects.create_user(username='u2', password='p', phone_number='09120000012')
        self.client.force_login(other_user)
        response = self.client.post(
            reverse('cart:cart_update', kwargs={'item_id': self.item.id}), {'quantity': 9}
        )
        self.assertEqual(response.status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)


class CartDetailViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = Book.objects.create(title='کتاب', slug='book', category=category, price=100000)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')

    def test_page_loads_for_anonymous_user(self):
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_page_loads_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)
