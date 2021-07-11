import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostCreateFormTest(TestCase):
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.form = PostForm()
        cls.user = User.objects.create_user(username="PostAuthor")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group",
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает новый пост, с группой и без группы"""
        form_data_options = [
            {"text": "Test post text", "group": self.group.id},
            {"text": "Test post text"},
        ]

        for form_data in form_data_options:
            with self.subTest(form_data=form_data):
                post_count = Post.objects.count()
                response = self.authorized_client.post(
                    reverse("new_post"), data=form_data, follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, reverse("index"))
                self.assertEqual(Post.objects.count(), post_count + 1)
                group = form_data.get("group")
                self.assertTrue(
                    Post.objects.filter(
                        text="Test post text",
                        author=self.user,
                        group=group,
                    ).exists()
                )

    def test_edit_post(self):
        """При редактировании поста через форму
        изменяется соответствующая запись в базе данных"""
        self.post = Post.objects.create(
            text="Test post text",
            author=self.user,
            group=PostCreateFormTest.group
        )
        form_data = {
            "text": "Test post changed",
            "group": self.group.id,
            "image": self.uploaded,
        }

        response = self.authorized_client.post(
            reverse("post_edit", kwargs={
                "username": "PostAuthor",
                "post_id": self.post.id}
            ),
            data=form_data,
            follow=True,
        )

        self.post.refresh_from_db()
        self.assertRedirects(
            response, reverse(
                "post", kwargs={
                    "username": "PostAuthor",
                    "post_id": self.post.id}
            )
        )
        self.assertEqual(self.post.text, "Test post changed")
        self.assertEqual(self.post.image, "posts/small.gif")
