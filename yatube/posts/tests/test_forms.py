import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

TEST_SLUG = 'test-slug'
TEST_USERNAME = 'test_author'
GROUP_LIST_PAGE = reverse('posts:group_list', args=(TEST_SLUG, ))
PROFILE_PAGE = reverse('posts:profile', args=(TEST_USERNAME, ))
CREATE_PAGE = reverse('posts:post_create')
ONE_POST = 1
ONE_COMMENT = 1
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.form = PostForm()
        cls.POST_EDIT_PAGE = reverse('posts:post_edit', args=(cls.post.pk, ))
        cls.POST_DETAIL_PAGE = reverse('posts:post_detail',
                                       args=(cls.post.pk, ))
        cls.ADD_COMMENT_PAGE = reverse('posts:add_comment',
                                       args=(cls.post.pk, ))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = PostCreateFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост с картинкой',
            'group': self.group.pk,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            CREATE_PAGE,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, PROFILE_PAGE)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + ONE_POST)
        # Проверяем, что создалась запись с заданным текстом и картинкой
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост с картинкой',
            image='posts/small.gif').exists())

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменённый тестовый пост #1',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            self.POST_EDIT_PAGE,
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, self.POST_DETAIL_PAGE)
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что изменилась запись
        self.assertIsNot(Post.objects.get(pk=self.post.pk), self.post)
        # Проверяем, что изменилась запись с заданным текстом
        self.assertTrue(Post.objects.filter(
            text='Изменённый тестовый пост #1').exists())

    def test_add_comment_for_authorized(self):
        "Авторизованный пользователь может добавить коментарий"
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        self.authorized_client.post(
            self.ADD_COMMENT_PAGE,
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count + ONE_COMMENT)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author.username, self.user.username)
        self.assertEqual(comment.post, self.post)
        response = self.authorized_client.get(self.POST_DETAIL_PAGE)
        self.assertEqual(response.context['comments'][0], comment)

    def test_not_add_comment_guest(self):
        "Неавторизованный пользователь не может добавить коментарий"
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        self.guest_client.post(
            self.ADD_COMMENT_PAGE,
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count)
