from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='email', unique=True, null=True
    )
    # Согласно API docs эти поля обязательные, другой вопрос, что в админке
    # пользователя можно создать и без них
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.username