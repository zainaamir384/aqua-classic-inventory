from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from catalog.models import Brand, Category, Product, ProductComponent
from inventory.models import Location
from inventory.services import record_movement


class Command(BaseCommand):
    help = "Seed complete master catalog data for Aqua Classic Water Filters."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.MIGRATE_HEADING("Creating Default User & Locations..."))
            
            # Ensure owner user exists
            owner, _ = User.objects.get_or_create(
                username="owner",
                defaults={
                    "email": "owner@aquaclassic.local",
                    "first_name": "Shop",
                    "last_name": "Owner",
                    "role": User.Role.OWNER,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if owner.pk and not owner.check_password("owner1234"):
                owner.set_password("owner1234")
                owner.save()

            # Ensure Locations exist
            storage_loc, _ = Location.objects.get_or_create(
                code="STORAGE",
                defaults={
                    "name": "Storage Room",
                    "address": "Main Storage Facility",
                    "is_default": True,
                    "is_active": True,
                },
            )
            display_loc, _ = Location.objects.get_or_create(
                code="DISPLAY",
                defaults={
                    "name": "Shop Display",
                    "address": "Front Shop Floor",
                    "is_default": False,
                    "is_active": True,
                },
            )

            self.stdout.write(self.style.MIGRATE_HEADING("Creating Categories & Brands..."))

            # Categories
            categories = {}
            category_data = [
                ("Cartridges 10 inch", "10-inch standard PPF, CTO, UDF cartridges."),
                ("Cartridges 20 inch Slim", "20-inch slim PPF, CTO, UDF cartridges."),
                ("Cartridges 20 inch Jumbo", "20-inch jumbo PPF, CTO cartridges."),
                ("Housings 10 inch", "10-inch filter housings, heads, and standard wrenches."),
                ("Housings 20 inch Slim", "20-inch slim filter housings and slim wrenches."),
                ("Housings 20 inch Jumbo", "20-inch jumbo filter housings and jumbo wrenches."),
                ("RO Housings", "Membrane housings, RO casing, and RO housing wrenches."),
                ("RO Filters", "Membrane, Post Carbon, Alkaline, Mineral, Nano Silver, UV sterilizer filters."),
                ("RO Cartridges", "PPF, CTO, UDF cartridges for RO."),
                ("RO Accessories", "Pipes, faucets, tanks, clips."),
                ("RO Parts & Electricals", "Valves, spare pipes, outlet faucets, high/low pressure switches, booster pumps, adapters."),
                ("10\" Water Filter (Assembled)", "Assembled 10-inch Single, Dual, and Triple water filter units."),
                ("20\" Slim Water Filter (Assembled)", "Assembled 20-inch Slim Single, Dual, and Triple water filter units."),
                ("20\" Jumbo Water Filter (Assembled)", "Assembled 20-inch Jumbo Single, Dual, and Triple water filter units."),
                ("RO Water Filter (Assembled)", "Complete 5, 6, 7, 8 stage wall-mount and standing RO plants."),
            ]
            for cat_name, desc in category_data:
                cat, _ = Category.objects.get_or_create(name=cat_name, defaults={"description": desc, "is_active": True})
                categories[cat_name] = cat

            # Ensure official 4 assembled categories exist
            cat_10, _ = Category.objects.get_or_create(name="10\" Water Filter (Assembled)", defaults={"description": "Assembled 10-inch Single, Dual, and Triple filter units", "is_active": True})
            cat_slim, _ = Category.objects.get_or_create(name="20\" Slim Water Filter (Assembled)", defaults={"description": "Assembled 20-inch Slim Single, Dual, and Triple filter units", "is_active": True})
            cat_jumbo, _ = Category.objects.get_or_create(name="20\" Jumbo Water Filter (Assembled)", defaults={"description": "Assembled 20-inch Jumbo Single, Dual, and Triple filter units", "is_active": True})
            cat_ro, _ = Category.objects.get_or_create(name="RO Water Filter (Assembled)", defaults={"description": "Complete 5, 6, 7, 8 stage wall-mount and standing RO plants", "is_active": True})

            categories["10\" Water Filter (Assembled)"] = cat_10
            categories["20\" Slim Water Filter (Assembled)"] = cat_slim
            categories["20\" Jumbo Water Filter (Assembled)"] = cat_jumbo
            categories["RO Water Filter (Assembled)"] = cat_ro

            # Reassign any products from legacy category names
            old_cats = Category.objects.filter(name__in=["Water Filters (Assembled)", "RO Systems (Assembled)", "Slim Water Filter (Assembled)", "Jumbo Water Filter (Assembled)", "10 inch Water Filter (Assembled)"])
            for p in Product.objects.filter(category__in=old_cats):
                p_name = p.name.lower()
                if "ro" in p_name:
                    p.category = cat_ro
                elif "slim" in p_name:
                    p.category = cat_slim
                elif "jumbo" in p_name:
                    p.category = cat_jumbo
                else:
                    p.category = cat_10
                p.save(update_fields=["category"])

            # Safely delete unused legacy category names now that products are moved
            Category.objects.filter(name__in=["Water Filters (Assembled)", "RO Systems (Assembled)", "Slim Water Filter (Assembled)", "Jumbo Water Filter (Assembled)", "10 inch Water Filter (Assembled)"]).delete()

            # Brands
            brands = {}
            brand_data = [
                ("Local", "Local / Pakistan"),
                ("Imported", "Imported / China / Vietnam"),
                ("Aqua Classic Gold", "Premium Brand"),
            ]
            for b_name, origin in brand_data:
                b, _ = Brand.objects.get_or_create(name=b_name, defaults={"origin_label": origin, "is_active": True})
                brands[b_name] = b

            self.stdout.write(self.style.MIGRATE_HEADING("Creating Products & Components..."))

            products = {}

            def create_prod(name, sku, cat_name, brand_name, config, stages, unit_type, uom, reorder, cost, ppb=None, notes=""):
                prod, _ = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "name": name,
                        "category": categories[cat_name],
                        "brand": brands.get(brand_name),
                        "configuration": config,
                        "stage_count": stages,
                        "unit_type": unit_type,
                        "unit_of_measure": uom,
                        "reorder_level": Decimal(str(reorder)),
                        "cost_price": Decimal(str(cost)),
                        "pieces_per_box": ppb,
                        "notes": notes,
                        "is_active": True,
                    },
                )
                products[sku] = prod
                return prod

            # 1. Cartridges 10 inch
            create_prod("PPF 10\" 80g (Local)", "PPF-10-80G-LOC", "Cartridges 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "1.50", 50)
            create_prod("PPF 10\" 100g (Local)", "PPF-10-100G-LOC", "Cartridges 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "2.00", 50)
            create_prod("PPF 10\" 130g (Local)", "PPF-10-130G-LOC", "Cartridges 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "2.50", 50)
            create_prod("PPF 10\" 160g (Local)", "PPF-10-160G-LOC", "Cartridges 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "3.00", 50)
            create_prod("PPF 10\" 100g (Imported)", "PPF-10-100G-IMP", "Cartridges 10 inch", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "2.50", 50)
            create_prod("PPF 10\" 160g (Imported)", "PPF-10-160G-IMP", "Cartridges 10 inch", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "3.50", 50)
            create_prod("CTO 10\" (Local)", "CTO-10-LOC", "Cartridges 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "3.50", 50)
            create_prod("CTO 10\" (Imported)", "CTO-10-IMP", "Cartridges 10 inch", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "4.50", 50)

            # 2. RO Cartridges & Specialty Filters
            create_prod("UDF 10\" (Local) - RO Only", "UDF-10-LOC", "RO Cartridges", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "4.00", 50, "For RO Systems ONLY")
            create_prod("UDF 10\" (Imported) - RO Only", "UDF-10-IMP", "RO Cartridges", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 50, "5.00", 50, "For RO Systems ONLY")
            create_prod("Nano Silver Anti-Bacterial Filter", "INL-NANO-SILVER", "RO Filters", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 15, "6.50", 25)
            create_prod("Alkaline Filter (Red)", "INL-ALKALINE-RED", "RO Filters", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 15, "7.00", 25)
            create_prod("Post Carbon Filter T33 (White)", "INL-POST-CARBON-T33", "RO Filters", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 20, "4.50", 25)
            create_prod("Mineral Filter (Yellow)", "INL-MINERAL-YLW", "RO Filters", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 15, "6.00", 25)
            create_prod("UV Sterilizer Unit (Standalone)", "INL-UV-STERILIZER", "RO Filters", "Imported", "N_A", None, Product.UnitType.COMPONENT, "unit", 5, "25.00", 10, "Standalone UV Sterilizer")

            # 3. Cartridges 20 inch Slim
            create_prod("PPF 20\" Slim (Local)", "PPF-20S-LOC", "Cartridges 20 inch Slim", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 25, "5.00", 25)
            create_prod("CTO 20\" Slim (Local)", "CTO-20S-LOC", "Cartridges 20 inch Slim", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 25, "7.00", 25)
            create_prod("UDF 20\" Slim (Local)", "UDF-20S-LOC", "Cartridges 20 inch Slim", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 25, "8.00", 25)

            # 4. Cartridges 20 inch Jumbo
            create_prod("PPF 20\" Jumbo (Imported)", "PPF-20J-IMP", "Cartridges 20 inch Jumbo", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 20, "12.00", 50)
            create_prod("CTO 20\" Jumbo (Imported)", "CTO-20J-IMP", "Cartridges 20 inch Jumbo", "Imported", "N_A", None, Product.UnitType.COMPONENT, "piece", 20, "16.00", 50)

            # 5. RO Accessories & Housings with exact Wrenches
            create_prod("Transparent Blue Housing 10\"", "HSG-10-TRANS-BLU", "Housings 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 24, "8.00", 6)
            create_prod("White Opaque Housing 10\"", "HSG-10-WHT-OPQ", "Housings 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 24, "7.50", 6)
            create_prod("All-Opaque Housing 10\" (Water Cooler)", "HSG-10-COOLER-OPQ", "Housings 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 12, "8.50", 6, "Specially for Water Coolers")
            create_prod("Standard Housing Head 10\"", "HEAD-10-STD", "Housings 10 inch", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 24, "3.00", 6)
            create_prod("Single Filter Plate (Wall)", "PLT-SNGL-WALL", "RO Accessories", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 20, "2.50", 20)
            create_prod("Dual Filter Plate (Wall)", "PLT-DUAL-WALL", "RO Accessories", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 15, "4.00", 15)
            create_prod("Triple Filter Plate (Wall)", "PLT-TRPL-WALL", "RO Accessories", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 15, "5.50", 15)
            create_prod("Standard RO Wall Bracket", "PLT-RO-WALL-BRK", "RO Accessories", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 10, "8.00", 10)
            create_prod("Heavy-Duty Stand RO Frame (Yellow/Metal)", "FRM-RO-HEAVY-STAND", "RO Accessories", "Local", "N_A", None, Product.UnitType.COMPONENT, "piece", 5, "18.00", 5, "Heavy-duty standing frame for RO systems")
            create_prod("Elbow Fitting 1/4\"", "SP-FTG-ELBOW-14", "RO Parts & Electricals", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 100, "0.40", 100)
            create_prod("T-Connector 1/4\"", "SP-FTG-TEE-14", "RO Parts & Electricals", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 100, "0.50", 100)
            create_prod("Ball Valve 1/4\"", "SP-VLV-BALL-14", "RO Parts & Electricals", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 50, "1.20", 50)
            create_prod("RO Tubing 1/4\" (Meter)", "SP-TBG-14-MTR", "RO Accessories", "Local", "N_A", None, Product.UnitType.SPARE_PART, "meter", 100, "0.30", 100)
            create_prod("10\" Standard Housing Wrench", "WRN-10-STD", "Housings 10 inch", "Local", "N_A", None, Product.UnitType.SPARE_PART, "piece", 20, "1.50", 50, "Wrench for 10 inch standard filter housing")
            create_prod("20\" Slim Housing Wrench", "WRN-20S-SLIM", "Housings 20 inch Slim", "Local", "N_A", None, Product.UnitType.SPARE_PART, "piece", 20, "2.50", 50, "Wrench for 20 inch slim filter housing")
            create_prod("20\" Jumbo Housing Wrench", "WRN-20J-JUMBO", "Housings 20 inch Jumbo", "Local", "N_A", None, Product.UnitType.SPARE_PART, "piece", 20, "4.00", 50, "Wrench for 20 inch jumbo filter housing")
            create_prod("RO Housing Wrench", "WRN-RO-HSG", "RO Housings", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 30, "1.50", 30, "Wrench for RO membrane vessel & RO housing")
            create_prod("RO Faucet / Tap (Chrome)", "SP-ACC-FAUCET-CHR", "RO Accessories", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 15, "8.50", 15)

            # 6. RO Electricals & Parts
            create_prod("Diaphragm Booster Pump (24V)", "SP-RO-PUMP-24V", "RO Parts & Electricals", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 10, "24.00", 1)
            create_prod("Pressure Gauge", "SP-ACC-PRESS-GAUGE", "RO Parts & Electricals", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 10, "5.00", 10)
            create_prod("RO Membrane Housing", "SP-RO-MEMB-HSG", "RO Housings", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 15, "6.00", 1)
            create_prod("RO Membrane 75 GPD", "SP-RO-MEMB-75G", "RO Filters", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 20, "14.00", 1)
            create_prod("RO Storage Tank 4 Gallon", "TNK-RO-4G", "RO Accessories", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 10, "22.00", 1)
            create_prod("RO Storage Tank 5 Gallon", "TNK-RO-5G", "RO Accessories", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 8, "26.00", 1)
            create_prod("RO Storage Tank 6 Gallon", "TNK-RO-6G", "RO Accessories", "Imported", "N_A", None, Product.UnitType.SPARE_PART, "piece", 5, "30.00", 1)

            # 7. Assembled Finished Units under 4 Official Categories
            s_fltr = create_prod("Single 10\" Water Filter (Local)", "UNT-FLTR-SNGL-LOC", "10\" Water Filter (Assembled)", "Local", Product.Configuration.SINGLE, 1, Product.UnitType.FINISHED_UNIT, "set", 5, "15.00")
            d_fltr = create_prod("Dual 10\" Water Filter (Local)", "UNT-FLTR-DUAL-LOC", "10\" Water Filter (Assembled)", "Local", Product.Configuration.DUAL, 2, Product.UnitType.FINISHED_UNIT, "set", 5, "24.00")
            t_fltr = create_prod("Triple 10\" Water Filter (Local)", "UNT-FLTR-TRPL-LOC", "10\" Water Filter (Assembled)", "Local", Product.Configuration.TRIPLE, 3, Product.UnitType.FINISHED_UNIT, "set", 5, "34.00")

            ro6 = create_prod("RO System 6-Stage (Wall Mount)", "UNT-RO-6STG-WALL", "RO Water Filter (Assembled)", "Aqua Classic Gold", Product.Configuration.TRIPLE, 6, Product.UnitType.FINISHED_UNIT, "set", 3, "95.00")
            ro7 = create_prod("RO System 7-Stage with Alkaline", "UNT-RO-7STG-ALK", "RO Water Filter (Assembled)", "Aqua Classic Gold", Product.Configuration.TRIPLE, 7, Product.UnitType.FINISHED_UNIT, "set", 3, "108.00")
            ro8_stand = create_prod("Heavy-Duty Stand RO System 8-Stage", "UNT-RO-8STG-STAND", "RO Water Filter (Assembled)", "Aqua Classic Gold", Product.Configuration.TRIPLE, 8, Product.UnitType.FINISHED_UNIT, "set", 2, "135.00", notes="Standing Heavy Duty RO Unit")

            self.stdout.write(self.style.MIGRATE_HEADING("Creating Bill of Materials (BOM)..."))

            def add_bom(parent, comp, qty):
                ProductComponent.objects.get_or_create(
                    product=parent,
                    component=comp,
                    defaults={"quantity": Decimal(str(qty))},
                )

            # Single Filter BOM
            add_bom(s_fltr, products["HSG-10-TRANS-BLU"], 1)
            add_bom(s_fltr, products["HEAD-10-STD"], 1)
            add_bom(s_fltr, products["PPF-10-100G-LOC"], 1)
            add_bom(s_fltr, products["PLT-SNGL-WALL"], 1)

            # Dual Filter BOM
            add_bom(d_fltr, products["HSG-10-TRANS-BLU"], 2)
            add_bom(d_fltr, products["HEAD-10-STD"], 2)
            add_bom(d_fltr, products["PPF-10-100G-LOC"], 1)
            add_bom(d_fltr, products["CTO-10-LOC"], 1)
            add_bom(d_fltr, products["PLT-DUAL-WALL"], 1)

            # Triple Filter BOM (STRICT: 2 PPF + 1 CTO + 1 Triple Plate — NO UDF!)
            add_bom(t_fltr, products["HSG-10-TRANS-BLU"], 3)
            add_bom(t_fltr, products["HEAD-10-STD"], 3)
            add_bom(t_fltr, products["PPF-10-100G-LOC"], 2)
            add_bom(t_fltr, products["CTO-10-LOC"], 1)
            add_bom(t_fltr, products["PLT-TRPL-WALL"], 1)

            # 6-Stage RO System BOM (UDF used here)
            add_bom(ro6, products["HSG-10-WHT-OPQ"], 2)
            add_bom(ro6, products["HSG-10-TRANS-BLU"], 1)
            add_bom(ro6, products["HEAD-10-STD"], 3)
            add_bom(ro6, products["PPF-10-100G-LOC"], 1)
            add_bom(ro6, products["CTO-10-LOC"], 1)
            add_bom(ro6, products["UDF-10-LOC"], 1)
            add_bom(ro6, products["SP-RO-MEMB-75G"], 1)
            add_bom(ro6, products["SP-RO-MEMB-HSG"], 1)
            add_bom(ro6, products["INL-POST-CARBON-T33"], 1)
            add_bom(ro6, products["SP-RO-PUMP-24V"], 1)
            add_bom(ro6, products["TNK-RO-4G"], 1)
            add_bom(ro6, products["PLT-RO-WALL-BRK"], 1)

            # 7-Stage RO System BOM
            add_bom(ro7, products["HSG-10-WHT-OPQ"], 2)
            add_bom(ro7, products["HSG-10-TRANS-BLU"], 1)
            add_bom(ro7, products["HEAD-10-STD"], 3)
            add_bom(ro7, products["PPF-10-100G-LOC"], 1)
            add_bom(ro7, products["CTO-10-LOC"], 1)
            add_bom(ro7, products["UDF-10-LOC"], 1)
            add_bom(ro7, products["SP-RO-MEMB-75G"], 1)
            add_bom(ro7, products["SP-RO-MEMB-HSG"], 1)
            add_bom(ro7, products["INL-POST-CARBON-T33"], 1)
            add_bom(ro7, products["INL-ALKALINE-RED"], 1)
            add_bom(ro7, products["SP-RO-PUMP-24V"], 1)
            add_bom(ro7, products["TNK-RO-4G"], 1)
            add_bom(ro7, products["PLT-RO-WALL-BRK"], 1)

            # 8-Stage Stand RO System BOM
            add_bom(ro8_stand, products["HSG-10-WHT-OPQ"], 2)
            add_bom(ro8_stand, products["HSG-10-TRANS-BLU"], 1)
            add_bom(ro8_stand, products["HEAD-10-STD"], 3)
            add_bom(ro8_stand, products["PPF-10-100G-LOC"], 1)
            add_bom(ro8_stand, products["CTO-10-LOC"], 1)
            add_bom(ro8_stand, products["UDF-10-LOC"], 1)
            add_bom(ro8_stand, products["SP-RO-MEMB-75G"], 1)
            add_bom(ro8_stand, products["SP-RO-MEMB-HSG"], 1)
            add_bom(ro8_stand, products["INL-POST-CARBON-T33"], 1)
            add_bom(ro8_stand, products["INL-ALKALINE-RED"], 1)
            add_bom(ro8_stand, products["INL-MINERAL-YLW"], 1)
            add_bom(ro8_stand, products["SP-RO-PUMP-24V"], 1)
            add_bom(ro8_stand, products["TNK-RO-5G"], 1)
            add_bom(ro8_stand, products["FRM-RO-HEAVY-STAND"], 1)
            add_bom(ro8_stand, products["SP-ACC-PRESS-GAUGE"], 1)

            self.stdout.write(self.style.MIGRATE_HEADING("Seeding Initial Inventory Stock in Storage Room..."))

            # Seed initial stock for raw components in Storage Room
            for prod in Product.objects.filter(unit_type__in=[Product.UnitType.COMPONENT, Product.UnitType.SPARE_PART]):
                record_movement(
                    product=prod,
                    location=storage_loc,
                    movement_type="PURCHASE_IN",
                    quantity=Decimal("100"),
                    created_by=owner,
                    reference_note="Initial master catalog seed stock",
                    unit_cost=prod.cost_price,
                )

            self.stdout.write(self.style.SUCCESS("Aqua Classic master catalog setup completed successfully!"))
