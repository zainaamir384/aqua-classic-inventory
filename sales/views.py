from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import OwnerRequiredMixin
from config.ui import build_detail_rows, build_table_rows
from inventory.models import StockMovement
from inventory.services import get_default_location, record_movement

from .forms import SaleItemFormSet, SaleRecordForm
from .models import SaleItem, SaleRecord


class SaleListView(LoginRequiredMixin, ListView):
    model = SaleRecord
    template_name = "sales/sale_list.html"
    context_object_name = "sales_list"

    def get_queryset(self):
        return SaleRecord.objects.prefetch_related("items__product__category", "created_by", "location").order_by("-created_at", "-sale_date")

    def get_context_data(self, **kwargs):
        from collections import defaultdict
        from django.utils import timezone

        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales & Revenue Hub"
        can_manage = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["can_manage"] = can_manage

        sales = list(context["sales_list"])
        sales_rev = sum(s.total_amount for s in sales)

        from services.models import ServiceTicket
        completed_services = list(ServiceTicket.objects.filter(status=ServiceTicket.Status.COMPLETED))
        service_rev = sum((t.total_bill for t in completed_services), Decimal("0.00"))

        total_rev = sales_rev + service_rev
        total_cost = sum(s.total_cost for s in sales)
        total_profit = total_rev - total_cost
        profit_margin = (total_profit / total_rev * Decimal("100.0")) if total_rev > 0 else Decimal("0.0")
        total_items = sum(item.quantity for s in sales for item in s.items.all())

        context["total_orders_count"] = len(sales)
        context["total_sales_revenue"] = total_rev
        context["total_revenue"] = total_rev
        context["sales_revenue"] = sales_rev
        context["service_revenue"] = service_rev
        context["total_cost"] = total_cost
        context["total_profit"] = total_profit
        context["profit_margin"] = profit_margin
        context["total_items_sold"] = total_items

        today = timezone.localdate()
        today_sales = []
        past_sales_by_date = defaultdict(list)

        for s in sales:
            s_date = timezone.localtime(s.created_at).date() if s.created_at else s.sale_date
            if s_date == today:
                today_sales.append(s)
            else:
                past_sales_by_date[s_date].append(s)

        # Build list of past day cards with totals
        past_days_grouped = []
        for d in sorted(past_sales_by_date.keys(), reverse=True):
            day_sales = past_sales_by_date[d]
            day_sales_rev = sum(s.total_amount for s in day_sales)
            day_srv_rev = sum((t.total_bill for t in completed_services if (t.updated_at and timezone.localtime(t.updated_at).date() == d)), Decimal("0.00"))
            day_rev = day_sales_rev + day_srv_rev
            day_cost = sum(s.total_cost for s in day_sales)
            day_profit = day_rev - day_cost
            day_items = sum(item.quantity for s in day_sales for item in s.items.all())
            past_days_grouped.append({
                "date": d,
                "sales": day_sales,
                "orders_count": len(day_sales),
                "total_revenue": day_rev,
                "total_profit": day_profit,
                "total_items": day_items,
            })

        today_sales_rev = sum(s.total_amount for s in today_sales)
        today_srv_rev = sum((t.total_bill for t in completed_services if (t.updated_at and timezone.localtime(t.updated_at).date() == today)), Decimal("0.00"))
        today_rev = today_sales_rev + today_srv_rev

        today_cost = sum(s.total_cost for s in today_sales)
        today_profit = today_rev - today_cost
        today_margin = (today_profit / today_rev * Decimal("100.0")) if today_rev > 0 else Decimal("0.0")

        context["today_date"] = today
        context["today_sales"] = today_sales
        context["today_orders_count"] = len(today_sales)
        context["today_revenue"] = today_rev
        context["today_sales_rev"] = today_sales_rev
        context["today_srv_rev"] = today_srv_rev
        context["today_cost"] = today_cost
        context["today_profit"] = today_profit
        context["today_margin"] = today_margin
        context["past_days_grouped"] = past_days_grouped

        return context


