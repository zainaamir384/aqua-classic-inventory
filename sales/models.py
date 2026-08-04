from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Product
from inventory.models import Location


class SaleRecord(models.Model):
	sale_date = models.DateField(auto_now_add=True)
	location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="sales")
	customer_name = models.CharField(max_length=160, blank=True)
	customer_phone = models.CharField(max_length=40, blank=True)
	notes = models.TextField(blank=True)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales_created")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Sale #{self.pk or 'new'}"

	def recalculate_total(self, save=True):
		total = Decimal("0.00")
		for item in self.items.all():
			total += item.line_total
		self.total_amount = total
		if save and self.pk:
			self.save(update_fields=["total_amount"])

	@property
	def total_quantity(self):
		return sum((item.quantity for item in self.items.all()), Decimal("0"))

	@property
	def total_cost(self):
		return sum((item.line_cost for item in self.items.all()), Decimal("0.00"))

	@property
	def total_profit(self):
		return self.total_amount - self.total_cost

	@property
	def profit_margin_percent(self):
		if self.total_amount and self.total_amount > Decimal("0.00"):
			return (self.total_profit / self.total_amount) * Decimal("100.0")
		return Decimal("0.00")


class SaleItem(models.Model):
	sale = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
	quantity = models.DecimalField(max_digits=12, decimal_places=3)
	sale_price = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		ordering = ["product__name"]

	def clean(self):
		if self.quantity is not None and self.quantity <= 0:
			raise ValidationError({"quantity": "Quantity must be greater than zero."})
		if self.sale_price is not None and self.sale_price < 0:
			raise ValidationError({"sale_price": "Sale price cannot be negative."})

	@property
	def unit_cost(self):
		return self.product.cost_price if self.product and self.product.cost_price else Decimal("0.00")

	@property
	def line_cost(self):
		if self.quantity is None:
			return Decimal("0.00")
		return self.quantity * self.unit_cost

	@property
	def line_total(self):
		if self.quantity is None or self.sale_price is None:
			return Decimal("0.00")
		return self.quantity * self.sale_price

	@property
	def line_profit(self):
		return self.line_total - self.line_cost

	def __str__(self) -> str:
		return f"{self.product} x {self.quantity}"

# Create your models here.
