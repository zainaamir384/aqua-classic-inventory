from django.contrib import admin

from .models import Location, StockItem, StockMovement


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
	list_display = ("name", "code", "is_default", "is_active")
	search_fields = ("name", "code", "address", "notes")
	list_filter = ("is_default", "is_active")


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
	list_display = ("product", "location", "quantity_on_hand", "updated_at")
	search_fields = ("product__name", "product__sku", "location__name")
	list_filter = ("location", "product__category", "product__brand")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
	list_display = ("created_at", "product", "location", "movement_type", "quantity", "created_by")
	search_fields = ("product__name", "product__sku", "reference_note", "created_by__username")
	list_filter = ("movement_type", "location", "product__category", "product__brand", "created_at")
	readonly_fields = ("created_at",)

# Register your models here.
