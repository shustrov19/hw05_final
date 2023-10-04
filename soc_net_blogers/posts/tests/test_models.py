from datetime import datetime, timezone

from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост #1',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follower = Follow.objects.create(
            user=User.objects.create_user(username='follower'),
            author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        data = datetime.now(timezone.utc).strftime("%d-%m-%Y")
        field_str = {
            self.group.__str__(): 'Тестовая группа',
            self.post.__str__(): ('Тестовая группа, '
                                  f'{data}, '
                                  f'{self.user.username}, '
                                  'Тестовый пост #'),
            self.comment.__str__(): ('Комментарий от '
                                     f'{self.comment.author.username}: '
                                     f'{self.comment.text[:15]}'),
            self.follower.__str__(): ('Пользователь '
                                      f'{self.follower.user.username} '
                                      f'подписан на автора '
                                      f'{self.follower.author.username}')
        }
        for field, expected_value in field_str.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'pub_date': 'Дата публикации',
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
