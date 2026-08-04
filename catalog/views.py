from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import OwnerRequiredMixin
from config.ui import build_detail_rows, build_table_rows

from .forms import BrandForm, CategoryForm, ProductComponentForm, ProductForm
from .models import Brand, Category, Product, ProductComponent


class BaseListView(LoginRequiredMixin, ListView):
    template_name = "generic/list.html"
    columns = []
    create_url = None
    create_label = "Add New"
    page_subtitle = ""
    detail_url_name = None
    edit_url_name = None
    delete_url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["columns"] = self.columns
        rows = []
        for obj in context["object_list"]:
            rows.append(
                {
                    "object": obj,
                    "values": [build_detail_rows(obj, [{"label": "value", "lookup": column["lookup"]}])[0]["value"] for column in self.columns],
                    "object_url": reverse(self.detail_url_name, kwargs={"pk": obj.pk}) if self.detail_url_name else None,
                    "edit_url": reverse(self.edit_url_name, kwargs={"pk": obj.pk}) if self.edit_url_name and self._can_manage else None,
                    "delete_url": reverse(self.delete_url_name, kwargs={"pk": obj.pk}) if self.delete_url_name and self._can_manage else None,
                }
            )
        context["rows"] = rows
        context["create_url"] = self.create_url if self._can_manage and self.create_url else None
        context["create_label"] = self.create_label
        return context

    @property
    def _can_manage(self):
        return self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"


class BaseFormView(OwnerRequiredMixin):
    template_name = "generic/form.html"
    success_message = "Saved successfully."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class CategoryListView(BaseListView):
    model = Category
    page_title = "Categories"
    columns = [{"label": "Name", "lookup": "name"}, {"label": "Active", "lookup": "is_active"}]
    create_url = reverse_lazy("catalog:category-add")
    detail_url_name = "catalog:category-edit"
    edit_url_name = "catalog:category-edit"
    delete_url_name = "catalog:category-delete"


class CategoryCreateView(BaseFormView, CreateView):
    model = Category
    form_class = CategoryForm
    page_title = "Add Category"
    success_url = reverse_lazy("catalog:category-list")


class CategoryUpdateView(BaseFormView, UpdateView):
    model = Category
    form_class = CategoryForm
    page_title = "Edit Category"
    success_url = reverse_lazy("catalog:category-list")


class CategoryDeleteView(BaseFormView, DeleteView):
    model = Category
    template_name = "generic/confirm_delete.html"
    page_title = "Delete Category"
    success_url = reverse_lazy("catalog:category-list")


class BrandListView(BaseListView):
    model = Brand
    page_title = "Brands"
    columns = [
        {"label": "Name", "lookup": "name"},
        {"label": "Origin", "lookup": "origin_label"},
        {"label": "Active", "lookup": "is_active"},
    ]
    create_url = reverse_lazy("catalog:brand-add")
    detail_url_name = "catalog:brand-edit"
    edit_url_name = "catalog:brand-edit"
    delete_url_name = "catalog:brand-delete"


class BrandCreateView(BaseFormView, CreateView):
    model = Brand
    form_class = BrandForm
    page_title = "Add Brand"
    success_url = reverse_lazy("catalog:brand-list")


class BrandUpdateView(BaseFormView, UpdateView):
    model = Brand
    form_class = BrandForm
    page_title = "Edit Brand"
    success_url = reverse_lazy("catalog:brand-list")


class BrandDeleteView(BaseFormView, DeleteView):
    model = Brand
    template_name = "generic/confirm_delete.html"
    page_title = "Delete Brand"
    success_url = reverse_lazy("catalog:brand-list")


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        qs = Product.objects.select_related("category", "brand").annotate(
            total_stock=models.Sum("stock_items__quantity_on_hand")
        )
        q = self.request.GET.get("q", "").strip()
        category_id = self.request.GET.get("category", "")

        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(sku__icontains=q))
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Products & Inventory"
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        context["selected_category"] = self.request.GET.get("category", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["can_manage"] = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "generic/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        details = [
            {"label": "Name", "lookup": "name"},
            {"label": "SKU", "lookup": "sku"},
            {"label": "Category", "lookup": "category"},
            {"label": "Brand", "lookup": "brand"},
            {"label": "Configuration", "lookup": "configuration"},
            {"label": "Stage Count", "lookup": "stage_count"},
            {"label": "Unit Type", "lookup": "unit_type"},
            {"label": "Unit of Measure", "lookup": "unit_of_measure"},
            {"label": "Reorder Level", "lookup": "reorder_level"},
            {"label": "Active", "lookup": "is_active"},
        ]
        if self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER":
            details.insert(8, {"label": "Cost Price", "lookup": "cost_price"})
        context["page_title"] = product.name
        context["details"] = build_detail_rows(product, details)
        context["edit_url"] = reverse_lazy("catalog:product-edit", kwargs={"pk": product.pk})
        context["delete_url"] = reverse_lazy("catalog:product-delete", kwargs={"pk": product.pk})
        context["bom_items"] = product.bill_of_materials.select_related("component")
        return context


