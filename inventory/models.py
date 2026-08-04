from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F

from catalog.models import Product


User = get_user_model()


class Location(models.Model):
	name = models.CharField(max_length=120, unique=True)
	code = models.CharField(max_length=20, unique=True)
	address = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	is_default = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class StockItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_items")
	location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="stock_items")
	quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ("product", "location")
		ordering = ["product__name", "location__name"]

	def __str__(self) -> str:
		return f"{self.product} @ {self.location}: {self.quantity_on_hand}"

	@classmethod
	def rebuild_from_ledger(cls) -> None:
		from .models import StockMovement

		with transaction.atomic():
			cls.objects.all().update(quantity_on_hand=Decimal("0"))
			balances = {}
			for movement in StockMovement.objects.select_related("product", "location").order_by("created_at", "pk"):
				key = (movement.product_id, movement.location_id)
				delta = movement.signed_quantity
				balances[key] = balances.get(key, Decimal("0")) + delta
			for (product_id, location_id), quantity in balances.items():
				cls.objects.update_or_create(
					product_id=product_id,
					location_id=location_id,
					defaults={"quantity_on_hand": quantity},
				)


class StockMovement(models.Model):
	class MovementType(models.TextChoices):
		PURCHASE_IN = "PURCHASE_IN", "Purchase In"
		ASSEMBLY_CONSUME = "ASSEMBLY_CONSUME", "Assembly Consume"
		ASSEMBLY_PRODUCE = "ASSEMBLY_PRODUCE", "Assembly Produce"
		SALE_OUT = "SALE_OUT", "Sale Out"
		ADJUSTMENT_IN = "ADJUSTMENT_IN", "Adjustment In"
		ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Adjustment Out"
		RETURN_IN = "RETURN_IN", "Return In"
		DAMAGE_OUT = "DAMAGE_OUT", "Damage Out"

	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
	location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="stock_movements")
	movement_type = models.CharField(max_length=30, choices=MovementType.choices)
	quantity = models.DecimalField(max_digits=12, decimal_places=3)
	reference_note = models.CharField(max_length=255, blank=True)
	unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_stock_movements")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at", "-pk"]

	@property
	def signed_quantity(self) -> Decimal:
		if self.movement_type in {self.MovementType.PURCHASE_IN, self.MovementType.ASSEMBLY_PRODUCE, self.MovementType.ADJUSTMENT_IN, self.MovementType.RETURN_IN}:
			return self.quantity
		return self.quantity * Decimal("-1")

	def clean(self):
		errors = {}
		if self.quantity <= 0:
			errors["quantity"] = "Quantity must be greater than zero."
		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		if self.pk:
			raise ValidationError("Stock movements are append-only and cannot be edited.")
		self.full_clean()
		with transaction.atomic():
			stock_item, _ = StockItem.objects.select_for_update().get_or_create(
				product=self.product,
				location=self.location,
				defaults={"quantity_on_hand": Decimal("0")},
			)
			new_quantity = stock_item.quantity_on_hand + self.signed_quantity
			if new_quantity < 0:
				raise ValidationError(
					{
						"quantity": f"Insufficient stock for '{self.product.name}'. Current stock is {stock_item.quantity_on_hand} pcs. Stock cannot be less than 0."
					}
				)
			super().save(*args, **kwargs)
			stock_item.quantity_on_hand = new_quantity
			stock_item.save(update_fields=["quantity_on_hand", "updated_at"])

	def delete(self, *args, **kwargs):
		raise ValidationError("Stock movements are append-only and cannot be deleted.")

	def __str__(self) -> str:
		return f"{self.product} {self.movement_type} {self.quantity} @ {self.location}"

# Create your models here.
