from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models import F
from django.views.generic import TemplateView

from catalog.models import Product
from inventory.models import StockItem, StockMovement


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        from datetime import timedelta
        from django.utils import timezone
        from sales.models import SaleItem, SaleRecord

        context = super().get_context_data(**kwargs)
        user = self.request.user
        from catalog.models import Category
        assembled_cats = Category.objects.filter(
            name__in=[
                '10" Water Filter (Assembled)',
                '20" Slim Water Filter (Assembled)',
                '20" Jumbo Water Filter (Assembled)',
                'RO Water Filter (Assembled)',
            ]
        )

        stock_items = StockItem.objects.select_related("product", "product__category", "location")
        raw_val = Decimal("0.00")
        assembled_val = Decimal("0.00")

        for item in stock_items:
            item_val = item.quantity_on_hand * item.product.cost_price
            if item.product.unit_type == Product.UnitType.FINISHED_UNIT or item.product.category in assembled_cats:
                assembled_val += item_val
            else:
                raw_val += item_val

        total_combined_val = raw_val + assembled_val

        context["raw_inventory_value"] = raw_val
        context["assembled_inventory_value"] = assembled_val
        context["total_combined_inventory_value"] = total_combined_val

        from services.models import ServiceTicket
        sales_rev_total = SaleRecord.objects.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        service_rev_total = sum((t.total_bill for t in ServiceTicket.objects.filter(status=ServiceTicket.Status.COMPLETED)), Decimal("0.00"))
        total_sales_revenue = sales_rev_total + service_rev_total

        # Calculate overall net profit
        total_cogs = Decimal("0.00")
        all_sale_items = SaleItem.objects.select_related("product").all()
        for item in all_sale_items:
            total_cogs += item.quantity * item.product.cost_price
        total_profit = max(Decimal("0.00"), total_sales_revenue - total_cogs)

        # 7-day Sales & Profit graph trends
        today = timezone.localdate()
        chart_labels = []
        sales_data = []
        profit_data = []

        completed_services = list(ServiceTicket.objects.filter(status=ServiceTicket.Status.COMPLETED))

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime("%b %d"))

            day_sales = SaleRecord.objects.filter(created_at__date=day)
            day_sales_rev = day_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
            day_srv_rev = sum((t.total_bill for t in completed_services if (t.updated_at and timezone.localtime(t.updated_at).date() == day)), Decimal("0.00"))
            day_revenue = day_sales_rev + day_srv_rev

            day_cogs = Decimal("0.00")
            day_items = SaleItem.objects.filter(sale__created_at__date=day).select_related("product")
            for item in day_items:
                day_cogs += item.quantity * item.product.cost_price

            day_prof = max(Decimal("0.00"), day_revenue - day_cogs)

            sales_data.append(float(day_revenue))
            profit_data.append(float(day_prof))

        # Category Inventory Distribution data for Donut Chart
        from catalog.models import Category
        cat_labels = []
        cat_stock = []
        categories = Category.objects.filter(is_active=True)
        for cat in categories:
            stk_qty = StockItem.objects.filter(product__category=cat).aggregate(total=Sum("quantity_on_hand"))["total"] or 0
            if stk_qty > 0:
                cat_labels.append(cat.name.replace(" (Assembled)", ""))
                cat_stock.append(int(stk_qty))

        # Dynamic today vs yesterday trend calculations
        today_sales = SaleRecord.objects.filter(created_at__date=today)
        today_sales_rev = today_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        today_srv_rev = sum((t.total_bill for t in completed_services if (t.updated_at and timezone.localtime(t.updated_at).date() == today)), Decimal("0.00"))
        revenue_today = today_sales_rev + today_srv_rev
        orders_today_count = today_sales.count()

        yesterday = today - timedelta(days=1)
        yesterday_sales = SaleRecord.objects.filter(created_at__date=yesterday)
        yesterday_sales_rev = yesterday_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        yesterday_srv_rev = sum((t.total_bill for t in completed_services if (t.updated_at and timezone.localtime(t.updated_at).date() == yesterday)), Decimal("0.00"))
        revenue_yesterday = yesterday_sales_rev + yesterday_srv_rev
        orders_yesterday_count = yesterday_sales.count()

        revenue_is_down = False
        if revenue_yesterday > 0:
            rev_change = ((revenue_today - revenue_yesterday) / revenue_yesterday) * 100
            revenue_trend_str = f"{rev_change:+.1f}% vs yesterday"
            if rev_change < 0:
                revenue_is_down = True
        elif revenue_today > 0:
            revenue_trend_str = "+100% vs yesterday"
        else:
            revenue_trend_str = "0% vs yesterday"

        orders_is_down = False
        if orders_yesterday_count > 0:
            ord_change = ((orders_today_count - orders_yesterday_count) / orders_yesterday_count) * 100
            orders_trend_str = f"{ord_change:+.1f}% vs yesterday"
            if ord_change < 0:
                orders_is_down = True
        elif orders_today_count > 0:
            orders_trend_str = "+100% vs yesterday"
        else:
            orders_trend_str = "0% vs yesterday"

        if total_sales_revenue > 0:
            profit_margin_pct = (total_profit / total_sales_revenue) * 100
            profit_margin_str = f"{profit_margin_pct:.1f}% net margin"
        else:
            profit_margin_str = "0% net margin"

        total_skus_count = Product.objects.filter(is_active=True).count()

        context["total_skus"] = total_skus_count
        context["revenue_today"] = revenue_today
        context["orders_today_count"] = orders_today_count
        context["revenue_trend_str"] = revenue_trend_str
        context["orders_trend_str"] = orders_trend_str
        context["revenue_is_down"] = revenue_is_down
        context["orders_is_down"] = orders_is_down
        context["profit_margin_str"] = profit_margin_str
        context["can_view_costs"] = user.is_superuser or getattr(user, "role", None) == "OWNER"
        context["total_stock_value"] = total_combined_val if context["can_view_costs"] else None
        context["total_sales_revenue"] = total_sales_revenue
        context["total_profit"] = total_profit
        context["recent_sales"] = SaleRecord.objects.prefetch_related("items__product").order_by("-created_at")[:5]
        context["low_stock_items"] = StockItem.objects.select_related("product", "location").filter(quantity_on_hand__lte=F("product__reorder_level"))[:10]
        context["recent_movements"] = StockMovement.objects.select_related("product", "location", "created_by")[:20]
        context["chart_labels"] = chart_labels
        context["chart_sales"] = sales_data
        context["chart_profit"] = profit_data
        context["cat_labels"] = cat_labels
        context["cat_stock"] = cat_stock
        return context
from django.shortcuts import render

# Create your views here.
