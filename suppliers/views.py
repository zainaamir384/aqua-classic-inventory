from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from accounts.mixins import OwnerRequiredMixin
from config.ui import build_detail_rows, build_table_rows
from inventory.services import get_default_location, record_movement
from inventory.models import StockMovement

from .forms import PurchaseOrderForm, PurchaseOrderLineItemFormSet, SupplierForm
from .models import PurchaseOrder, PurchaseOrderLineItem, Supplier


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = "generic/list.html"
    columns = [
        {"label": "Name", "lookup": "name"},
        {"label": "Contact", "lookup": "contact_person"},
        {"label": "Phone", "lookup": "phone"},
        {"label": "Active", "lookup": "is_active"},
    ]
    create_url = reverse_lazy("suppliers:supplier-add")
    detail_url_name = "suppliers:supplier-edit"
    edit_url_name = "suppliers:supplier-edit"
    delete_url_name = "suppliers:supplier-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Suppliers"
        context["columns"] = self.columns
        can_manage = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["rows"] = [
            {
                "object": supplier,
                "values": [supplier.name, supplier.contact_person, supplier.phone, supplier.is_active],
                "object_url": reverse("suppliers:supplier-edit", kwargs={"pk": supplier.pk}),
                "edit_url": reverse("suppliers:supplier-edit", kwargs={"pk": supplier.pk}) if can_manage else None,
                "delete_url": reverse("suppliers:supplier-delete", kwargs={"pk": supplier.pk}) if can_manage else None,
            }
            for supplier in context["object_list"]
        ]
        context["create_url"] = self.create_url if can_manage else None
        return context


class SupplierCreateView(OwnerRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "generic/form.html"
    success_url = reverse_lazy("suppliers:supplier-list")
    page_title = "Add Supplier"

    def form_valid(self, form):
        messages.success(self.request, "Supplier created.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class SupplierUpdateView(SupplierCreateView, UpdateView):
    page_title = "Edit Supplier"


class SupplierDeleteView(OwnerRequiredMixin, DeleteView):
    model = Supplier
    template_name = "generic/confirm_delete.html"
    success_url = reverse_lazy("suppliers:supplier-list")
    page_title = "Delete Supplier"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = "generic/list.html"
    columns = [
        {"label": "ID", "lookup": "id"},
        {"label": "Supplier", "lookup": "supplier"},
        {"label": "Status", "lookup": "status"},
        {"label": "Order Date", "lookup": "order_date"},
        {"label": "Created By", "lookup": "created_by"},
    ]
    create_url = reverse_lazy("suppliers:po-add")
    detail_url_name = "suppliers:po-detail"
    edit_url_name = "suppliers:po-edit"
    delete_url_name = "suppliers:po-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Orders"
        context["columns"] = self.columns
        can_manage = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["rows"] = [
            {
                "object": purchase_order,
                "values": [purchase_order.id, purchase_order.supplier, purchase_order.status, purchase_order.order_date, purchase_order.created_by],
                "object_url": reverse("suppliers:po-detail", kwargs={"pk": purchase_order.pk}),
                "edit_url": reverse("suppliers:po-edit", kwargs={"pk": purchase_order.pk}) if can_manage else None,
                "delete_url": reverse("suppliers:po-delete", kwargs={"pk": purchase_order.pk}) if can_manage else None,
            }
            for purchase_order in context["object_list"]
        ]
        return context


class PurchaseOrderFormMixin:
    template_name = "suppliers/purchase_order_form.html"
    success_url = reverse_lazy("suppliers:po-list")
    page_title = "Purchase Order"

    def get_formset(self):
        return PurchaseOrderLineItemFormSet(self.request.POST or None, instance=getattr(self, "object", None))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        context.setdefault("formset", self.get_formset())
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context["formset"]
        if not formset.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save(commit=False)
            if not self.object.pk:
                self.object.created_by = self.request.user
            self.object.save()
            formset.instance = self.object
            formset.save()
        messages.success(self.request, "Purchase order saved.")
        return redirect(self.success_url)


class PurchaseOrderCreateView(OwnerRequiredMixin, PurchaseOrderFormMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    page_title = "Add Purchase Order"


class PurchaseOrderUpdateView(OwnerRequiredMixin, PurchaseOrderFormMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    page_title = "Edit Purchase Order"


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = "suppliers/purchase_order_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"PO #{self.object.pk}"
        context["line_items"] = self.object.line_items.select_related("product")
        context["receive_url"] = reverse_lazy("suppliers:po-receive", kwargs={"pk": self.object.pk})
        context["edit_url"] = reverse_lazy("suppliers:po-edit", kwargs={"pk": self.object.pk})
        context["delete_url"] = reverse_lazy("suppliers:po-delete", kwargs={"pk": self.object.pk})
        context["details"] = build_detail_rows(
            self.object,
            [
                {"label": "Supplier", "lookup": "supplier"},
                {"label": "Status", "lookup": "status"},
                {"label": "Order Date", "lookup": "order_date"},
                {"label": "Expected Delivery", "lookup": "expected_delivery_date"},
                {"label": "Notes", "lookup": "notes"},
            ],
        )
        return context


class PurchaseOrderDeleteView(OwnerRequiredMixin, DeleteView):
    model = PurchaseOrder
    template_name = "generic/confirm_delete.html"
    success_url = reverse_lazy("suppliers:po-list")
    page_title = "Delete Purchase Order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class PurchaseOrderReceiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        purchase_order = get_object_or_404(PurchaseOrder.objects.prefetch_related("line_items__product"), pk=pk)
        location = get_default_location()
        with transaction.atomic():
            for line_item in purchase_order.line_items.all():
                remaining = line_item.outstanding_qty
                if remaining > 0:
                    record_movement(
                        product=line_item.product,
                        location=location,
                        movement_type=StockMovement.MovementType.PURCHASE_IN,
                        quantity=remaining,
                        created_by=request.user,
                        reference_note=f"Received against PO #{purchase_order.pk}"
                            + (f" ({line_item.ordered_boxes} boxes × {line_item.pieces_per_box} pcs)" if line_item.ordered_boxes else ""),
                        unit_cost=line_item.unit_cost,
                    )
                    line_item.received_qty = line_item.ordered_qty
                    line_item.save(update_fields=["received_qty"])
            purchase_order.status = PurchaseOrder.Status.RECEIVED
            purchase_order.save(update_fields=["status"])
        messages.success(request, "Purchase order received into stock.")
        return redirect("suppliers:po-detail", pk=purchase_order.pk)
from django.shortcuts import render

# Create your views here.
