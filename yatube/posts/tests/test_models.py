from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text="Тестовый текст" * 20,
            author=User.objects.create_user(username="Model Tester"),
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            "text": "Текст",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_object_name_is_text_field(self):
        """В поле __str__  объекта Post записано значение поля text
        длиной в 15 символов.
        """
        post = PostModelTest.post
        expected_object_name = post.text[:15]

        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title="Ж" * 300, slug="z" * 200)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        group = GroupModelTest.group
        field_verboses = {
            "title": "Группа",
            "slug": "Slug",
            "description": "Описание",
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name,
                    expected
                )

    def test_object_name_is_title_field(self):
        """В поле __str__  объекта Group записано значение поля title."""
        group = GroupModelTest.group
        expected_object_name = group.title

        self.assertEqual(expected_object_name, str(group))
