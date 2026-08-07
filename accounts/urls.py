from django.urls import path

from .views import (
    OwnerPasswordChangeView,
    OwnerProfileEditView,
    OwnerProfileView,
    StaffCreateView,
    StaffDeactivateView,
    StaffListView,
    StaffPasswordResetView,
    StaffUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("profile/", OwnerProfileView.as_view(), name="profile"),
    path("profile/edit/", OwnerProfileEditView.as_view(), name="profile-edit"),
    path("password-change/", OwnerPasswordChangeView.as_view(), name="change-password"),
    path("staff/", StaffListView.as_view(), name="staff-list"),
    path("staff/add/", StaffCreateView.as_view(), name="staff-add"),
    path("staff/<int:pk>/edit/", StaffUpdateView.as_view(), name="staff-edit"),
    path("staff/<int:pk>/deactivate/", StaffDeactivateView.as_view(), name="staff-deactivate"),
    path("staff/<int:pk>/reset-password/", StaffPasswordResetView.as_view(), name="staff-reset-password"),
]