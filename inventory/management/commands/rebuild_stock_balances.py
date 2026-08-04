from django.core.management.base import BaseCommand

from inventory.models import StockItem


class Command(BaseCommand):
    help = "Rebuild cached stock balances from the stock ledger."

    def handle(self, *args, **options):
        StockItem.rebuild_from_ledger()
        self.stdout.write(self.style.SUCCESS("Stock balances rebuilt."))
