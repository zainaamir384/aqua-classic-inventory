from django.contrib import admin
from .models import ServiceTicket


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "customer_name",
        "customer_phone",
        "service_type",
        "status",
        "scheduled_time",
        "parts_cost",
        "service_charges",
    )
    list_filter = ("status", "service_type")
    search_fields = ("customer_name", "customer_phone", "issue_description")
