from http import HTTPStatus

from django.test import Client, TestCase

from ..forms import User

TEST_USERNAME = 'test_user'
SIGNUP_PAGE = '/auth/signup/'
LOGOUT_PAGE = '/auth/logout/'
LOGIN_PAGE = '/auth/login/'
PSWRD_RESET_PAGE = '/auth/password_reset/'
PSWRD_RESET_DONE_PAGE = '/auth/password_reset/done/'
PSWRD_RESET_CONFIRM_PAGE = '/auth/reset/<uidb64>/<token>/'
PSWRD_RESET_COMPLETE_PAGE = '/auth/reset/done/'
PSWRD_CHANGE_PAGE = '/auth/password_change/'
PSWRD_CHANGE_DONE_PAGE = '/auth/password_change/done/'

TEMPLATE_URLS_NAMES = {
    SIGNUP_PAGE: 'users/signup.html',
    LOGIN_PAGE: 'users/login.html',
    PSWRD_RESET_PAGE: 'users/password_reset_form.html',
    PSWRD_RESET_DONE_PAGE: 'users/password_reset_done.html',
    PSWRD_RESET_CONFIRM_PAGE: 'users/password_reset_confirm.html',
    PSWRD_RESET_COMPLETE_PAGE: 'users/password_reset_complete.html',
    PSWRD_CHANGE_PAGE: 'users/password_change_form.html',
    PSWRD_CHANGE_DONE_PAGE: 'users/password_change_done.html',
    LOGOUT_PAGE: 'users/logged_out.html',
}


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим пользователя в БД
        cls.user = User.objects.create_user(username=TEST_USERNAME)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Регистрируем пользователя
        self.user = UserURLTests.user
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.URLS_ACCESS_TO_PAGES_OK = {
            self.authorized_client: (
                PSWRD_CHANGE_PAGE,
                PSWRD_CHANGE_DONE_PAGE
            ),
            self.guest_client: (
                SIGNUP_PAGE,
                LOGOUT_PAGE,
                LOGIN_PAGE,
                PSWRD_RESET_PAGE,
                PSWRD_RESET_DONE_PAGE,
                PSWRD_RESET_CONFIRM_PAGE,
                PSWRD_RESET_COMPLETE_PAGE
            ),
        }

    def test_urls_exists_at_desired_location_for_guest(self):
        """Страницы доступные для каждого типа пользователей"""
        for user in self.URLS_ACCESS_TO_PAGES_OK:
            for url in self.URLS_ACCESS_TO_PAGES_OK[user]:
                with self.subTest(address=url):
                    response = user.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest_on_admin_login(self):
        """Страница перенаправит анонимного пользователя на страницу логина."""
        for url in self.URLS_ACCESS_TO_PAGES_OK[self.authorized_client]:
            with self.subTest(address=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, f'/auth/login/?next={url}'
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in TEMPLATE_URLS_NAMES.items():
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
