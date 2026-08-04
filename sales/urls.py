from django.urls import path

from .views import SaleCreateView, SaleDeleteView, SaleDetailView, SaleListView, SaleUpdateView


app_name = "sales"

urlpatterns = [
    path("sales/", SaleListView.as_view(), name="sale-list"),
    path("sales/add/", SaleCreateView.as_view(), name="sale-add"),
    path("sales/<int:pk>/", SaleDetailView.as_view(), name="sale-detail"),
    path("sales/<int:pk>/edit/", SaleUpdateView.as_view(), name="sale-edit"),
    path("sales/<int:pk>/delete/", SaleDeleteView.as_view(), name="sale-delete"),
]