class SaleFormMixin:
    template_name = "sales/sale_record_form.html"
    success_url = reverse_lazy("sales:sale-list")
    page_title = "Sale Record"

    def get_formset(self):
        return SaleItemFormSet(self.request.POST or None, instance=getattr(self, "object", None))

    def get_context_data(self, **kwargs):
        import json
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from catalog.models import Category, Product
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        context["categories"] = Category.objects.filter(is_active=True).order_by("name")
        
        products = Product.objects.filter(is_active=True).select_related("category").annotate(
            calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0"))
        ).order_by("-calculated_stock", "name")
        
        products_data = []
        for p in products:
            stock_int = int(p.calculated_stock)
            stock_str = f" ({stock_int} pcs in stock)" if stock_int > 0 else " (0 pcs - OUT OF STOCK)"
            products_data.append({
                "id": p.id,
                "name": f"{p.name} [{p.sku or ''}] — {stock_str}",
                "category_id": p.category_id,
                "category_name": p.category.name if p.category else "",
                "stock": stock_int,
                "price": float(p.cost_price or 0.0),
            })
        context["products_json"] = json.dumps(products_data)
        context.setdefault("formset", self.get_formset())
        return context


    def _save_sale_and_items(self, form, reverse_existing: bool = False):
        from collections import defaultdict
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        context = self.get_context_data(form=form)
        formset = context["formset"]
        if not formset.is_valid():
            return False
        from inventory.models import StockItem
        location = getattr(form.instance, "location", None) or get_default_location()
        
        requested_by_product = defaultdict(Decimal)
        for item_form in formset.forms:
            if hasattr(item_form, "cleaned_data") and item_form.cleaned_data and not item_form.cleaned_data.get("DELETE", False):
                product = item_form.cleaned_data.get("product")
                requested_qty = item_form.cleaned_data.get("quantity") or Decimal("0")
                if product and requested_qty > 0:
                    requested_by_product[product] += requested_qty

        for product, total_req_qty in requested_by_product.items():
            stock_item = StockItem.objects.filter(product=product, location=location).first()
            available_qty = stock_item.quantity_on_hand if stock_item else Decimal("0")
            if available_qty < total_req_qty:
                avail_display = int(available_qty) if available_qty == int(available_qty) else float(available_qty)
                req_display = int(total_req_qty) if total_req_qty == int(total_req_qty) else float(total_req_qty)
                messages.error(
                    self.request,
                    f"❌ Cannot record sale: Insufficient stock for '{product.name}'. Currently available stock is {avail_display} pcs, but {req_display} pcs total requested in this order."
                )
                return False

        try:
            with transaction.atomic():
                sale = form.save(commit=False)
                if not sale.pk:
                    sale.created_by = self.request.user
                if not getattr(sale, "location_id", None):
                    sale.location = get_default_location()
                sale.save()
                if reverse_existing:
                    for existing_item in sale.items.all():
                        record_movement(
                            product=existing_item.product,
                            location=sale.location,
                            movement_type=StockMovement.MovementType.RETURN_IN,
                            quantity=existing_item.quantity,
                            created_by=self.request.user,
                            reference_note=f"Reverse sale #{sale.pk}",
                            unit_cost=existing_item.sale_price,
                        )
                    sale.items.all().delete()
                formset.instance = sale
                items = formset.save()
                for item in items:
                    record_movement(
                        product=item.product,
                        location=sale.location,
                        movement_type=StockMovement.MovementType.SALE_OUT,
                        quantity=item.quantity,
                        created_by=self.request.user,
                        reference_note=f"Sale #{sale.pk}",
                        unit_cost=item.sale_price,
                    )
                sale.recalculate_total()
            return sale
        except ValidationError as e:
            err_msg = str(e.message) if hasattr(e, 'message') else str(e)
            if hasattr(e, 'message_dict'):
                messages_list = []
                for field, msgs in e.message_dict.items():
                    messages_list.extend(msgs)
                err_msg = " ".join(messages_list)
            messages.error(self.request, f"❌ Insufficient Stock: {err_msg}")
            return False


class SaleCreateView(LoginRequiredMixin, SaleFormMixin, CreateView):
    model = SaleRecord
    form_class = SaleRecordForm
    page_title = "Record Sale"

    def form_valid(self, form):
        sale = self._save_sale_and_items(form)
        if sale is False:
            return self.form_invalid(form)
        messages.success(self.request, "Sale recorded.")
        return redirect(self.success_url)


class SaleUpdateView(OwnerRequiredMixin, SaleFormMixin, UpdateView):
    model = SaleRecord
    form_class = SaleRecordForm
    page_title = "Edit Sale"

    def form_valid(self, form):
        sale = self._save_sale_and_items(form, reverse_existing=True)
        if sale is False:
            return self.form_invalid(form)
        messages.success(self.request, "Sale updated.")
        return redirect(self.success_url)


class SaleDetailView(LoginRequiredMixin, DetailView):
    model = SaleRecord
    template_name = "sales/sale_record_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Sale #{self.object.pk}"
        context["details"] = build_detail_rows(
            self.object,
            [
                {"label": "Date", "lookup": "sale_date"},
                {"label": "Location", "lookup": "location"},
                {"label": "Sold To", "lookup": "customer_name"},
                {"label": "Total", "lookup": "total_amount"},
                {"label": "Notes", "lookup": "notes"},
            ],
        )
        context["items"] = self.object.items.select_related("product")
        context["edit_url"] = reverse_lazy("sales:sale-edit", kwargs={"pk": self.object.pk})
        context["delete_url"] = reverse_lazy("sales:sale-delete", kwargs={"pk": self.object.pk})
        return context


class SaleDeleteView(OwnerRequiredMixin, DeleteView):
    model = SaleRecord
    template_name = "generic/confirm_delete.html"
    success_url = reverse_lazy("sales:sale-list")
    page_title = "Delete Sale"

    def delete(self, request, *args, **kwargs):
        sale = self.get_object()
        with transaction.atomic():
            for item in sale.items.all():
                record_movement(
                    product=item.product,
                    location=sale.location,
                    movement_type=StockMovement.MovementType.RETURN_IN,
                    quantity=item.quantity,
                    created_by=request.user,
                    reference_note=f"Delete sale #{sale.pk}",
                    unit_cost=item.sale_price,
                )
            sale.items.all().delete()
            return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["cancel_url"] = self.success_url
        return context
from django.shortcuts import render

# Create your views here.
