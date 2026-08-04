from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Product


class Supplier(models.Model):
	name = models.CharField(max_length=160, unique=True)
	contact_person = models.CharField(max_length=160, blank=True)
	phone = models.CharField(max_length=40, blank=True)
	address = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class PurchaseOrder(models.Model):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		RECEIVED = "RECEIVED", "Received"
		PARTIAL = "PARTIAL", "Partial"

	supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
	order_date = models.DateField(auto_now_add=True)
	expected_delivery_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	notes = models.TextField(blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="purchase_orders_created")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"PO-{self.pk or 'new'} - {self.supplier.name}"


class PurchaseOrderLineItem(models.Model):
	purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="line_items")
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_order_items")
	ordered_boxes = models.PositiveIntegerField(null=True, blank=True, help_text="Number of boxes ordered.")
	pieces_per_box = models.PositiveIntegerField(null=True, blank=True, help_text="Pieces in each box. Auto-filled from product if available.")
	ordered_qty = models.DecimalField(max_digits=12, decimal_places=3, help_text="Total pieces ordered. Auto-calculated if boxes are entered.")
	received_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
	unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

	class Meta:
		ordering = ["product__name"]

	def clean(self):
		if self.ordered_qty <= 0:
			raise ValidationError({"ordered_qty": "Ordered quantity must be greater than zero."})

	@property
	def outstanding_qty(self):
		return max(self.ordered_qty - self.received_qty, Decimal("0"))

	def __str__(self) -> str:
		return f"{self.product} x {self.ordered_qty}"

# Create your models here.
