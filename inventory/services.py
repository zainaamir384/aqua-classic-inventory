from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import Product, ProductComponent

from .models import Location, StockItem, StockMovement


class InsufficientStockError(ValidationError):
    pass


def get_default_location() -> Location:
    location = Location.objects.filter(is_default=True, is_active=True).first()
    if location:
        return location
    return Location.objects.create(name="Main Shop", code="MAIN", is_default=True)


def record_movement(*, product: Product, location: Location, movement_type: str, quantity: Decimal, created_by, reference_note: str = "", unit_cost=None) -> StockMovement:
    return StockMovement.objects.create(
        product=product,
        location=location,
        movement_type=movement_type,
        quantity=quantity,
        reference_note=reference_note,
        unit_cost=unit_cost,
        created_by=created_by,
    )


def validate_assembly_stock(product: Product, quantity: Decimal, location: Location) -> dict[str, Decimal]:
    shortages: dict[str, Decimal] = {}
    for bom_line in product.bill_of_materials.select_related("component"):
        required = bom_line.quantity * quantity
        stock_item = StockItem.objects.filter(product=bom_line.component, location=location).first()
        available = stock_item.quantity_on_hand if stock_item else Decimal("0")
        if available < required:
            shortages[bom_line.component.name] = required - available
    return shortages


def assemble_product(*, product: Product, quantity: Decimal, location: Location, created_by, reference_note: str = ""):
    if product.unit_type != Product.UnitType.FINISHED_UNIT:
        raise ValidationError("Only finished-unit products can be assembled.")

    shortages = validate_assembly_stock(product, quantity, location)
    if shortages:
        raise InsufficientStockError(shortages)

    with transaction.atomic():
        for bom_line in product.bill_of_materials.select_related("component"):
            required = bom_line.quantity * quantity
            record_movement(
                product=bom_line.component,
                location=location,
                movement_type=StockMovement.MovementType.ASSEMBLY_CONSUME,
                quantity=required,
                created_by=created_by,
                reference_note=f"Assembly consume for {product.sku}. {reference_note}".strip(),
            )
        record_movement(
            product=product,
            location=location,
            movement_type=StockMovement.MovementType.ASSEMBLY_PRODUCE,
            quantity=quantity,
            created_by=created_by,
            reference_note=f"Assembly produce for {product.sku}. {reference_note}".strip(),
        )


def record_sale(*, product: Product, quantity: Decimal, location: Location, created_by, reference_note: str = "", unit_cost=None):
    return record_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.SALE_OUT,
        quantity=quantity,
        created_by=created_by,
        reference_note=reference_note,
        unit_cost=unit_cost,
    )