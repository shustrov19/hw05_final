from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User

TEST_SLUG = 'test-slug'
TEST_USERNAME = 'test_author'
INDEX_PAGE = '/'
GROUP_LIST_PAGE = f'/group/{TEST_SLUG}/'
PROFILE_PAGE_AUTHOR = f'/profile/{TEST_USERNAME}/'
CREATE_PAGE = '/create/'
PAGE_404 = '/unexisting_page/'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username=TEST_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост #1',
        )
        cls.POST_DETAIL_PAGE = f'/posts/{cls.post.pk}/'
        cls.POST_EDIT_PAGE = f'/posts/{cls.post.pk}/edit/'
        # Шаблоны по адресам
        cls.TEMPLATES_URL_NAMES = {
            INDEX_PAGE: 'posts/index.html',
            GROUP_LIST_PAGE: 'posts/group_list.html',
            PROFILE_PAGE_AUTHOR: 'posts/profile.html',
            cls.POST_DETAIL_PAGE: 'posts/post_detail.html',
            CREATE_PAGE: 'posts/create_post.html',
            cls.POST_EDIT_PAGE: 'posts/create_post.html',
            PAGE_404: 'core/404.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.author = PostURLTests.user
        self.not_author = User.objects.create_user(username='test_not_author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.not_author)
        # Доступные urls для каждого типа пользователей
        self.URLS_ACCESS_TO_PAGES_OK = {
            self.guest_client: (
                INDEX_PAGE,
                GROUP_LIST_PAGE,
                PROFILE_PAGE_AUTHOR,
                self.POST_DETAIL_PAGE,
            ),
            self.authorized_not_author: (CREATE_PAGE, ),
            self.authorized_author: (self.POST_EDIT_PAGE, )
        }
        cache.clear()

    def test_url_custom_404(self):
        """Несуществующая страница недоступна."""
        response = self.guest_client.get(PAGE_404)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступные для каждого типа пользователей"""
        for user in self.URLS_ACCESS_TO_PAGES_OK:
            for url in self.URLS_ACCESS_TO_PAGES_OK[user]:
                with self.subTest(address=url):
                    response = user.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest_on_admin_login(self):
        """Страница перенаправит анонимного пользователя на страницу логина."""
        for url in (CREATE_PAGE, self.POST_EDIT_PAGE):
            with self.subTest(address=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, f'/auth/login/?next={url}'
                )

    def test_redirect_authorized_on_post(self):
        """Страница перенаправит авторизованного пользователя(не автора поста)
        на страницу поста автора."""
        response = self.authorized_not_author.get(
            self.POST_EDIT_PAGE, follow=True)
        self.assertRedirects(response, self.POST_DETAIL_PAGE)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.TEMPLATES_URL_NAMES.items():
            with self.subTest(address=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)
