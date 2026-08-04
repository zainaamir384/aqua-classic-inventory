from decimal import Decimal

from django.conf import settings
from django.db import models


class ServiceTicket(models.Model):
    class ServiceType(models.TextChoices):
        INSTALLATION = "INSTALLATION", "New Unit Installation"
        REPAIR = "REPAIR", "Repair & Maintenance"
        FILTER_CHANGE = "FILTER_CHANGE", "Filter Replacement"
        INSPECTION = "INSPECTION", "Inspection / Checkup"
        OTHER = "OTHER", "Other Service"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    customer_name = models.CharField(max_length=160, verbose_name="Customer Name")
    customer_phone = models.CharField(max_length=40, verbose_name="Phone Number")
    customer_address = models.TextField(verbose_name="Customer Address / Location")
    service_type = models.CharField(
        max_length=40,
        choices=ServiceType.choices,
        default=ServiceType.REPAIR,
        verbose_name="Service Required",
    )
    issue_description = models.TextField(verbose_name="Issue / Service Request Details")
    scheduled_date = models.DateField(
        blank=True, null=True, verbose_name="Scheduled Visit Date"
    )
    scheduled_time = models.DateField(
        blank=True, null=True, verbose_name="Scheduled Visit Date"
    )
    serviceman_name = models.CharField(
        max_length=160, blank=True, verbose_name="Serviceman / Technician Name"
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING
    )
    parts_description = models.TextField(
        blank=True, verbose_name="Parts Changed / Replaced"
    )
    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total Parts Price (PKR)",
    )
    service_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Labor Service Fee (PKR)",
    )
    notes = models.TextField(
        blank=True, verbose_name="Resolution Note / Completion Remarks"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="services_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total_bill(self) -> Decimal:
        return self.parts_cost + self.service_charges

    def __str__(self) -> str:
        return f"SRV-{self.pk:03d} - {self.customer_name} ({self.get_service_type_display()})"
