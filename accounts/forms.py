from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

from .models import User


class StaffCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")


class StaffUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active")


class AdminPasswordResetForm(PasswordChangeForm):
    pass
