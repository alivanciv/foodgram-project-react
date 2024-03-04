from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator

from users.constants import (
    MAX_NAME_LENGTH,
    MAX_EMAIL_LENGTH,
)
from users.validators import required_username


class CustomUser(AbstractUser):
    username = models.CharField(
        verbose_name='Логин',
        max_length=MAX_NAME_LENGTH,
        unique=True,
        validators=[
            UnicodeUsernameValidator(
                message='Недопустимые символы в нике.'
            ),
            required_username
        ]
    )
    email = models.EmailField(
        verbose_name='Почта',
        max_length=MAX_EMAIL_LENGTH,
        unique=True)
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_NAME_LENGTH
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_NAME_LENGTH
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username[:MAX_NAME_LENGTH]


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="following"
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name="self_subscription",
            ),
        ]
