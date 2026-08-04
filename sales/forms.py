from django import forms
from django.forms import inlineformset_factory

from .models import SaleItem, SaleRecord


CUSTOMER_TYPE_CHOICES = [
    ("Customer", "Customer"),
    ("Salesman", "Salesman"),
]


class SaleRecordForm(forms.ModelForm):
    customer_name = forms.ChoiceField(
        choices=CUSTOMER_TYPE_CHOICES,
        label="Sold To",
        initial="Customer",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = SaleRecord
        fields = ("customer_name",)


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ("product", "quantity", "sale_price")


SaleItemFormSet = inlineformset_factory(SaleRecord, SaleItem, form=SaleItemForm, extra=1, can_delete=True)
