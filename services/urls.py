from django.urls import path
from .views import (
    ServiceCompleteView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceDispatchView,
    ServiceListView,
    ServiceResetPendingView,
    ServiceUpdateView,
)

app_name = "services"

urlpatterns = [
    path("", ServiceListView.as_view(), name="service-list"),
    path("add/", ServiceCreateView.as_view(), name="service-add"),
    path("<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),
    path("<int:pk>/edit/", ServiceUpdateView.as_view(), name="service-edit"),
    path("<int:pk>/delete/", ServiceDeleteView.as_view(), name="service-delete"),
    path("<int:pk>/dispatch/", ServiceDispatchView.as_view(), name="service-dispatch"),
    path("<int:pk>/reset-pending/", ServiceResetPendingView.as_view(), name="service-reset-pending"),
    path("<int:pk>/complete/", ServiceCompleteView.as_view(), name="service-complete"),
]
