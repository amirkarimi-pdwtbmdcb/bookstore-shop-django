from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from books.models import Author, Book, Category, Publisher, Review, WishList

User = get_user_model()


class CategoryModelTests(TestCase):
    def test_str_returns_name(self):
        category = Category.objects.create(name='رمان', slug='novel')
        self.assertEqual(str(category), 'رمان')


class BookModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='رمان', slug='novel')
        self.author = Author.objects.create(name='صادق هدایت', slug='sadegh-hedayat')
        self.book = Book.objects.create(
            title='بوف کور',
            slug='boof-kor',
            category=self.category,
            price=150000,
        )
        self.book.authors.add(self.author)

    def test_str_returns_title(self):
        self.assertEqual(str(self.book), 'بوف کور')

    def test_get_absolute_url(self):
        self.assertEqual(self.book.get_absolute_url(), f'/book/{self.book.slug}/')

    def test_default_book_type_is_physical(self):
        self.assertEqual(self.book.book_type, Book.BookType.PHYSICAL)

    def test_average_rating_with_no_reviews_is_zero(self):
        self.assertEqual(self.book.average_rating, 0)

    def test_average_rating_only_counts_approved_reviews(self):
        user1 = User.objects.create_user(username='u1', password='p', phone_number='09120000011')
        user2 = User.objects.create_user(username='u2', password='p', phone_number='09120000012')

        Review.objects.create(book=self.book, user=user1, comment='خوب بود', rating=5, is_approved=True)
        Review.objects.create(book=self.book, user=user2, comment='بد بود', rating=1, is_approved=False)

        # only the approved 5-star review should count
        self.assertEqual(self.book.average_rating, 5.0)


class ReviewModelTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='رمان', slug='novel')
        self.book = Book.objects.create(title='بوف کور', slug='boof-kor', category=category, price=150000)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')

    def test_one_review_per_user_per_book(self):
        Review.objects.create(book=self.book, user=self.user, comment='خوب بود', rating=5)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(book=self.book, user=self.user, comment='دوباره', rating=3)


class WishListModelTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='رمان', slug='novel')
        self.book = Book.objects.create(title='بوف کور', slug='boof-kor', category=category, price=150000)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')

    def test_one_wishlist_entry_per_user_per_book(self):
        WishList.objects.create(book=self.book, user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WishList.objects.create(book=self.book, user=self.user)


def make_book(category, **overrides):
    defaults = {
        'title': 'کتاب تست',
        'slug': 'test-book',
        'price': 100000,
        'is_active': True,
    }
    defaults.update(overrides)
    return Book.objects.create(category=category, **defaults)


class BookListViewTests(TestCase):
    def setUp(self):
        self.category_fiction = Category.objects.create(name='داستان', slug='fiction')
        self.category_history = Category.objects.create(name='تاریخ', slug='history')
        self.author = Author.objects.create(name='نویسنده تست', slug='test-author')
        self.publisher = Publisher.objects.create(name='ناشر تست', slug='test-publisher')

        self.cheap_book = make_book(
            self.category_fiction, title='کتاب ارزان', slug='cheap-book', price=50000,
        )
        self.cheap_book.authors.add(self.author)

        self.expensive_book = make_book(
            self.category_history, title='کتاب گران', slug='expensive-book', price=500000,
        )

        self.inactive_book = make_book(
            self.category_fiction, title='کتاب غیرفعال', slug='inactive-book',
            price=10000, is_active=False,
        )

    def test_only_active_books_are_listed(self):
        response = self.client.get(reverse('books:book_list'))
        books = list(response.context['books'])
        self.assertIn(self.cheap_book, books)
        self.assertIn(self.expensive_book, books)
        self.assertNotIn(self.inactive_book, books)

    def test_search_matches_title(self):
        response = self.client.get(reverse('books:book_list'), {'q': 'ارزان'})
        books = list(response.context['books'])
        self.assertEqual(books, [self.cheap_book])

    def test_filter_by_category(self):
        response = self.client.get(reverse('books:book_list'), {'category': 'history'})
        books = list(response.context['books'])
        self.assertEqual(books, [self.expensive_book])

    def test_filter_by_author(self):
        response = self.client.get(reverse('books:book_list'), {'author': 'test-author'})
        books = list(response.context['books'])
        self.assertEqual(books, [self.cheap_book])

    def test_filter_by_price_range(self):
        response = self.client.get(reverse('books:book_list'), {'min_price': 100000})
        books = list(response.context['books'])
        self.assertEqual(books, [self.expensive_book])

    def test_sort_by_price_ascending(self):
        response = self.client.get(reverse('books:book_list'), {'sort': 'price_asc'})
        books = list(response.context['books'])
        self.assertEqual(books, [self.cheap_book, self.expensive_book])

    def test_filter_context_includes_categories_authors_publishers(self):
        response = self.client.get(reverse('books:book_list'))
        self.assertIn(self.category_fiction, response.context['categories'])
        self.assertIn(self.author, response.context['authors'])
        self.assertIn(self.publisher, response.context['publishers'])


class BookDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='داستان', slug='fiction')
        self.book = make_book(self.category, title='کتاب فعال', slug='active-book')
        self.inactive_book = make_book(
            self.category, title='کتاب غیرفعال', slug='inactive-book', is_active=False,
        )

    def test_active_book_detail_is_visible(self):
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)

    def test_inactive_book_detail_returns_404(self):
        response = self.client.get(
            reverse('books:book_detail', kwargs={'slug': self.inactive_book.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_only_shows_approved_reviews(self):
        user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')
        approved = Review.objects.create(book=self.book, user=user, comment='خوب', rating=5, is_approved=True)
        response = self.client.get(reverse('books:book_detail', kwargs={'slug': self.book.slug}))
        self.assertIn(approved, response.context['reviews'])


class CategoryAuthorPublisherDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='داستان', slug='fiction')
        self.author = Author.objects.create(name='نویسنده تست', slug='test-author')
        self.publisher = Publisher.objects.create(name='ناشر تست', slug='test-publisher')
        self.book = make_book(self.category, publisher=self.publisher)
        self.book.authors.add(self.author)

    def test_category_detail_lists_its_books(self):
        response = self.client.get(reverse('books:category_detail', kwargs={'slug': self.category.slug}))
        self.assertIn(self.book, response.context['books'])

    def test_author_detail_lists_their_books(self):
        response = self.client.get(reverse('books:author_detail', kwargs={'slug': self.author.slug}))
        self.assertIn(self.book, response.context['books'])

    def test_publisher_detail_lists_their_books(self):
        response = self.client.get(reverse('books:publisher_detail', kwargs={'slug': self.publisher.slug}))
        self.assertIn(self.book, response.context['books'])


class ReviewCreateViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = make_book(category)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')

    def test_requires_login(self):
        response = self.client.post(
            reverse('books:comment_create', kwargs={'book_id': self.book.id}),
            {'rating': 5, 'comment': 'عالی بود'},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(book=self.book).exists())

    def test_logged_in_user_can_review(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('books:comment_create', kwargs={'book_id': self.book.id}),
            {'rating': 5, 'comment': 'عالی بود'},
        )
        review = Review.objects.get(book=self.book, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertRedirects(response, reverse('books:book_detail', kwargs={'slug': self.book.slug}))

    def test_cannot_review_same_book_twice(self):
        Review.objects.create(book=self.book, user=self.user, comment='اول', rating=4)
        self.client.force_login(self.user)
        self.client.post(
            reverse('books:comment_create', kwargs={'book_id': self.book.id}),
            {'rating': 2, 'comment': 'دوباره'},
        )
        self.assertEqual(Review.objects.filter(book=self.book, user=self.user).count(), 1)


class WishlistToggleTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = make_book(category)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')

    def test_requires_login(self):
        response = self.client.post(reverse('books:wishlist_toggle', kwargs={'book_id': self.book.id}))
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(WishList.objects.exists())

    def test_toggle_adds_then_removes(self):
        self.client.force_login(self.user)
        url = reverse('books:wishlist_toggle', kwargs={'book_id': self.book.id})

        self.client.post(url)
        self.assertTrue(WishList.objects.filter(user=self.user, book=self.book).exists())

        self.client.post(url)
        self.assertFalse(WishList.objects.filter(user=self.user, book=self.book).exists())


class WishlistListViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='داستان', slug='fiction')
        self.book = make_book(category)
        self.user = User.objects.create_user(username='u1', password='p', phone_number='09120000011')
        self.other_user = User.objects.create_user(username='u2', password='p', phone_number='09120000012')

    def test_requires_login(self):
        response = self.client.get(reverse('books:wishlist_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_only_shows_own_wishlist(self):
        WishList.objects.create(user=self.user, book=self.book)
        WishList.objects.create(user=self.other_user, book=self.book)

        self.client.force_login(self.user)
        response = self.client.get(reverse('books:wishlist_list'))
        items = list(response.context['wishlist_items'])

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].user, self.user)
