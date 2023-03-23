from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import User

TEST_USERNAME = 'test_user'
SIGNUP_PAGE = reverse('users:signup')
LOGIN_PAGE = reverse('users:login')
PSWRD_CHANGE_PAGE = reverse('users:password_change')
PSWRD_CHANGE_DONE_PAGE = reverse('users:password_change_done')
PSWRD_RESET_PAGE = reverse('users:password_reset')
PSWRD_RESET_DONE_PAGE = reverse('users:password_reset_done')
PSWRD_RESET_CONFIRM_PAGE = reverse('users:password_reset_confirm',
                                   args=('uidb64', 'token'))
PSWRD_RESET_COMPLETE_PAGE = reverse('password_reset_complete')
LOGOUT_PAGE = reverse('users:logout')

TEMPLATES_PAGES_NAME = {
    SIGNUP_PAGE: 'users/signup.html',
    LOGIN_PAGE: 'users/login.html',
    PSWRD_CHANGE_PAGE: 'users/password_change_form.html',
    PSWRD_CHANGE_DONE_PAGE: 'users/password_change_done.html',
    PSWRD_RESET_PAGE: 'users/password_reset_form.html',
    PSWRD_RESET_DONE_PAGE: 'users/password_reset_done.html',
    PSWRD_RESET_CONFIRM_PAGE: 'users/password_reset_confirm.html',
    PSWRD_RESET_COMPLETE_PAGE: 'users/password_reset_complete.html',
    LOGOUT_PAGE: 'users/logged_out.html',
}


class UserViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим пользователя в БД
        cls.user = User.objects.create_user(username=TEST_USERNAME)

    def setUp(self):
        self.user = UserViewsTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in TEMPLATES_PAGES_NAME.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_show_correct_context(self):
        """Шаблон posts:post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(SIGNUP_PAGE)
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField
        }
        # Проверяем, что типы полей формы в context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)
