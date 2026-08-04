from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.views.generic import TemplateView

from catalog.models import Category, Product
from config.ui import build_table_rows
from inventory.models import StockItem, StockMovement

from .utils import export_pdf, export_xlsx


class ReportAccessMixin(LoginRequiredMixin):
    def wants_export(self):
        return self.request.GET.get("format") in {"xlsx", "pdf"}

    def export_response(self, title, headers, rows):
        format_name = self.request.GET.get("format")
        if format_name == "xlsx":
            content = export_xlsx(title, headers, rows)
            response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = f'attachment; filename="{title}.xlsx"'
            return response
        if format_name == "pdf":
            content = export_pdf(title, headers, rows)
            response = HttpResponse(content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{title}.pdf"'
            return response
        return None


class ReportHomeView(LoginRequiredMixin, TemplateView):
    template_name = "reports/report_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory & Stock Advisory Reports"

        products = Product.objects.filter(is_active=True).select_related("category").annotate(
            calculated_stock=Coalesce(Sum("stock_items__quantity_on_hand"), Decimal("0"))
        ).order_by("calculated_stock", "name")

        low_or_zero = []
        out_count = 0
        low_count = 0
        healthy_count = 0

        for p in products:
            stk = int(p.calculated_stock)
            val = stk * p.cost_price
            p_data = {
                "object": p,
                "stock": stk,
                "value": val,
                "status": "OUT_OF_STOCK" if stk <= 0 else ("LOW_STOCK" if stk <= 10 else "HEALTHY"),
            }
            if stk <= 0:
                out_count += 1
                low_or_zero.append(p_data)
            elif stk <= 10:
                low_count += 1
                low_or_zero.append(p_data)
            else:
                healthy_count += 1

        context["total_products"] = len(products)
        context["out_of_stock_count"] = out_count
        context["low_stock_count"] = low_count
        context["healthy_stock_count"] = healthy_count
        context["low_or_zero_items"] = low_or_zero

        return context


class StockValuationReportView(UserPassesTestMixin, ReportAccessMixin, TemplateView):
    template_name = "reports/report_table.html"

    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, "role", None) == "OWNER"

    def get_queryset(self):
        return StockItem.objects.select_related("product", "location")

    def get(self, request, *args, **kwargs):
        if self.wants_export():
            rows = self._rows()
            return self.export_response("stock_valuation", ["Product", "Location", "Qty", "Cost", "Value"], rows)
        return super().get(request, *args, **kwargs)

    def _rows(self):
        rows = []
        for item in self.get_queryset():
            value = item.quantity_on_hand * item.product.cost_price
            rows.append([
                item.product.name,
                item.location.name,
                int(item.quantity_on_hand),
                f"{item.product.cost_price:.2f}",
                f"{value:.2f}",
            ])
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Valuation"
        context["columns"] = [
            {"label": "Product", "lookup": "product"},
            {"label": "Location", "lookup": "location"},
            {"label": "Qty", "lookup": "quantity_on_hand"},
            {"label": "Cost", "lookup": "product.cost_price"},
            {"label": "Value", "lookup": "quantity_on_hand"},
        ]
        context["rows"] = [
            {
                "object": item,
                "values": [
                    item.product.name,
                    item.location.name,
                    int(item.quantity_on_hand),
                    f"{item.product.cost_price:.2f}",
                    f"{item.quantity_on_hand * item.product.cost_price:.2f}",
                ],
            }
            for item in self.get_queryset()
        ]
        return context


class MovementHistoryReportView(ReportAccessMixin, TemplateView):
    template_name = "reports/report_table.html"

    def get_queryset(self):
        queryset = StockMovement.objects.select_related("product", "location", "created_by")
        product_id = self.request.GET.get("product")
        movement_type = self.request.GET.get("movement_type")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        return queryset.order_by("-created_at")

    def get(self, request, *args, **kwargs):
        if self.wants_export():
            rows = [[m.created_at, m.product.name, m.location.name, m.movement_type, m.quantity, m.created_by.username] for m in self.get_queryset()]
            return self.export_response("movement_history", ["Date", "Product", "Location", "Type", "Qty", "By"], rows)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Movement History"
        context["columns"] = [
            {"label": "Date", "lookup": "created_at"},
            {"label": "Product", "lookup": "product"},
            {"label": "Location", "lookup": "location"},
            {"label": "Type", "lookup": "movement_type"},
            {"label": "Qty", "lookup": "quantity"},
            {"label": "By", "lookup": "created_by"},
        ]
        context["rows"] = build_table_rows(self.get_queryset(), context["columns"])
        return context


class LowStockReportView(ReportAccessMixin, TemplateView):
    template_name = "reports/report_table.html"

    def get_queryset(self):
        return StockItem.objects.select_related("product", "location").filter(quantity_on_hand__lte=10).order_by("quantity_on_hand", "product__name")

    def _rows(self):
        return [[i.product.name, i.location.name, int(i.quantity_on_hand), 10] for i in self.get_queryset()]

    def get(self, request, *args, **kwargs):
        if self.wants_export():
            return self.export_response("low_stock", ["Product", "Location", "Qty", "Reorder"], self._rows())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Low Stock"
        context["columns"] = [
            {"label": "Product", "lookup": "product"},
            {"label": "Location", "lookup": "location"},
            {"label": "Qty", "lookup": "quantity_on_hand"},
            {"label": "Reorder", "lookup": "product.reorder_level"},
        ]
        context["rows"] = [
            {
                "object": item,
                "values": [
                    item.product.name,
                    item.location.name,
                    int(item.quantity_on_hand),
                    int(item.product.reorder_level or 10),
                ],
            }
            for item in self.get_queryset()
        ]
        return context
