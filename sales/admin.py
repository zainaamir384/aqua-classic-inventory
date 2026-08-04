from django.contrib import admin

from .models import SaleItem, SaleRecord


class SaleItemInline(admin.TabularInline):
	model = SaleItem
	extra = 1


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
	list_display = ("id", "sale_date", "location", "customer_name", "total_amount", "created_by")
	search_fields = ("customer_name", "customer_phone", "notes", "created_by__username")
	list_filter = ("sale_date", "location")
	inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
	list_display = ("sale", "product", "quantity", "sale_price")
	search_fields = ("product__name", "sale__customer_name")

# Register your models here.
