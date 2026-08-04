from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderLineItem, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = ("name", "contact_person", "phone", "is_active", "created_at")
	search_fields = ("name", "contact_person", "phone", "address", "notes")
	list_filter = ("is_active",)


class PurchaseOrderLineItemInline(admin.TabularInline):
	model = PurchaseOrderLineItem
	extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
	list_display = ("id", "supplier", "status", "order_date", "expected_delivery_date", "created_by")
	search_fields = ("supplier__name", "notes", "created_by__username")
	list_filter = ("status", "order_date", "supplier")
	inlines = [PurchaseOrderLineItemInline]

# Register your models here.
