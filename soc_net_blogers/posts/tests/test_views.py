import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

TEST_SLUG = 'test-slug'
TEST_USERNAME = 'test_author'
ONE_FOLLOW = 1
INDEX_PAGE = reverse('posts:index')
GROUP_LIST_PAGE = reverse('posts:group_list', args=(TEST_SLUG, ))
PROFILE_PAGE = reverse('posts:profile', args=(TEST_USERNAME, ))
CREATE_PAGE = reverse('posts:post_create')
FOLLOW_PROFILE = reverse('posts:profile_follow', args=(TEST_USERNAME, ))
UNFOLLOW_PROFILE = reverse('posts:profile_unfollow', args=(TEST_USERNAME, ))
FOLLOW_INDEX_PAGE = reverse('posts:follow_index')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост #1',
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

        cls.POST_DETAIL_PAGE = reverse('posts:post_detail',
                                       args=(cls.post.pk, ))
        cls.POST_EDIT_PAGE = reverse('posts:post_edit', args=(cls.post.pk, ))
        cls.TEMPLATE_PAGES_NAME = {
            INDEX_PAGE: 'posts/index.html',
            GROUP_LIST_PAGE: 'posts/group_list.html',
            PROFILE_PAGE: 'posts/profile.html',
            cls.POST_DETAIL_PAGE: 'posts/post_detail.html',
            CREATE_PAGE: 'posts/create_post.html',
            cls.POST_EDIT_PAGE: 'posts/create_post.html',
            FOLLOW_INDEX_PAGE: 'posts/follow.html'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.user = PostPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.not_author = User.objects.create_user(username='test_not_author')
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.not_author)
        # Очищаем кэш
        cache.clear()

    def test_pages_uses_correct_template(self):
        """View-функция использует соответствующий шаблон."""
        for reverse_name, template in self.TEMPLATE_PAGES_NAME.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX_PAGE)
        posts_list = response.context.get('page_obj')
        self.assertIsNotNone(posts_list)
        post = posts_list[0]
        self.assertEqual(post.image, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон posts:group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(GROUP_LIST_PAGE))
        group_list = response.context.get('page_obj')
        self.assertIsNotNone(group_list)
        post = group_list[0]
        self.assertEqual(post.group.title, self.group.title)
        self.assertEqual(post.group.description, self.group.description)
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(post.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон posts:profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(PROFILE_PAGE))
        posts_list = response.context.get('page_obj')
        self.assertIsNotNone(posts_list)
        post = posts_list[0]
        self.assertEqual(post.image, self.post.image)
        author = post.author.username
        self.assertEqual(author, self.user.username)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон posts:post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(self.POST_DETAIL_PAGE))
        post_id = response.context.get('post').pk
        self.assertEqual(post_id, self.post.pk)
        post_img = response.context.get('post').image
        self.assertEqual(post_img, self.post.image)
        # comments = response.context.get('comments')
        # self.assertEqual(comments[0], self.comment)

    def test_create_show_correct_context(self):
        """Шаблон posts:post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(CREATE_PAGE)
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_show_correct_context(self):
        """Шаблон posts:post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_EDIT_PAGE)
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_create_in_correct_page(self):
        """Созданный пост появляется в корректных шаблонах"""
        new_group = Group.objects.create(
            title='Неправильная тестовая группа',
            slug='wrong-test-slug',
            description='Нет описания',
        )
        new_post = Post.objects.create(
            author=self.user,
            group=new_group,
            text='Новый тестовый пост',
        )
        urls = [
            INDEX_PAGE,
            reverse('posts:group_list', args=('wrong-test-slug', )),
            PROFILE_PAGE
        ]
        response = self.authorized_client.get(GROUP_LIST_PAGE)
        posts_list = response.context.get('page_obj')
        # Проверка, что новый пост с новой группой не попадает
        # на страницу со старой группой
        self.assertNotIn(new_post, posts_list)
        # Проверка, что новый пост с новой группой попадает
        # на главную страницу, страницу с новой группой, страницу автора.
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                posts_list = response.context.get('page_obj')
                self.assertIn(new_post, posts_list)

    def test_cache_index_page(self):
        """Тестирование кэша на странице index"""
        response_1 = self.authorized_client.get(INDEX_PAGE).content
        Post.objects.all().delete()
        response_2 = self.authorized_client.get(INDEX_PAGE).content
        self.assertEqual(response_1, response_2)
        cache.clear()
        response_3 = self.authorized_client.get(INDEX_PAGE).content
        self.assertNotEqual(response_2, response_3)

    def test_follow_authorized(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        followers_count = Follow.objects.count()
        self.authorized_not_author.get(FOLLOW_PROFILE)
        self.assertEqual(Follow.objects.count(), followers_count + ONE_FOLLOW)
        self.assertTrue(Follow.objects.filter(
            author=self.user,
            user=self.not_author
        ).exists())

    def test_unfollow_authorized(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        Follow.objects.create(author=self.user, user=self.not_author)
        followers_count = Follow.objects.count()
        self.authorized_not_author.get(UNFOLLOW_PROFILE)
        self.assertEqual(Follow.objects.count(), followers_count - ONE_FOLLOW)
        self.assertFalse(Follow.objects.filter(
            author=self.user,
            user=self.not_author
        ).exists())

    def test_new_post_appears_for_subscribers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        Follow.objects.create(author=self.user, user=self.not_author)
        new_post = Post.objects.create(
            text='Текст для подписчиков',
            author=self.user,
            group=self.group
        )
        response = self.authorized_not_author.get(FOLLOW_INDEX_PAGE)
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_new_post_not_appear_for_non_subscribers(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него."""
        new_post = Post.objects.create(
            text='Текст для подписчиков',
            author=self.not_author,
            group=self.group
        )
        response = self.authorized_client.get(FOLLOW_INDEX_PAGE)
        self.assertNotIn(new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    AMOUNT_POSTS = 13
    FIRST_PAGE_POSTS_NUMBER = 10
    SECOND_PAGE_POSTS_NUMBER = 3

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
        posts_list = []
        for i in range(cls.AMOUNT_POSTS):
            posts_list.append(
                Post(
                    author=cls.user,
                    group=cls.group,
                    text=f'Тестовый пост #{i}',
                )
            )
        Post.objects.bulk_create(posts_list)
        cls.URLS = (INDEX_PAGE, GROUP_LIST_PAGE, PROFILE_PAGE)

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Очищаем кэш
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        for url in self.URLS:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context.get('page_obj')),
                                 self.FIRST_PAGE_POSTS_NUMBER)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть 3 поста."""
        for url in self.URLS:
            with self.subTest():
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')),
                                 self.SECOND_PAGE_POSTS_NUMBER)
