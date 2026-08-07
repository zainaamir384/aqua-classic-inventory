from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordContextMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView, View

from .forms import AdminPasswordResetForm, StaffCreateForm, StaffUpdateForm
from .mixins import OwnerRequiredMixin
from .models import User


class StaffListView(OwnerRequiredMixin, ListView):
    model = User
    template_name = "accounts/staff_list.html"
    context_object_name = "staff_list"

    def get_queryset(self):
        return User.objects.exclude(is_superuser=True).order_by("username")


class StaffCreateView(OwnerRequiredMixin, CreateView):
    model = User
    form_class = StaffCreateForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("accounts:staff-list")

    def form_valid(self, form):
        messages.success(self.request, "Staff account created.")
        return super().form_valid(form)


class StaffUpdateView(OwnerRequiredMixin, UpdateView):
    model = User
    form_class = StaffUpdateForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("accounts:staff-list")

    def form_valid(self, form):
        messages.success(self.request, "Staff account updated.")
        return super().form_valid(form)


class StaffDeactivateView(OwnerRequiredMixin, View):
    template_name = "accounts/staff_confirm_deactivate.html"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return redirect("accounts:staff-list") if user.is_superuser else self.render_to_response({"staff": user})

    def post(self, request, pk):
        staff = get_object_or_404(User, pk=pk)
        staff.is_active = False
        staff.save(update_fields=["is_active"])
        messages.success(request, f"{staff.username} has been deactivated.")
        return redirect("accounts:staff-list")

    def render_to_response(self, context):
        from django.shortcuts import render

        return render(self.request, self.template_name, context)


class StaffPasswordResetView(OwnerRequiredMixin, FormView):
    template_name = "accounts/password_reset_form.html"
    success_url = reverse_lazy("accounts:staff-list")

    def dispatch(self, request, *args, **kwargs):
        self.staff = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return AdminPasswordResetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.staff
        kwargs["initial"] = {"user": self.staff}
        return kwargs

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f"Password reset for {user.username}.")
        return super().form_valid(form)


from django.views.generic import TemplateView


class OwnerProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        from catalog.models import Product
        from inventory.models import StockMovement
        from sales.models import SaleRecord

        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["page_title"] = "Owner Profile"
        context["owner"] = user
        context["total_products"] = Product.objects.filter(is_active=True).count()
        context["total_sales_count"] = SaleRecord.objects.count()
        context["my_movements_count"] = StockMovement.objects.filter(created_by=user).count()
        return context


class OwnerProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ("username", "first_name", "last_name", "email")
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class OwnerPasswordChangeView(LoginRequiredMixin, PasswordContextMixin, FormView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")
    title = "Change Password"

    def get_form_class(self):
        from django.contrib.auth.forms import PasswordChangeForm
        return PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Your password has been updated successfully!")
        return super().form_valid(form)
