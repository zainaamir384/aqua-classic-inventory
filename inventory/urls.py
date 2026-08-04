from django.urls import path

from .views import (
    AssemblyView,
    LocationCreateView,
    LocationListView,
    LocationUpdateView,
    StockItemListView,
    StockLedgerListView,
    StockMovementCreateView,
)

app_name = "inventory"

urlpatterns = [
    path("locations/", LocationListView.as_view(), name="location-list"),
    path("locations/add/", LocationCreateView.as_view(), name="location-add"),
    path("locations/<int:pk>/edit/", LocationUpdateView.as_view(), name="location-edit"),
    path("stock/", StockItemListView.as_view(), name="stock-list"),
    path("ledger/", StockLedgerListView.as_view(), name="stock-ledger"),
    path("ledger/add/", StockMovementCreateView.as_view(), name="movement-add"),
    path("assemble/", AssemblyView.as_view(), name="assemble-unit"),
]