from django.urls import path

from .views import LowStockReportView, MovementHistoryReportView, ReportHomeView, StockValuationReportView


app_name = "reports"

urlpatterns = [
    path("", ReportHomeView.as_view(), name="report-home"),
    path("valuation/", StockValuationReportView.as_view(), name="valuation"),
    path("movements/", MovementHistoryReportView.as_view(), name="movements"),
    path("low-stock/", LowStockReportView.as_view(), name="low-stock"),
]
