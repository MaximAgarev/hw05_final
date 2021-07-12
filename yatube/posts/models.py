from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name="Группа", max_length=200)
    slug = models.SlugField(verbose_name="Slug", max_length=100, unique=True)
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст")
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        verbose_name="Группа",
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name="Комментарий",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    text = models.TextField(
        verbose_name="Текст",
    )
    created = models.DateTimeField(
        verbose_name="Дата написания",
        auto_now_add=True
    )

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="following"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_following"
            )
        ]
    # Я все-таки решил оставить этот вариант.
    # По ссылке unique_together на djangoproject написано:
    # Use UniqueConstraint with the constraints option instead.
    # UniqueConstraint provides more functionality than unique_together.
    # unique_together may be deprecated in the future.
    # Не буду приучиваться к устаревающему варианту :)
