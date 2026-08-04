from decimal import Decimal

from django import forms
from django.db.models import Sum, Q, F
from django.db.models.functions import Coalesce

from catalog.models import Product, Category, ProductComponent
from .models import Location, StockMovement


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("name", "code", "address", "notes", "is_default", "is_active")


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ("product", "location", "movement_type", "quantity", "reference_note", "unit_cost")


class StockAwareModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        stock = getattr(obj, "calculated_stock", Decimal("0"))
        stock_int = int(stock)
        if stock_int > 0:
            return f"{obj.name} — ({stock_int} pcs in stock)"
        return f"{obj.name} — (0 pcs — OUT OF STOCK)"


class AssemblyForm(forms.Form):
    CONFIG_CHOICES = [
        ("", "— Select Configuration (Single / Dual / Triple) —"),
        ("Single", "Single"),
        ("Dual", "Dual"),
        ("Triple", "Triple"),
    ]

    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        label="Assembly Category",
        help_text="Choose 10 inch, Slim, Jumbo Water Filter, or RO System",
    )
    config_type = forms.ChoiceField(
        choices=CONFIG_CHOICES,
        required=False,
        label="Configuration Set (Water Filters Only)",
        help_text="Select Single, Dual, or Triple for Water Filters",
    )
    stage_count = forms.IntegerField(
        min_value=1,
        max_value=20,
        required=False,
        label="Filter Stage Number",
        help_text="Compulsory for RO Systems (e.g. 5, 6, 7, 8). Optional for Water Filters.",
    )

    # --- CATEGORIZED & STOCK-AWARE RAW COMPONENT SELECTION ---
    housing_item = StockAwareModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label="1. Housing / Jug Body Used",
        help_text="Select Housing/Jug from stock to deduct (e.g. 10 inch Taiwan Blue Housing, Local Housing)",
    )
    housing_qty_per_unit = forms.IntegerField(
        min_value=1,
        initial=3,
        required=False,
        label="Housings Used per Unit",
        help_text="Default is 3 for Triple, 2 for Dual, 1 for Single",
    )

    stage1_item = StockAwareModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label="2. Stage 1 PPF Cartridge Used",
        help_text="Select 1st stage PPF cartridge from stock (e.g. Hygenic 80g PPF, Axtron 130g PPF, 160g PPF)",
    )

    stage2_item = StockAwareModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label="3. Stage 2 CTO / Carbon Cartridge Used",
        help_text="Select 2nd stage CTO cartridge from stock (e.g. Penta Pure CTO, Local CTO)",
    )

    stage3_item = StockAwareModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label="4. Stage 3 PPF Cartridge Used (Optional)",
        help_text="Select 3rd stage PPF cartridge from stock (e.g. 130g PPF, 160g PPF)",
    )

    unit_name = forms.CharField(
        max_length=200,
        required=False,
        label="Assembled Product Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Triple 10 inch Filter (130g PPF + Penta Pure CTO)"}),
        help_text="Custom name for display stock. Leave blank to auto-generate from selected cartridges & set type.",
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantity Assembled",
        help_text="Number of finished units assembled to add to display stock",
    )
    cost_price = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        required=False,
        label="Cost Price per Unit (PKR)",
        help_text="Manufacturing cost per unit",
    )
    reference_note = forms.CharField(
        required=False,
        max_length=255,
        label="Assembly Notes / Build Details",
        help_text="Optional build reference notes",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            name__in=[
                '10" Water Filter (Assembled)',
                '20" Slim Water Filter (Assembled)',
                '20" Jumbo Water Filter (Assembled)',
                'RO Water Filter (Assembled)',
            ]
        ).order_by("name")

        # 1. Queryset for Housings ONLY (Annotated with stock quantity, in-stock items first, 0-stock at bottom)
        housing_qs = (
            Product.objects.filter(
                is_active=True,
                category__name__icontains="Housing"
            )
            .annotate(calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0")))
            .order_by("-calculated_stock", "name")
        )
        self.fields["housing_item"].queryset = housing_qs

        # Excluded non-cartridge fittings and tools
        EXCLUDED_FITTINGS = ["Connector", "T-Connector", "Fitting", "Wrench", "Valve", "Nozzle", "Pen", "T Cock", "Bracket"]

        # 2. Queryset for Stage 1 (PPF Cartridges ONLY)
        ppf_qs = (
            Product.objects.filter(is_active=True)
            .filter(Q(name__icontains="PPF") | Q(notes__icontains="PPF"))
            .exclude(unit_type=Product.UnitType.FINISHED_UNIT)
        )
        for kw in EXCLUDED_FITTINGS:
            ppf_qs = ppf_qs.exclude(name__icontains=kw)
        self.fields["stage1_item"].queryset = (
            ppf_qs.annotate(calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0")))
            .order_by("-calculated_stock", "name")
        )

        # 3. Queryset for Stage 2 (CTO Cartridges ONLY)
        cto_qs = (
            Product.objects.filter(is_active=True)
            .filter(name__icontains="CTO")
            .exclude(unit_type=Product.UnitType.FINISHED_UNIT)
        )
        for kw in EXCLUDED_FITTINGS:
            cto_qs = cto_qs.exclude(name__icontains=kw)
        self.fields["stage2_item"].queryset = (
            cto_qs.annotate(calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0")))
            .order_by("-calculated_stock", "name")
        )

        # 4. Queryset for Stage 3 (PPF Cartridges ONLY)
        self.fields["stage3_item"].queryset = (
            ppf_qs.annotate(calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0")))
            .order_by("-calculated_stock", "name")
        )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        stage_count = cleaned_data.get("stage_count")

        if category and "ro" in category.name.lower():
            if not stage_count:
                self.add_error("stage_count", "Filter Stage Number is COMPULSORY for RO Systems (e.g. 5, 6, 7, 8 Stage).")

        return cleaned_data
