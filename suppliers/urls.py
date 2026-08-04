from django.urls import path

from .views import (
    PurchaseOrderCreateView,
    PurchaseOrderDeleteView,
    PurchaseOrderDetailView,
    PurchaseOrderListView,
    PurchaseOrderReceiveView,
    PurchaseOrderUpdateView,
    SupplierCreateView,
    SupplierDeleteView,
    SupplierListView,
    SupplierUpdateView,
)


app_name = "suppliers"

urlpatterns = [
    path("suppliers/", SupplierListView.as_view(), name="supplier-list"),
    path("suppliers/add/", SupplierCreateView.as_view(), name="supplier-add"),
    path("suppliers/<int:pk>/edit/", SupplierUpdateView.as_view(), name="supplier-edit"),
    path("suppliers/<int:pk>/delete/", SupplierDeleteView.as_view(), name="supplier-delete"),
    path("purchase-orders/", PurchaseOrderListView.as_view(), name="po-list"),
    path("purchase-orders/add/", PurchaseOrderCreateView.as_view(), name="po-add"),
    path("purchase-orders/<int:pk>/", PurchaseOrderDetailView.as_view(), name="po-detail"),
    path("purchase-orders/<int:pk>/edit/", PurchaseOrderUpdateView.as_view(), name="po-edit"),
    path("purchase-orders/<int:pk>/delete/", PurchaseOrderDeleteView.as_view(), name="po-delete"),
    path("purchase-orders/<int:pk>/receive/", PurchaseOrderReceiveView.as_view(), name="po-receive"),
]