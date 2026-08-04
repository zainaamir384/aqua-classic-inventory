# Technical Requirements Document (TRD)
# Aqua Classic Water Filters Inventory System

## 1. Stack & Architecture
- **Framework:** Django 6.0.7 (Python 3.14)
- **Database:** SQLite 3 (ORM with strict foreign keys & atomic transactions)
- **Frontend:** HTML5, Vanilla CSS Design System, Bootstrap 5 Modals, Chart.js Visual Graphs
- **Currency:** PKR (`PKR ` formatting via Intl.NumberFormat & Python string format)

## 2. Dynamic Features Implementation
- **Modal Stack Overlay Fix:** `show.bs.modal` event listener in `base.html` auto-relocates modal popups to `document.body` to eliminate z-index stacking conflicts.
- **Stock Deduction Guards:** `product.total_stock <= 0` disables `- Deduct / Sell` button; view raises clean user-friendly alert on shortage.
- **Dynamic Stage Count:** JS toggles `stage_count` input visibility on Add/Edit forms based on category.
- **Table Overflow Rules:** `.table-responsive` enforces rounded card border clipping prevention with left/right cell padding.
