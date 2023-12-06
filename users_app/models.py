from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError({'Пользователь должен иметь username'})
        if not email:
            raise ValueError({'Пользователь должен иметь email'})
        if not password:
            raise ValueError({'Пользователь должен иметь password'})

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(unique=True, max_length=30)
    email = models.EmailField(unique=True, max_length=30)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'

    objects = UserManager()

    def __str__(self):
        return self.username