class ProductCreateView(BaseFormView, CreateView):
    model = Product
    form_class = ProductForm
    page_title = "Add Product"
    success_url = reverse_lazy("catalog:product-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProductUpdateView(BaseFormView, UpdateView):
    model = Product
    form_class = ProductForm
    page_title = "Edit Product"
    success_url = reverse_lazy("catalog:product-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProductDeleteView(BaseFormView, DeleteView):
    model = Product
    template_name = "generic/confirm_delete.html"
    page_title = "Delete Product"
    success_url = reverse_lazy("catalog:product-list")

    def form_valid(self, form):
        from django.db import transaction
        from django.shortcuts import redirect
        from django.urls import reverse
        from inventory.models import StockItem, StockMovement
        from sales.models import SaleItem
        from suppliers.models import PurchaseOrderLineItem

        product = self.get_object()
        name = product.name
        with transaction.atomic():
            StockMovement.objects.filter(product=product).delete()
            StockItem.objects.filter(product=product).delete()
            ProductComponent.objects.filter(models.Q(product=product) | models.Q(component=product)).delete()
            PurchaseOrderLineItem.objects.filter(product=product).delete()
            SaleItem.objects.filter(product=product).delete()
            product.delete()

        messages.success(self.request, f"Product '{name}' was deleted successfully.")
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and "/delete/" not in next_url:
            return redirect(next_url)
        return redirect("catalog:product-list")


class ProductDeductStockView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from decimal import Decimal
        from django.db import transaction
        from django.shortcuts import get_object_or_404, redirect
        from inventory.models import StockMovement
        from inventory.services import get_default_location, record_movement
        from sales.models import SaleItem, SaleRecord

        product = get_object_or_404(Product, pk=pk)
        qty_str = request.POST.get("quantity", "0").strip()
        reason = request.POST.get("reason", "Sold to Customer").strip()
        price_str = request.POST.get("sale_price", "").strip()
        note = request.POST.get("note", "").strip()

        try:
            quantity = Decimal(qty_str)
        except Exception:
            quantity = Decimal("0")

        try:
            sale_price = Decimal(price_str) if price_str else product.cost_price
        except Exception:
            sale_price = product.cost_price

        if quantity <= 0:
            messages.error(request, "Please enter a valid quantity to deduct.")
            referer = request.META.get("HTTP_REFERER")
            return redirect(referer) if referer else redirect("catalog:product-list")

        location = get_default_location()
        is_sale = "sold" in reason.lower() or "sale" in reason.lower()
        movement_type = StockMovement.MovementType.SALE_OUT if is_sale else StockMovement.MovementType.ADJUSTMENT_OUT

        try:
            with transaction.atomic():
                # Touch updated_at so item moves to top of tables
                product.save(update_fields=["updated_at"])

                # 1. Record stock movement
                record_movement(
                    product=product,
                    location=location,
                    movement_type=movement_type,
                    quantity=quantity,
                    created_by=request.user,
                    reference_note=f"{reason} @ PKR {sale_price:.2f}/pc" + (f": {note}" if note else ""),
                    unit_cost=sale_price,
                )

                # 2. If it's a sale (to customer or salesman), create a SaleRecord entry
                if is_sale:
                    customer_name = "Salesman" if "salesman" in reason.lower() else "Walk-in Customer"
                    total_amt = sale_price * quantity
                    sale_rec = SaleRecord.objects.create(
                        location=location,
                        customer_name=customer_name,
                        notes=f"{reason}" + (f" ({note})" if note else ""),
                        created_by=request.user,
                        total_amount=total_amt,
                    )
                    SaleItem.objects.create(
                        sale=sale_rec,
                        product=product,
                        quantity=quantity,
                        sale_price=sale_price,
                    )

            messages.success(
                request,
                f"Successfully deducted {quantity} piece(s) of '{product.name}' @ PKR {sale_price:.2f}/pc "
                f"(Total: PKR {sale_price * quantity:.2f}) and logged to sales history!"
            )
        except Exception as e:
            err_msg = str(e)
            if "Insufficient stock" in err_msg or "quantity" in err_msg:
                messages.error(request, f"Cannot deduct stock: Only {product.total_stock or 0} piece(s) left in stock.")
            else:
                messages.error(request, f"Cannot deduct stock: {err_msg}")

        referer = request.META.get("HTTP_REFERER")
        return redirect(referer) if referer else redirect("catalog:product-list")


class ProductAddStockView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from decimal import Decimal
        from django.db import transaction
        from django.shortcuts import get_object_or_404, redirect
        from inventory.models import StockMovement
        from inventory.services import get_default_location, record_movement
        from suppliers.models import PurchaseOrder, PurchaseOrderLineItem, Supplier

        product = get_object_or_404(Product, pk=pk)
        boxes_str = request.POST.get("boxes", "0").strip()
        ppb_str = request.POST.get("pieces_per_box", "").strip()
        qty_str = request.POST.get("quantity", "0").strip()
        cost_str = request.POST.get("unit_cost", "").strip()
        note = request.POST.get("note", "").strip()

        try:
            boxes = int(boxes_str) if boxes_str else 0
        except ValueError:
            boxes = 0

        try:
            ppb = int(ppb_str) if ppb_str else (product.pieces_per_box or 0)
        except ValueError:
            ppb = product.pieces_per_box or 0

        try:
            quantity = Decimal(qty_str) if qty_str else Decimal("0")
        except Exception:
            quantity = Decimal("0")

        try:
            unit_cost = Decimal(cost_str) if cost_str else product.cost_price
        except Exception:
            unit_cost = product.cost_price

        total_qty = Decimal("0")
        ref_text = "Stock Addition"
        if boxes > 0 and ppb > 0:
            total_qty = Decimal(str(boxes * ppb))
            ref_text = f"Added {boxes} box(es) ({ppb} pcs/box)"
        elif quantity > 0:
            total_qty = quantity
            ref_text = f"Added {quantity} piece(s)"

        if total_qty <= 0:
            messages.error(request, "Please enter either number of boxes or number of pieces to add stock.")
            return redirect("catalog:product-list")

        location = get_default_location()

        try:
            with transaction.atomic():
                # Update product cost price if provided and touch updated_at
                fields_to_update = ["updated_at"]
                if cost_str and unit_cost > 0:
                    product.cost_price = unit_cost
                    fields_to_update.append("cost_price")
                    if ppb > 0:
                        product.pieces_per_box = ppb
                        fields_to_update.append("pieces_per_box")
                product.save(update_fields=fields_to_update)

                # Record stock movement
                record_movement(
                    product=product,
                    location=location,
                    movement_type=StockMovement.MovementType.PURCHASE_IN,
                    quantity=total_qty,
                    created_by=request.user,
                    reference_note=f"{ref_text} @ PKR {unit_cost:.2f}/pc" + (f": {note}" if note else ""),
                    unit_cost=unit_cost,
                )

                # Save Purchase Order in Purchase History
                default_supplier = Supplier.objects.first()
                if default_supplier:
                    po = PurchaseOrder.objects.create(
                        supplier=default_supplier,
                        created_by=request.user,
                        status=PurchaseOrder.Status.RECEIVED,
                        notes=f"Quick stock addition for {product.name}" + (f" ({note})" if note else ""),
                    )
                    PurchaseOrderLineItem.objects.create(
                        purchase_order=po,
                        product=product,
                        ordered_boxes=boxes if boxes > 0 else None,
                        pieces_per_box=ppb if ppb > 0 else None,
                        ordered_qty=total_qty,
                        received_qty=total_qty,
                        unit_cost=unit_cost,
                    )

            messages.success(
                request,
                f"Successfully added {total_qty} piece(s) to stock for '{product.name}' @ PKR {unit_cost:.2f}/pc "
                f"(Total: PKR {unit_cost * total_qty:.2f}) and logged to purchase history!"
            )
        except Exception as e:
            messages.error(request, f"Could not add stock: {e}")

        referer = request.META.get("HTTP_REFERER")
        return redirect(referer) if referer else redirect("catalog:product-list")


class ProductComponentListView(BaseListView):
    model = ProductComponent
    page_title = "Bill of Materials"
    columns = [
        {"label": "Product", "lookup": "product"},
        {"label": "Component", "lookup": "component"},
        {"label": "Qty", "lookup": "quantity"},
    ]
    create_url = reverse_lazy("catalog:bom-add")
    detail_url_name = "catalog:bom-edit"
    edit_url_name = "catalog:bom-edit"
    delete_url_name = "catalog:bom-delete"


class ProductComponentCreateView(BaseFormView, CreateView):
    model = ProductComponent
    form_class = ProductComponentForm
    page_title = "Add BOM Line"
    success_url = reverse_lazy("catalog:bom-list")


class ProductComponentUpdateView(BaseFormView, UpdateView):
    model = ProductComponent
    form_class = ProductComponentForm
    page_title = "Edit BOM Line"
    success_url = reverse_lazy("catalog:bom-list")


class ProductComponentDeleteView(BaseFormView, DeleteView):
    model = ProductComponent
    template_name = "generic/confirm_delete.html"
    page_title = "Delete BOM Line"
    success_url = reverse_lazy("catalog:bom-list")
