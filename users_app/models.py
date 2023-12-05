from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    username = models.CharField(unique=True, max_length=30)
    email = models.EmailField(unique=True, max_length=30)
    # is_active = models.BooleanField(default=False)
