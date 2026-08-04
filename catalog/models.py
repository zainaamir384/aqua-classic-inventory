from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Brand(models.Model):
	name = models.CharField(max_length=120, unique=True)
	origin_label = models.CharField(max_length=120)
	notes = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return f"{self.name} ({self.origin_label})"


class Product(models.Model):
	class Configuration(models.TextChoices):
		SINGLE = "SINGLE", "Single"
		DUAL = "DUAL", "Dual"
		TRIPLE = "TRIPLE", "Triple"
		N_A = "N_A", "N/A"

	class UnitType(models.TextChoices):
		FINISHED_UNIT = "FINISHED_UNIT", "Finished Unit"
		COMPONENT = "COMPONENT", "Component"
		SPARE_PART = "SPARE_PART", "Spare Part"

	name = models.CharField(max_length=160)
	sku = models.CharField(max_length=64, unique=True, blank=True)
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
	brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
	configuration = models.CharField(max_length=20, choices=Configuration.choices, default=Configuration.N_A)
	stage_count = models.PositiveIntegerField(null=True, blank=True)
	unit_type = models.CharField(max_length=30, choices=UnitType.choices)
	unit_of_measure = models.CharField(max_length=40, default="piece")
	reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
	cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	notes = models.TextField(blank=True)
	pieces_per_box = models.PositiveIntegerField(null=True, blank=True, help_text="Number of pieces in one standard box. Leave blank if not applicable.")
	allow_negative_stock = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at", "-id"]

	def clean(self):
		errors = {}
		if self.stage_count is not None and self.stage_count <= 0:
			errors["stage_count"] = "Stage count must be a positive integer."
		if self.reorder_level < 0:
			errors["reorder_level"] = "Reorder level cannot be negative."
		if self.cost_price < 0:
			errors["cost_price"] = "Cost price cannot be negative."
		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		if not self.sku:
			self.sku = self.generate_sku()
		super().save(*args, **kwargs)

	def generate_sku(self) -> str:
		category_code = slugify(self.category.name).upper().replace("-", "")[:4] or "PRD"
		brand_code = "GEN"
		if self.brand:
			origin_source = self.brand.origin_label or self.brand.name
			brand_code = slugify(origin_source).upper().replace("-", "")[:3] or "GEN"
		stage_code = f"{self.stage_count}ST" if self.stage_count else "NOST"
		prefix = f"{category_code}-{brand_code}-{stage_code}"
		next_index = (
			Product.objects.filter(sku__startswith=prefix).count() + 1
		)
		return f"{prefix}-{next_index:03d}"

	def __str__(self) -> str:
		return f"{self.name} [{self.sku}]"


class ProductComponent(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bill_of_materials")
	component = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_products")
	quantity = models.DecimalField(max_digits=12, decimal_places=3)

	class Meta:
		unique_together = ("product", "component")
		ordering = ["product__name", "component__name"]

	def clean(self):
		errors = {}
		if self.product_id and self.component_id and self.product_id == self.component_id:
			errors["component"] = "A product cannot use itself as a component."
		if self.product_id and self.product.unit_type != Product.UnitType.FINISHED_UNIT:
			errors["product"] = "Bill of materials can only be defined for finished units."
		if self.component_id and self.component.unit_type == Product.UnitType.FINISHED_UNIT:
			errors["component"] = "Finished units should not be used as components."
		if self.quantity <= 0:
			errors["quantity"] = "Quantity must be greater than zero."
		if errors:
			raise ValidationError(errors)

	def __str__(self) -> str:
		return f"{self.product} -> {self.quantity} x {self.component}"

# Create your models here.
