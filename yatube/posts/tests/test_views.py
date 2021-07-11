import datetime
import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

        cls.user = User.objects.create_user(username="PostAuthor")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group",
        )
        cls.post = Post.objects.create(
            text="Test post text",
            pub_date=datetime.datetime.today(),
            image=uploaded,
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Обращение через name использует соответствующий шаблон."""
        templates_page_names = {
            "index.html": reverse("index"),
            "posts/new.html": reverse("new_post"),
            "posts/group.html": reverse(
                "group_posts",
                kwargs={"slug": "test_group"}
            ),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом.
        Новый пост с указанной группой попадает на страницу index.
        """
        response = self.authorized_client.get(reverse("index"))
        first_post = response.context["page"][0]

        self.assertEqual(first_post.text, "Test post text")
        self.assertEqual(first_post.pub_date.date(),
                         datetime.datetime.today().date())
        self.assertEqual(first_post.author, self.user)
        self.assertEqual(first_post.group, self.group)

    def test_group_page_show_correct_context(self):
        """Шаблон group/<slug> сформирован с правильным контекстом.
        Новый пост с указанной группой попадает на страницу правильной группы.
        """
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": "test_group"})
        )
        first_post = response.context["page"][0]
        first_post_text = first_post.text

        self.assertEqual(response.context["group"].title, "Test group")
        self.assertEqual(response.context["group"].slug, "test_group")
        self.assertEqual(first_post_text, "Test post text")

    def test_post_not_shown_in_wrong_group(self):
        """ "Новый пост с указанной группой не попадает
        на страницу неправильной группы.
        """
        wrong_group = PostPagesTests.group
        wrong_group.slug = "wrong_group"

        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": "wrong_group"})
        )
        first_post = response.context.get("page")

        self.assertIsNone(first_post)

    def test_new_page_show_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("new_post"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]

                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        post_author = PostPagesTests.post.author

        self.authorized_client.force_login(post_author)
        response = self.authorized_client.get(
            reverse(
                "post_edit", kwargs={
                    "username": post_author.username,
                    "post_id": self.post.id
                }
            )
        )

        self.assertEqual(response.context.get("editing"), True)
        self.assertEqual(response.context.get("post_id"), self.post.id)

    def test_profile_page_show_correct_context(self):
        """Шаблон профайла сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("profile", kwargs={"username": "PostAuthor"})
        )
        first_post = response.context["page"][0]
        first_post_text = first_post.author.username

        self.assertEqual(first_post_text, "PostAuthor")

    def test_post_page_show_correct_context(self):
        """Шаблон профайла сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("post", kwargs={"username": "PostAuthor", "post_id": 1})
        )
        single_post = response.context["post"]

        self.assertEqual(single_post.text, "Test post text")

    def test_image_in_post_is_in_context(self):
        """При выводе поста с картинкой изображение передаётся в context"""
        test_pages = [
            reverse("index"),
            reverse("profile", kwargs={"username": "PostAuthor"}),
            reverse("group_posts", kwargs={"slug": "test_group"}),
            reverse("post", kwargs={
                "username": "PostAuthor",
                "post_id": self.post.id
            }),
        ]

        for test_page in test_pages:
            with self.subTest(test_page=test_page):
                self.authorized_client.get(test_page)

                self.assertTrue(Post.objects.filter(
                    text="Test post text",
                    image="posts/small.gif").exists()
                )

    def test_cached_index_page(self):
        """Главная страница попадает в кэш"""
        cached_post = Post.objects.create(
            text="Cached post text",
            pub_date=datetime.datetime.today(),
            author=self.user,
        )

        response_before_del = self.guest_client.get(reverse("index"))
        cached_post.delete()
        response_after_del = self.guest_client.get(reverse("index"))

        self.assertEqual(response_before_del.content,
                         response_after_del.content)
        self.assertEqual(response_after_del.context, None)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        follower = User.objects.create_user(username="FollowerTester")
        following = self.post.author
        self.authorized_client.force_login(follower)

        follows = {
            "profile_follow": True,
            "profile_unfollow": False,
        }

        for intent, result in follows.items():
            with self.subTest(intent=intent):
                self.authorized_client.get(
                    reverse(intent, kwargs={"username": following.username})
                )

                self.assertEqual(Follow.objects.filter(
                    user=follower, author=following).exists(), result)

    def test_new_post_appears_in_follower_feed(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется у тех, кто не подписан."""
        follower = User.objects.create_user(username="FollowerTester")
        non_follower = User.objects.create_user(username="NonFollowerTester")
        following = self.post.author
        Follow.objects.create(user=follower, author=following)

        self.authorized_client.force_login(follower)
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(response.context["page"][0].text, self.post.text)

        self.authorized_client.force_login(non_follower)
        response = self.authorized_client.get(reverse("follow_index"))
        with self.assertRaises(IndexError):
            response.context["page"][0]

    def test_authorized_user_can_comment(self):
        """Только авторизированный пользователь может комментировать посты"""
        commenter = User.objects.create_user(username="CommentTester")
        self.authorized_client.force_login(commenter)
        form_data = {
            "text": "Test comment",
        }

        response = self.authorized_client.post(
            reverse("add_comment", kwargs={
                "username": self.user.username,
                "post_id": self.post.id
            }
            ), data=form_data, follow=True)
        self.assertTrue(Comment.objects.filter(text="Test comment").exists())

        response = self.guest_client.get(
            reverse("add_comment", kwargs={
                "username": self.user.username,
                "post_id": self.post.id
            }
            ))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response,
                             f"/auth/login/?next=/{self.user.username}/"
                             f"{self.post.id}/comment")


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group",
        )
        test_user = User.objects.create_user(username="PaginatorTester")

        posts = []
        for i in range(13):
            posts.append(
                Post(
                    text=f"Test post {i} text",
                    pub_date=datetime.datetime.today(),
                    author=test_user,
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """На первой странице паджинатора 10 записей."""
        cache.clear()
        page_names = [
            reverse("index"),
            reverse("profile", kwargs={"username": "PaginatorTester"}),
            reverse("group_posts", kwargs={"slug": "test_group"}),
        ]

        for page in page_names:
            with self.subTest(page=page):
                response = self.guest_client.get(page)

                self.assertEqual(
                    len(response.context.get("page").object_list),
                    10
                )

    def test_second_page_contains_three_records(self):
        """На второй странице паджинатора 3 записи."""
        response = self.guest_client.get(reverse("index") + "?page=2")

        self.assertEqual(len(response.context.get("page").object_list), 3)
