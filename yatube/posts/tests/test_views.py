import shutil
import tempfile
from functools import cache

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Тестовая комент',
            author=cls.user,
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_folow = Client()
        self.authorized_client_folow.force_login(self.user2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test_slug'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0,
                         self.post.text)
        self.assertEqual(post_author_0, self.post.author.username)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(response.context[
            "title"], 'Последние обновления на сайте')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertEqual(response.context.get(
            'group').title, self.group.title)
        self.assertEqual(response.context.get(
            'group').description, self.group.description)
        self.assertEqual(response.context.get('group').slug, 'test_slug')
        self.assertEqual(len(response.context.get('page_obj').object_list), 1)
        self.assertEqual(response.context[
            "title"], f'Записи сообщества {self.group}')
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = response.context['form']
        self.assertIsInstance(form_field, PostForm)
        self.assertNotIn("is_edit", response.context)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('posts').text, 'Тестовая пост')
        self.assertEqual(response.context[
            "posts_count"], self.post.author.posts.count())
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(response.context.get('page_obj').object_list), 1)
        self.assertEqual(response.context["author"], self.user)
        self.assertEqual(response.context[
            "posts_count"], self.post.author.posts.count())
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context["post"].text, self.post.text)
        self.assertEqual(response.context["is_edit"], True)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug2'}))
        self.assertEqual(len(response.context.get('page_obj').object_list), 0)

    def test_add_comment(self):
        """Комментарий появляется на странице поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertIn(self.comment.text, str(response.context.get('comments')))

    def test_follow(self):
        """Проверка подписки."""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user2.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Проверка отписки."""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user2.username}))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user2.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков."""
        self.authorized_client_folow.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}))
        response = self.authorized_client_folow.get(reverse(
            'posts:follow_index'))
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author.username)

    def test_not_subscription_feed(self):
        """Запись не появляется в ленте подписчиков."""
        response = self.authorized_client_folow.get(reverse(
            'posts:follow_index'))
        self.assertNotContains(response, 'Тестовая пост')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовая пост {i}',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """10 постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_records(self):
        """3 поста."""
        # Проверка: на второй странице должно быть три поста.
        response = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Сache работает."""
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='Тестовая пост',
            group=self.group,
        )
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response3.content)
