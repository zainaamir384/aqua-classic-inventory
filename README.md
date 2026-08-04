# Aqua Classic Water Filters Inventory System

Internal Django inventory application for Aqua Classic Water Filters.

## Requirements

- Python 3.11+
- PostgreSQL for production, SQLite for local development

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and adjust values for your environment.
4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Create an owner/admin account:

   ```bash
   python manage.py createsuperuser
   ```

6. Load demo data:

   ```bash
   python manage.py seed_demo_data
   ```

7. Start the server:

   ```bash
   python manage.py runserver
   ```

## Notes

- All pages are login-protected.
- Stock balances are updated transactionally when stock movements are saved.
- Use the Stock Ledger and Reports screens to audit movement history and stock valuation.
