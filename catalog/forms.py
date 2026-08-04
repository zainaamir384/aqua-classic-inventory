from django import forms

from .models import Brand, Category, Product, ProductComponent


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "is_active")


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ("name", "origin_label", "notes", "is_active")


class ProductForm(forms.ModelForm):
    brand_input = forms.CharField(
        max_length=120,
        required=False,
        label="Brand Name",
        help_text="Type brand name (e.g. Local, Aqua Safe, China). If new, it will be added automatically.",
    )
    new_category_name = forms.CharField(
        max_length=120,
        required=False,
        label="Or Add New Category",
        help_text="Leave blank to use selected category above.",
    )
    initial_boxes = forms.IntegerField(
        required=False,
        min_value=0,
        label="Number of Boxes",
        help_text="Number of boxes of this item.",
    )
    initial_stock = forms.DecimalField(
        required=False,
        min_value=0,
        label="Stock (Total Pieces)",
        help_text="Total pieces. Auto-calculated if Number of Boxes is entered.",
    )
    stage_count = forms.IntegerField(
        required=False,
        min_value=1,
        label="Stage Count (Assembled Filters / RO Only)",
        help_text="Number of stages e.g. 1, 2, 3 for water filters, or 6, 7, 8 for RO systems.",
    )

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "brand_input",
            "new_category_name",
            "stage_count",
            "cost_price",
            "initial_boxes",
            "pieces_per_box",
            "initial_stock",
            "is_active",
            "notes",
        )
        labels = {
            "pieces_per_box": "Number of Items in a Box",
            "cost_price": "Purchase Cost Price (per piece)",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        if self.instance and self.instance.pk and self.instance.brand:
            self.fields["brand_input"].initial = self.instance.brand.name

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        new_category_name = cleaned_data.get("new_category_name", "").strip()

        if new_category_name:
            cat, _ = Category.objects.get_or_create(
                name=new_category_name,
                defaults={"description": "User created category", "is_active": True},
            )
            cleaned_data["category"] = cat
        elif not category:
            self.add_error("category", "Please select a category or type a new category name.")

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        brand_name = self.cleaned_data.get("brand_input", "").strip()
        if brand_name:
            brand, _ = Brand.objects.get_or_create(
                name=brand_name,
                defaults={"origin_label": brand_name, "is_active": True},
            )
            product.brand = brand
        else:
            product.brand = None

        stage_count = self.cleaned_data.get("stage_count")
        if stage_count:
            product.stage_count = stage_count

        cat_name = product.category.name.lower() if product.category else ""
        if "assembled" in cat_name or "system" in cat_name:
            product.unit_type = Product.UnitType.FINISHED_UNIT
        elif not product.unit_type:
            product.unit_type = Product.UnitType.COMPONENT

        if commit:
            product.save()

            initial_boxes = self.cleaned_data.get("initial_boxes")
            pieces_per_box = self.cleaned_data.get("pieces_per_box")
            initial_stock = self.cleaned_data.get("initial_stock")

            total_qty = 0
            if initial_boxes and pieces_per_box:
                total_qty = initial_boxes * pieces_per_box
            elif initial_stock:
                total_qty = initial_stock

            if total_qty > 0:
                from accounts.models import User
                from inventory.models import StockMovement
                from inventory.services import get_default_location, record_movement

                creator = self.user
                if not creator or not getattr(creator, "is_authenticated", False):
                    creator = User.objects.filter(is_superuser=True).first() or User.objects.first()

                location = get_default_location()
                record_movement(
                    product=product,
                    location=location,
                    movement_type=StockMovement.MovementType.PURCHASE_IN,
                    quantity=total_qty,
                    created_by=creator,
                    reference_note="Initial product creation stock entry",
                    unit_cost=product.cost_price,
                )

        return product


class ProductComponentForm(forms.ModelForm):
    class Meta:
        model = ProductComponent
        fields = ("product", "component", "quantity")
