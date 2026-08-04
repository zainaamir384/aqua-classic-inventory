from django.contrib import admin

from .models import Brand, Category, Product, ProductComponent


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "is_active", "created_at")
	search_fields = ("name", "description")
	list_filter = ("is_active",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
	list_display = ("name", "origin_label", "is_active", "created_at")
	search_fields = ("name", "origin_label", "notes")
	list_filter = ("origin_label", "is_active")


class ProductComponentInline(admin.TabularInline):
	model = ProductComponent
	fk_name = "product"
	extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("name", "sku", "category", "brand", "unit_type", "stage_count", "is_active")
	list_filter = ("category", "brand", "unit_type", "configuration", "is_active")
	search_fields = ("name", "sku", "notes")
	inlines = [ProductComponentInline]


@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
	list_display = ("product", "component", "quantity")
	search_fields = ("product__name", "component__name")
	list_filter = ("product__category", "component__category")

# Register your models here.
