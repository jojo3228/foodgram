from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        error_messages={
            'unique': 'Данный адрес уже используется',
        },
    )

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким именем уже существует',
        },
        max_length=150,
    )

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )

    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='media/users/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписок."""

    subscriber = models.ForeignKey(
        User,
        # CustomUser,
        on_delete=models.CASCADE,
        related_name="subscriber",
        help_text="Подписчик автора",
    )
    author = models.ForeignKey(
        User,
        # CustomUser,
        on_delete=models.CASCADE,
        related_name="subscribing",
        help_text="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("subscriber", "author"), name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F("author")),
                name="self_follow",
            )
        )

    def __str__(self):
        return f"{self.subscriber} подписался на {self.author}"
