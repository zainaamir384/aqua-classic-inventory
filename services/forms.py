from django import forms
from .models import ServiceTicket


class ServiceTicketForm(forms.ModelForm):
    scheduled_time = forms.DateField(
        required=False,
        label="Scheduled Visit Date",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    class Meta:
        model = ServiceTicket
        fields = (
            "customer_name",
            "customer_phone",
            "customer_address",
            "service_type",
            "issue_description",
            "scheduled_time",
        )
        widgets = {
            "customer_address": forms.Textarea(attrs={"rows": 2}),
            "issue_description": forms.Textarea(attrs={"rows": 3}),
        }


class ServiceEditForm(forms.ModelForm):
    scheduled_time = forms.DateField(
        required=False,
        label="Scheduled Visit Date",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    class Meta:
        model = ServiceTicket
        fields = (
            "customer_name",
            "customer_phone",
            "customer_address",
            "serviceman_name",
            "service_type",
            "status",
            "issue_description",
            "scheduled_time",
            "parts_description",
            "parts_cost",
            "service_charges",
            "notes",
        )
        widgets = {
            "customer_address": forms.Textarea(attrs={"rows": 2}),
            "issue_description": forms.Textarea(attrs={"rows": 3}),
            "parts_description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class ServiceCompleteForm(forms.ModelForm):
    class Meta:
        model = ServiceTicket
        fields = (
            "serviceman_name",
            "parts_description",
            "parts_cost",
            "service_charges",
            "notes",
        )
        widgets = {
            "parts_description": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Parts replaced details..."}
            ),
            "notes": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Completion remarks..."}
            ),
        }
