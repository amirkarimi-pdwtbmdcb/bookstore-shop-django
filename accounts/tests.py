from django.contrib.auth import authenticate, get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UsernameOrPhoneBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sara',
            password='a-strong-pass-1',
            phone_number='09120000001',
        )

    def test_authenticate_with_username(self):
        user = authenticate(username='sara', password='a-strong-pass-1')
        self.assertEqual(user, self.user)

    def test_authenticate_with_phone_number(self):
        # the same "username" slot is reused for the phone number, since
        # Django's authenticate() always passes the login field as "username"
        user = authenticate(username='09120000001', password='a-strong-pass-1')
        self.assertEqual(user, self.user)

    def test_wrong_password_fails(self):
        user = authenticate(username='sara', password='wrong-password')
        self.assertIsNone(user)

    def test_unknown_identifier_fails(self):
        user = authenticate(username='no-such-user', password='a-strong-pass-1')
        self.assertIsNone(user)

    def test_inactive_user_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save()
        user = authenticate(username='sara', password='a-strong-pass-1')
        self.assertIsNone(user)


class CustomUserModelTests(TestCase):
    def test_create_user_with_phone_number(self):
        user = User.objects.create_user(
            username='sara',
            password='a-strong-pass-1',
            phone_number='09120000001',
        )
        self.assertEqual(user.username, 'sara')
        self.assertEqual(user.phone_number, '09120000001')
        # create_user must hash the password, never store it as plain text
        self.assertNotEqual(user.password, 'a-strong-pass-1')
        self.assertTrue(user.check_password('a-strong-pass-1'))

    def test_phone_number_must_be_unique(self):
        User.objects.create_user(
            username='sara', password='pass12345', phone_number='09120000001'
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='sara2', password='pass12345', phone_number='09120000001'
            )


class SignUpViewTests(TestCase):
    def test_get_signup_page(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)

    def test_successful_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'newuser',
            'phone_number': '09120000002',
            'password1': 'a-strong-pass-1',
            'password2': 'a-strong-pass-1',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # SignUpView logs the user in right after signup
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        # and redirects to the book list (the site's home page)
        self.assertRedirects(response, reverse('books:book_list'))

    def test_signup_with_mismatched_passwords_does_not_create_user(self):
        self.client.post(reverse('accounts:signup'), {
            'username': 'newuser2',
            'phone_number': '09120000003',
            'password1': 'a-strong-pass-1',
            'password2': 'does-not-match',
        })
        self.assertFalse(User.objects.filter(username='newuser2').exists())


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sara', password='a-strong-pass-1', phone_number='09120000001'
        )

    def test_login_with_username(self):
        response = self.client.post(reverse('login'), {
            'username': 'sara', 'password': 'a-strong-pass-1',
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_phone_number(self):
        response = self.client.post(reverse('login'), {
            'username': '09120000001', 'password': 'a-strong-pass-1',
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_redirects_to_book_list(self):
        response = self.client.post(reverse('login'), {
            'username': 'sara', 'password': 'a-strong-pass-1',
        })
        self.assertRedirects(response, reverse('books:book_list'))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sara', password='a-strong-pass-1', phone_number='09120000001'
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertNotEqual(response.status_code, 200)

    def test_logged_in_user_sees_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], self.user)


class ProfileUpdateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sara', password='a-strong-pass-1', phone_number='09120000001'
        )
        self.client.force_login(self.user)

    def test_update_own_profile(self):
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'سارا',
            'last_name': 'احمدی',
            'email': 'sara@example.com',
            'phone_number': '09120000001',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'سارا')
        self.assertEqual(self.user.email, 'sara@example.com')

    def test_profile_edit_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('accounts:profile_edit'))
        self.assertNotEqual(response.status_code, 200)
