from http import HTTPStatus
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slag',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)

    def test_home(self):
        """доступны всем"""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.id}/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_authorized(self):
        """Страница доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_author(self):
        """Страница доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """без авторизации  URL недоступны"""
        url_names = (
            '/create/',
            f'/posts/{self.post.id}/edit/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                url = urljoin(reverse('login'), f"?next={adress}")
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, url)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test_slag/',
            'posts/create_post.html': '/create/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        """срабатывает 404 и использует соответствующий шаблон."""
        response = self.guest_client.get('/qwerty/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_redirect_anonymous_on_login(self):
        """Страница  перенаправит не автора на страницу поста."""
        response = self.authorized_client2.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')
