from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from accounts.mixins import OwnerRequiredMixin
from catalog.models import Product
from config.ui import build_table_rows

from .forms import AssemblyForm, LocationForm, StockMovementForm
from .models import Location, StockItem, StockMovement
from .services import InsufficientStockError, assemble_product, get_default_location


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = "generic/list.html"
    page_title = "Locations"
    columns = [
        {"label": "Name", "lookup": "name"},
        {"label": "Code", "lookup": "code"},
        {"label": "Default", "lookup": "is_default"},
        {"label": "Active", "lookup": "is_active"},
    ]
    create_url = reverse_lazy("inventory:location-add")
    detail_url_name = "inventory:location-edit"
    edit_url_name = "inventory:location-edit"
    delete_url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["columns"] = self.columns
        can_manage = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["rows"] = [
            {
                "object": location,
                "values": [location.name, location.code, location.is_default, location.is_active],
                "object_url": reverse("inventory:location-edit", kwargs={"pk": location.pk}),
                "edit_url": reverse("inventory:location-edit", kwargs={"pk": location.pk}) if can_manage else None,
            }
            for location in context["object_list"]
        ]
        context["create_url"] = self.create_url if can_manage else None
        return context


class LocationCreateView(OwnerRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = "generic/form.html"
    success_url = reverse_lazy("inventory:location-list")
    page_title = "Add Location"

    def form_valid(self, form):
        messages.success(self.request, "Location created.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class LocationUpdateView(LocationCreateView, UpdateView):
    page_title = "Edit Location"


class StockItemListView(LoginRequiredMixin, ListView):
    model = StockItem
    template_name = "inventory/stock_item_list.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = StockItem.objects.select_related("product", "location")
        query = self.request.GET.get("q")
        category = self.request.GET.get("category")
        brand = self.request.GET.get("brand")
        stage_count = self.request.GET.get("stage_count")
        configuration = self.request.GET.get("configuration")
        low_stock = self.request.GET.get("low_stock")
        location_id = self.request.GET.get("location")

        if query:
            queryset = queryset.filter(Q(product__name__icontains=query) | Q(product__sku__icontains=query))
        if category:
            queryset = queryset.filter(product__category_id=category)
        if brand:
            queryset = queryset.filter(product__brand_id=brand)
        if stage_count:
            queryset = queryset.filter(product__stage_count=stage_count)
        if configuration:
            queryset = queryset.filter(product__configuration=configuration)
        if low_stock:
            queryset = queryset.filter(quantity_on_hand__lte=F("product__reorder_level"))
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset.order_by("product__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        columns = [
            {"label": "Product", "lookup": "product"},
            {"label": "SKU", "lookup": "product.sku"},
            {"label": "Location", "lookup": "location"},
            {"label": "On Hand", "lookup": "quantity_on_hand"},
            {"label": "Reorder", "lookup": "product.reorder_level"},
        ]
        context["page_title"] = "Current Stock"
        context["columns"] = columns
        context["rows"] = build_table_rows(context["object_list"], columns)
        context["filters"] = {
            "products": Product.objects.filter(is_active=True).order_by("name"),
            "categories": Product.objects.values_list("category__id", "category__name").distinct().order_by("category__name"),
            "brands": Product.objects.values_list("brand__id", "brand__name").distinct().order_by("brand__name"),
            "locations": Location.objects.filter(is_active=True).order_by("name"),
        }
        return context


class StockLedgerListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = "inventory/stock_ledger.html"
    paginate_by = 50
    page_title = "Stock In / Out Ledger"

    def get_queryset(self):
        queryset = StockMovement.objects.select_related("product", "product__category", "location", "created_by")
        product_id = self.request.GET.get("product")
        category_id = self.request.GET.get("category")
        movement_type = self.request.GET.get("movement_type")
        search_query = self.request.GET.get("q", "").strip()

        if search_query:
            queryset = queryset.filter(Q(product__name__icontains=search_query) | Q(reference_note__icontains=search_query))
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        from catalog.models import Category
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["page_subtitle"] = "Official read-only audit history of all stock additions, sales, and movements."
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_type"] = self.request.GET.get("movement_type", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["create_url"] = None
        return context


class StockMovementCreateView(LoginRequiredMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = "generic/form.html"
    success_url = reverse_lazy("inventory:stock-ledger")
    page_title = "Add Stock Movement"

    def get_initial(self):
        initial = super().get_initial()
        initial["location"] = get_default_location()
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Stock movement recorded.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context


class AssemblyView(LoginRequiredMixin, FormView):
    form_class = AssemblyForm
    template_name = "inventory/assemble_unit.html"
    success_url = reverse_lazy("inventory:assemble-unit")
    page_title = "Assemble Unit Hub"

    def form_valid(self, form):
        from decimal import Decimal
        from django.db import transaction
        from catalog.models import Category, Product, ProductComponent
        from inventory.models import StockMovement
        from inventory.services import get_default_location, record_movement

        category = form.cleaned_data["category"]
        config_type = form.cleaned_data.get("config_type", "").strip()
        stage_count = form.cleaned_data.get("stage_count")
        unit_name = form.cleaned_data.get("unit_name", "").strip()
        quantity = Decimal(str(form.cleaned_data["quantity"]))
        cost_price = form.cleaned_data.get("cost_price") or Decimal("0.00")
        reference_note = form.cleaned_data.get("reference_note", "").strip()

        housing_item = form.cleaned_data.get("housing_item")
        housing_qty_per_unit = form.cleaned_data.get("housing_qty_per_unit") or 3
        stage1_item = form.cleaned_data.get("stage1_item")
        stage2_item = form.cleaned_data.get("stage2_item")
        stage3_item = form.cleaned_data.get("stage3_item")

        # Auto-generate name if blank based on selected cartridges/housings
        if not unit_name:
            cartridge_parts = []
            if stage1_item:
                cartridge_parts.append(stage1_item.name)
            if stage2_item:
                cartridge_parts.append(stage2_item.name)
            if stage3_item:
                cartridge_parts.append(stage3_item.name)

            if "ro" in category.name.lower():
                suffix = f" ({', '.join(cartridge_parts)})" if cartridge_parts else ""
                unit_name = f"RO System {stage_count}-Stage{suffix}"
            else:
                prefix = f"{config_type} " if config_type else ""
                clean_cat = category.name.replace(" (Assembled)", "")
                suffix = f" ({', '.join(cartridge_parts)})" if cartridge_parts else ""
                unit_name = f"{prefix}{clean_cat}{suffix}"

        config_enum = Product.Configuration.N_A
        if config_type.upper() == "SINGLE":
            config_enum = Product.Configuration.SINGLE
        elif config_type.upper() == "DUAL":
            config_enum = Product.Configuration.DUAL
        elif config_type.upper() == "TRIPLE":
            config_enum = Product.Configuration.TRIPLE

        location = get_default_location()

        try:
            with transaction.atomic():
                product, created = Product.objects.get_or_create(
                    name=unit_name,
                    defaults={
                        "category": category,
                        "unit_type": Product.UnitType.FINISHED_UNIT,
                        "configuration": config_enum,
                        "stage_count": stage_count,
                        "cost_price": cost_price,
                        "is_active": True,
                    },
                )
                # Update attributes if existing
                updated_fields = []
                if product.unit_type != Product.UnitType.FINISHED_UNIT:
                    product.unit_type = Product.UnitType.FINISHED_UNIT
                    updated_fields.append("unit_type")
                if stage_count and product.stage_count != stage_count:
                    product.stage_count = stage_count
                    updated_fields.append("stage_count")
                if config_enum != Product.Configuration.N_A and product.configuration != config_enum:
                    product.configuration = config_enum
                    updated_fields.append("configuration")
                if cost_price > 0 and product.cost_price != cost_price:
                    product.cost_price = cost_price
                    updated_fields.append("cost_price")
                if updated_fields:
                    product.save(update_fields=updated_fields)

                # 1. Produce finished assembled units to display stock
                ref_msg = f"Assembled Unit: {unit_name}" + (f" ({reference_note})" if reference_note else "")
                record_movement(
                    product=product,
                    location=location,
                    movement_type=StockMovement.MovementType.ASSEMBLY_PRODUCE,
                    quantity=quantity,
                    created_by=self.request.user,
                    reference_note=ref_msg,
                    unit_cost=product.cost_price,
                )

                # 2. Auto-deduct selected raw component stock from inventory ONLY for non-RO filters
                deducted_summary = []
                if "ro" not in category.name.lower():
                    if housing_item:
                        h_total = Decimal(str(housing_qty_per_unit)) * quantity
                        record_movement(
                            product=housing_item,
                            location=location,
                            movement_type=StockMovement.MovementType.ASSEMBLY_CONSUME,
                            quantity=h_total,
                            created_by=self.request.user,
                            reference_note=f"Used in assembly of {unit_name} ({int(quantity)} units)",
                        )
                        deducted_summary.append(f"{int(h_total)}x {housing_item.name}")

                    for item in [stage1_item, stage2_item, stage3_item]:
                        if item:
                            c_total = quantity  # 1 cartridge per assembled unit
                            record_movement(
                                product=item,
                                location=location,
                                movement_type=StockMovement.MovementType.ASSEMBLY_CONSUME,
                                quantity=c_total,
                                created_by=self.request.user,
                                reference_note=f"Used in assembly of {unit_name} ({int(quantity)} units)",
                            )
                            deducted_summary.append(f"{int(c_total)}x {item.name}")

            msg = f"Successfully assembled and added {int(quantity)} unit(s) of '{unit_name}' to display stock!"
            if deducted_summary:
                msg += f" Auto-deducted raw parts: {', '.join(deducted_summary)}."
            messages.success(self.request, msg)
            return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Could not complete assembly: {e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        from decimal import Decimal
        from django.db.models import Q, Sum
        from django.db.models.functions import Coalesce
        from catalog.models import Category, Product

        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url

        assembled_cats = Category.objects.filter(
            name__in=[
                '10" Water Filter (Assembled)',
                '20" Slim Water Filter (Assembled)',
                '20" Jumbo Water Filter (Assembled)',
                'RO Water Filter (Assembled)',
            ]
        ).order_by("name")

        cat_filter = self.request.GET.get("category", "").strip()
        qs = Product.objects.filter(
            Q(category__in=assembled_cats) | Q(unit_type=Product.UnitType.FINISHED_UNIT)
        )
        if cat_filter:
            qs = qs.filter(category_id=cat_filter)

        context["categories"] = assembled_cats
        context["selected_category"] = int(cat_filter) if cat_filter.isdigit() else None
        context["assembled_products"] = (
            qs.annotate(total_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0.000")))
            .select_related("category", "brand")
            .order_by("-updated_at", "-id")
        )
        can_manage = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["can_manage"] = can_manage
        return context


class LowStockListView(LoginRequiredMixin, ListView):
    model = StockItem
    template_name = "inventory/stock_item_list.html"
    page_title = "Low Stock Alerts"

    def get_queryset(self):
        return StockItem.objects.select_related("product", "location").filter(quantity_on_hand__lte=F("product__reorder_level")).order_by("product__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        columns = [
            {"label": "Product", "lookup": "product"},
            {"label": "Location", "lookup": "location"},
            {"label": "On Hand", "lookup": "quantity_on_hand"},
            {"label": "Reorder", "lookup": "product.reorder_level"},
        ]
        context["page_title"] = self.page_title
        context["columns"] = columns
        context["rows"] = build_table_rows(context["object_list"], columns)
        return context
from django.shortcuts import render

# Create your views here.
