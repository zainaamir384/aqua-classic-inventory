from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		OWNER = "OWNER", "Owner/Admin"
		STAFF = "STAFF", "Staff"

	role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)

	class Meta:
		verbose_name = "user"
		verbose_name_plural = "users"

	def __str__(self) -> str:
		return self.get_full_name() or self.username

# Create your models here.
