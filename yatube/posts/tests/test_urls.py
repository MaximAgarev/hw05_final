import datetime
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="PostAuthor")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group",
        )
        cls.post = Post.objects.create(
            text="Test post text",
            pub_date=datetime.datetime.today(),
            author=cls.user,
            group=cls.group,
            id=1,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get("/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_exists_at_desired_location_authorized(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/new/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_redirect_anonymous_on_auth_login(self):
        """Страница /new/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get("/new/", follow=True)

        self.assertRedirects(response, "/auth/login/?next=/new/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            "index.html": "/",
            "posts/group.html": "/group/test_group/",
            "posts/new.html": "/new/",
        }

        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertTemplateUsed(response, template)

    def test_user_profile_exists_at_desired_location(self):
        """Страница профайла доступна любому пользователю"""
        response = self.guest_client.get(
            reverse("profile", kwargs={
                "username": PostURLTests.post.author.username,
            })
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_page_exists_at_desired_location(self):
        """Отдельный пост доступен любому пользователю"""
        response = self.guest_client.get(
            reverse(
                "post",
                kwargs={
                    "username": PostURLTests.post.author.username,
                    "post_id": PostURLTests.post.id,
                },
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_available_for_author(self):
        """Страница редактирования доступна автору"""
        post_author = PostURLTests.post.author
        self.authorized_client.force_login(post_author)

        response = self.authorized_client.get("/PostAuthor/1/edit/")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "posts/new.html")

    def test_edit_page_not_available_for_non_author(self):
        """Страница редактирования недоступна авторизованному не-автору"""
        non_author = User.objects.create_user(username="NonAuthor")
        self.authorized_client.force_login(non_author)

        response = self.authorized_client.get("/PostAuthor/1/edit/")

        self.assertRedirects(response, "/PostAuthor/1/")

    def test_edit_page_not_available_for_not_authorized(self):
        """Страница редактирования недоступна неавторизованному"""
        response = self.guest_client.get("/PostAuthor/1/edit/")

        self.assertRedirects(response, "/auth/login/?next=/PostAuthor/1/edit/")

    def test_404_if_page_not_found(self):
        """Возвращает ли сервер код 404, если страница не найдена"""
        response = self.guest_client.get("dead_link/")

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
