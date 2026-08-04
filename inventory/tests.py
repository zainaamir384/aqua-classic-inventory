from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductComponent
from .models import Location, StockItem, StockMovement
from .services import InsufficientStockError, assemble_product, get_default_location, record_movement

User = get_user_model()


class StockMovementTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="tester", password="pass1234", role=User.Role.OWNER)
		self.location = Location.objects.create(name="Main Shop", code="MAIN", is_default=True)
		category = Category.objects.create(name="Parts")
		brand = Brand.objects.create(name="Generic", origin_label="Imported-Generic")
		self.product = Product.objects.create(
			name="RO Membrane",
			category=category,
			brand=brand,
			configuration=Product.Configuration.N_A,
			unit_type=Product.UnitType.COMPONENT,
			unit_of_measure="piece",
			cost_price=Decimal("12.50"),
			reorder_level=Decimal("5"),
		)

	def test_purchase_movement_increases_stock(self):
		record_movement(
			product=self.product,
			location=self.location,
			movement_type=StockMovement.MovementType.PURCHASE_IN,
			quantity=Decimal("4"),
			created_by=self.user,
		)
		stock = StockItem.objects.get(product=self.product, location=self.location)
		self.assertEqual(stock.quantity_on_hand, Decimal("4"))

	def test_negative_stock_is_blocked(self):
		with self.assertRaises(ValidationError):
			record_movement(
				product=self.product,
				location=self.location,
				movement_type=StockMovement.MovementType.SALE_OUT,
				quantity=Decimal("1"),
				created_by=self.user,
			)


class AssemblyTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="owner", password="pass1234", role=User.Role.OWNER)
		self.location = Location.objects.create(name="Main Shop", code="MAIN", is_default=True)
		category = Category.objects.create(name="RO Filters")
		parts = Category.objects.create(name="RO Parts")
		brand = Brand.objects.create(name="Vietnam Premium", origin_label="Vietnam")
		self.finished = Product.objects.create(
			name="RO Vietnam 8-Stage Unit",
			category=category,
			brand=brand,
			configuration=Product.Configuration.N_A,
			stage_count=8,
			unit_type=Product.UnitType.FINISHED_UNIT,
			unit_of_measure="set",
			cost_price=Decimal("120.00"),
			reorder_level=Decimal("2"),
		)
		self.membrane = Product.objects.create(
			name="RO Membrane",
			category=parts,
			brand=brand,
			configuration=Product.Configuration.N_A,
			unit_type=Product.UnitType.COMPONENT,
			unit_of_measure="piece",
			cost_price=Decimal("20.00"),
			reorder_level=Decimal("2"),
		)
		self.housing = Product.objects.create(
			name="Membrane Housing",
			category=parts,
			brand=brand,
			configuration=Product.Configuration.N_A,
			unit_type=Product.UnitType.COMPONENT,
			unit_of_measure="piece",
			cost_price=Decimal("10.00"),
			reorder_level=Decimal("2"),
		)
		ProductComponent.objects.create(product=self.finished, component=self.membrane, quantity=Decimal("1"))
		ProductComponent.objects.create(product=self.finished, component=self.housing, quantity=Decimal("1"))
		record_movement(
			product=self.membrane,
			location=self.location,
			movement_type=StockMovement.MovementType.PURCHASE_IN,
			quantity=Decimal("2"),
			created_by=self.user,
		)
		record_movement(
			product=self.housing,
			location=self.location,
			movement_type=StockMovement.MovementType.PURCHASE_IN,
			quantity=Decimal("2"),
			created_by=self.user,
		)

	def test_assemble_product_consumes_components_and_produces_finished_unit(self):
		assemble_product(product=self.finished, quantity=Decimal("1"), location=self.location, created_by=self.user)
		finished_stock = StockItem.objects.get(product=self.finished, location=self.location)
		membrane_stock = StockItem.objects.get(product=self.membrane, location=self.location)
		housing_stock = StockItem.objects.get(product=self.housing, location=self.location)
		self.assertEqual(finished_stock.quantity_on_hand, Decimal("1"))
		self.assertEqual(membrane_stock.quantity_on_hand, Decimal("1"))
		self.assertEqual(housing_stock.quantity_on_hand, Decimal("1"))

	def test_assemble_product_reports_shortages(self):
		with self.assertRaises(InsufficientStockError):
			assemble_product(product=self.finished, quantity=Decimal("3"), location=self.location, created_by=self.user)
