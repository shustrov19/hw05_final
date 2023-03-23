from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm, User

INDEX_PAGE = reverse('posts:index')
ONE_USER = 1
TEST_USERNAME = 'test-user'
SIGNUP_PAGE = reverse('users:signup')


class UserCreateFormTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.form = CreationForm()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        # Подсчитаем количество записей в User
        users_count = User.objects.count()
        form_data = {
            'username': TEST_USERNAME,
            'password1': 'aeruiUHDWUI65',
            'password2': 'aeruiUHDWUI65',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            SIGNUP_PAGE,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, INDEX_PAGE)
        # Проверяем, увеличилось ли число users
        self.assertEqual(User.objects.count(), users_count + ONE_USER)
        # Проверяем, что создался пользователь
        self.assertTrue(User.objects.filter(username=TEST_USERNAME).exists())
