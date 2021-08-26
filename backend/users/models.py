from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import BooleanField, Count, Value


class UserQuerySet(models.QuerySet):
    def follow_recipes(self, user=None):
        """Отфильтровать подписоту и получить связанныерецепты."""
        queryset = self.filter(
            following__user=user
        ).prefetch_related('recipes').annotate(
            is_subscribed=Value(True, output_field=BooleanField()),
            recipes_count=Count('recipes__author')
        ).order_by('-author__id')
        return queryset


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='email', unique=True, null=True
    )
    # Согласно API docs эти поля обязательные, другой вопрос, что в админке
    # пользователя можно создать и без них
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    objects = UserQuerySet.as_manager()

    def __str__(self):
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'.strip()
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
