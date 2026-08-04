from django import forms
from django.forms import inlineformset_factory

from catalog.models import Product

from .models import PurchaseOrder, PurchaseOrderLineItem, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("name", "contact_person", "phone", "address", "notes", "is_active")


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ("supplier", "expected_delivery_date", "status", "notes")


class PurchaseOrderLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLineItem
        fields = ("product", "ordered_boxes", "pieces_per_box", "ordered_qty", "received_qty", "unit_cost")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ordered_boxes"].required = False
        self.fields["pieces_per_box"].required = False
        self.fields["ordered_qty"].required = False

    def clean(self):
        cleaned_data = super().clean()
        ordered_boxes = cleaned_data.get("ordered_boxes")
        pieces_per_box = cleaned_data.get("pieces_per_box")
        ordered_qty = cleaned_data.get("ordered_qty")
        product = cleaned_data.get("product")

        # Auto-fill pieces_per_box from product if not provided
        if not pieces_per_box and product and product.pieces_per_box:
            pieces_per_box = product.pieces_per_box
            cleaned_data["pieces_per_box"] = pieces_per_box

        # Calculate ordered_qty from boxes if boxes are entered
        if ordered_boxes and pieces_per_box:
            cleaned_data["ordered_qty"] = ordered_boxes * pieces_per_box
        elif not ordered_qty:
            self.add_error(None, "Enter either Boxes + Pieces per Box, or Total Pieces directly.")

        return cleaned_data


PurchaseOrderLineItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderLineItem,
    form=PurchaseOrderLineItemForm,
    extra=1,
    can_delete=True,
)
