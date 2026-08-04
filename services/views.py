from decimal import Decimal
from django.db import models
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import OwnerRequiredMixin
from config.ui import build_detail_rows
from .forms import ServiceCompleteForm, ServiceEditForm, ServiceTicketForm
from .models import ServiceTicket


class ServiceListView(LoginRequiredMixin, ListView):
    model = ServiceTicket
    template_name = "services/service_list.html"
    context_object_name = "tickets"

    def get_queryset(self):
        qs = ServiceTicket.objects.select_related("created_by").all()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                models.Q(customer_name__icontains=q)
                | models.Q(customer_phone__icontains=q)
                | models.Q(customer_address__icontains=q)
                | models.Q(issue_description__icontains=q)
            )
        status_filter = self.request.GET.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Services & Installations"
        all_tickets = ServiceTicket.objects.all()
        context["pending_count"] = all_tickets.filter(status=ServiceTicket.Status.PENDING).count()
        context["in_progress_count"] = all_tickets.filter(status=ServiceTicket.Status.IN_PROGRESS).count()
        context["completed_count"] = all_tickets.filter(status=ServiceTicket.Status.COMPLETED).count()
        context["can_manage"] = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        return context


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = ServiceTicket
    form_class = ServiceTicketForm
    template_name = "services/service_form.html"
    success_url = reverse_lazy("services:service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Book Service Visit"
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        ticket = form.save(commit=False)
        ticket.created_by = self.request.user
        ticket.status = ServiceTicket.Status.PENDING
        ticket.save()
        messages.success(self.request, f"Service Ticket SRV-{ticket.pk:03d} created cleanly as Pending.")
        return redirect(self.success_url)


class ServiceDispatchView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(ServiceTicket, pk=pk)
        ticket.status = ServiceTicket.Status.IN_PROGRESS
        ticket.save()
        messages.info(request, f"Service Ticket SRV-{ticket.pk:03d} set to IN PROGRESS (Serviceman dispatched).")
        return redirect("services:service-list")


class ServiceResetPendingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(ServiceTicket, pk=pk)
        ticket.status = ServiceTicket.Status.PENDING
        ticket.save()
        messages.warning(request, f"Service Ticket SRV-{ticket.pk:03d} reset back to PENDING.")
        return redirect("services:service-list")


class ServiceCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(ServiceTicket, pk=pk)
        serviceman_name = request.POST.get("serviceman_name", "").strip()
        parts_desc = request.POST.get("parts_description", "").strip()
        parts_cost_raw = request.POST.get("parts_cost", "0.00").strip()
        charges_raw = request.POST.get("service_charges", "0.00").strip()
        notes = request.POST.get("notes", "").strip()

        try:
            parts_cost = Decimal(parts_cost_raw) if parts_cost_raw else Decimal("0.00")
        except Exception:
            parts_cost = Decimal("0.00")

        try:
            charges = Decimal(charges_raw) if charges_raw else Decimal("0.00")
        except Exception:
            charges = Decimal("0.00")

        ticket.serviceman_name = serviceman_name
        ticket.parts_description = parts_desc
        ticket.parts_cost = parts_cost
        ticket.service_charges = charges
        ticket.notes = notes
        ticket.status = ServiceTicket.Status.COMPLETED
        ticket.save()

        total = parts_cost + charges
        messages.success(request, f"Service Ticket SRV-{ticket.pk:03d} COMPLETED! Bill collected: PKR {total:,.2f}")
        return redirect("services:service-list")


class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceTicket
    form_class = ServiceEditForm
    template_name = "services/service_form.html"
    success_url = reverse_lazy("services:service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Service Ticket SRV-{self.object.pk:03d}"
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        ticket = form.save()
        messages.success(self.request, f"Service Ticket SRV-{ticket.pk:03d} updated.")
        return redirect(self.success_url)


class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = ServiceTicket
    template_name = "services/service_detail.html"
    context_object_name = "ticket"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Service Ticket SRV-{self.object.pk:03d}"
        context["can_manage"] = self.request.user.is_superuser or getattr(self.request.user, "role", None) == "OWNER"
        context["details"] = build_detail_rows(
            self.object,
            [
                {"label": "Customer Name", "lookup": "customer_name"},
                {"label": "Phone Number", "lookup": "customer_phone"},
                {"label": "Address", "lookup": "customer_address"},
                {"label": "Service Type", "lookup": "get_service_type_display"},
                {"label": "Scheduled Date", "lookup": "scheduled_time"},
                {"label": "Status", "lookup": "get_status_display"},
                {"label": "Serviceman / Technician", "lookup": "serviceman_name"},
                {"label": "Parts Replaced", "lookup": "parts_description"},
                {"label": "Parts Price (PKR)", "lookup": "parts_cost"},
                {"label": "Labor Service Fee (PKR)", "lookup": "service_charges"},
                {"label": "Total Bill Collected (PKR)", "lookup": "total_bill"},
                {"label": "Issue Description", "lookup": "issue_description"},
                {"label": "Resolution Notes", "lookup": "notes"},
            ],
        )
        return context


class ServiceDeleteView(OwnerRequiredMixin, DeleteView):
    model = ServiceTicket
    template_name = "generic/confirm_delete.html"
    success_url = reverse_lazy("services:service-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Service Ticket SRV-{self.object.pk:03d}"
        context["cancel_url"] = self.success_url
        return context
