from django.urls import path

from .views import (
    BrandCreateView,
    BrandDeleteView,
    BrandListView,
    BrandUpdateView,
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryUpdateView,
    ProductComponentCreateView,
    ProductComponentDeleteView,
    ProductComponentListView,
    ProductComponentUpdateView,
    ProductAddStockView,
    ProductCreateView,
    ProductDeductStockView,
    ProductDeleteView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
)


app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/add/", CategoryCreateView.as_view(), name="category-add"),
    path("categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category-edit"),
    path("categories/<int:pk>/delete/", CategoryDeleteView.as_view(), name="category-delete"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("brands/add/", BrandCreateView.as_view(), name="brand-add"),
    path("brands/<int:pk>/edit/", BrandUpdateView.as_view(), name="brand-edit"),
    path("brands/<int:pk>/delete/", BrandDeleteView.as_view(), name="brand-delete"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/add/", ProductCreateView.as_view(), name="product-add"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product-edit"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    path("products/<int:pk>/deduct/", ProductDeductStockView.as_view(), name="product-deduct"),
    path("products/<int:pk>/add-stock/", ProductAddStockView.as_view(), name="product-add-stock"),
    path("bom/", ProductComponentListView.as_view(), name="bom-list"),
    path("bom/add/", ProductComponentCreateView.as_view(), name="bom-add"),
    path("bom/<int:pk>/edit/", ProductComponentUpdateView.as_view(), name="bom-edit"),
    path("bom/<int:pk>/delete/", ProductComponentDeleteView.as_view(), name="bom-delete"),
]
