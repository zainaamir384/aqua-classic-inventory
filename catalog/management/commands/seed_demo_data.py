from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from catalog.models import Brand, Category, Product, ProductComponent
from inventory.models import Location
from inventory.services import get_default_location, record_movement
from suppliers.models import Supplier


class Command(BaseCommand):
    help = "Seed realistic Aqua Classic demo data."

    def handle(self, *args, **options):
        with transaction.atomic():
            owner, _ = User.objects.get_or_create(
                username="owner",
                defaults={
                    "email": "owner@aquaclassic.local",
                    "first_name": "Demo",
                    "last_name": "Owner",
                    "role": User.Role.OWNER,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            owner.set_password("owner1234")
            owner.save()

            staff, _ = User.objects.get_or_create(
                username="staff",
                defaults={
                    "email": "staff@aquaclassic.local",
                    "first_name": "Demo",
                    "last_name": "Staff",
                    "role": User.Role.STAFF,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            staff.set_password("staff1234")
            staff.save()


            categories = {}
            for name, description in [
                ("Basic Filter", "Domestic kitchen filters and housings."),
                ("RO Filter", "Domestic reverse osmosis finished units."),
                ("RO Parts", "RO spare parts and fittings."),
                ("Cartridges", "Filter cartridges and stages."),
                ("Alkaline/Add-on", "Alkaline, mineral, and post-carbon add-ons."),
            ]:
                categories[name], _ = Category.objects.get_or_create(name=name, defaults={"description": description})

            brands = {}
            for name, origin in [
                ("Local Workshop", "Local"),
                ("Generic Import", "Imported-Generic"),
                ("China Tier", "China"),
                ("Vietnam Premium", "Vietnam"),
            ]:
                brands[name], _ = Brand.objects.get_or_create(name=name, defaults={"origin_label": origin})

            location = get_default_location()
            supplier, _ = Supplier.objects.get_or_create(name="Aqua Supply House", defaults={"contact_person": "Nabil", "phone": "0800-111-222"})

            products = {}
            product_specs = [
                ("RO Vietnam 8-Stage Unit", categories["RO Filter"], brands["Vietnam Premium"], "N_A", 8, Product.UnitType.FINISHED_UNIT, "set", Decimal("120.00"), 5),
                ("RO China 6-Stage Unit", categories["RO Filter"], brands["China Tier"], "N_A", 6, Product.UnitType.FINISHED_UNIT, "set", Decimal("75.00"), 8),
                ("Domestic Dual Filter Housing", categories["Basic Filter"], brands["Local Workshop"], Product.Configuration.DUAL, 2, Product.UnitType.FINISHED_UNIT, "set", Decimal("35.00"), 6),
                ("PP Cartridge", categories["Cartridges"], brands["Local Workshop"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("3.00"), 25),
                ("CTO Cartridge", categories["Cartridges"], brands["Generic Import"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("4.50"), 20),
                ("RO Membrane", categories["RO Parts"], brands["Vietnam Premium"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("18.00"), 10),
                ("Membrane Housing", categories["RO Parts"], brands["Generic Import"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("9.00"), 10),
                ("Booster Pump", categories["RO Parts"], brands["China Tier"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("22.00"), 8),
                ("Elbow Fitting", categories["RO Parts"], brands["Generic Import"], "N_A", None, Product.UnitType.SPARE_PART, "piece", Decimal("0.35"), 100),
                ("High/Low Switch", categories["RO Parts"], brands["China Tier"], "N_A", None, Product.UnitType.SPARE_PART, "piece", Decimal("2.50"), 15),
                ("Post Carbon Cartridge", categories["Alkaline/Add-on"], brands["Generic Import"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("5.75"), 12),
                ("Mineral Cartridge", categories["Alkaline/Add-on"], brands["Vietnam Premium"], "N_A", None, Product.UnitType.COMPONENT, "piece", Decimal("6.25"), 12),
            ]

            for name, category, brand, configuration, stage_count, unit_type, uom, cost, stock_qty in product_specs:
                product, created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "category": category,
                        "brand": brand,
                        "configuration": configuration,
                        "stage_count": stage_count,
                        "unit_type": unit_type,
                        "unit_of_measure": uom,
                        "cost_price": cost,
                        "reorder_level": Decimal("5"),
                        "is_active": True,
                    },
                )
                products[name] = product
                if created and stock_qty:
                    record_movement(
                        product=product,
                        location=location,
                        movement_type="PURCHASE_IN",
                        quantity=Decimal(stock_qty),
                        created_by=owner,
                        reference_note="Demo seed stock",
                        unit_cost=cost,
                    )

            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["RO Membrane"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["Membrane Housing"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["Booster Pump"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["Elbow Fitting"], defaults={"quantity": Decimal("6")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["High/Low Switch"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["Post Carbon Cartridge"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO Vietnam 8-Stage Unit"], component=products["Mineral Cartridge"], defaults={"quantity": Decimal("1")})

            ProductComponent.objects.get_or_create(product=products["RO China 6-Stage Unit"], component=products["RO Membrane"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO China 6-Stage Unit"], component=products["Membrane Housing"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO China 6-Stage Unit"], component=products["Booster Pump"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["RO China 6-Stage Unit"], component=products["Elbow Fitting"], defaults={"quantity": Decimal("4")})
            ProductComponent.objects.get_or_create(product=products["RO China 6-Stage Unit"], component=products["High/Low Switch"], defaults={"quantity": Decimal("1")})

            ProductComponent.objects.get_or_create(product=products["Domestic Dual Filter Housing"], component=products["PP Cartridge"], defaults={"quantity": Decimal("1")})
            ProductComponent.objects.get_or_create(product=products["Domestic Dual Filter Housing"], component=products["CTO Cartridge"], defaults={"quantity": Decimal("1")})

            self.stdout.write(self.style.SUCCESS("Demo data created."))
