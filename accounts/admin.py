from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
	add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Role", {"fields": ("role",)}),)
	list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
	list_filter = ("role", "is_active", "is_staff", "is_superuser")
	search_fields = ("username", "email", "first_name", "last_name")

# Register your models here.
