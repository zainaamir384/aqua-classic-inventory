# Aqua Classic Inventory Management System — Master Execution Prompt

> **System Status:** Production Ready | Tailored for Aqua Classic Water Filters (Pakistan)

---

## Core Execution Rules & Specifications

### 1. Currency & Formatting
- **Currency:** PKR (`PKR ` prefix across all dashboards, reports, and transactions).
- **Number Format:** Quantities formatted as integers (`200 pcs`), prices formatted to 2 decimal places (`PKR 1,500.00`).

### 2. Master Product & Category Structure
- **Cartridge & Parts Categories:** Cartridges 10 inch, Cartridges 20 inch Slim, Cartridges 20 inch Jumbo, Housings 10 inch, Housings 20 inch Slim, Housings 20 inch Jumbo, RO Housings, RO Filters, RO Cartridges, RO Accessories, RO Parts & Electricals.
- **Official 4 Assembled Categories:**
  1. `10" Water Filter (Assembled)`
  2. `20" Slim Water Filter (Assembled)`
  3. `20" Jumbo Water Filter (Assembled)`
  4. `RO Water Filter (Assembled)`

### 3. Housing Wrenches Allocation
- **10" Standard Housing Wrench** $\rightarrow$ `Housings 10 inch`
- **20" Slim Housing Wrench** $\rightarrow$ `Housings 20 inch Slim`
- **20" Jumbo Housing Wrench** $\rightarrow$ `Housings 20 inch Jumbo`
- **RO Housing Wrench** $\rightarrow$ `RO Housings`

### 4. Assembled Units Hub (`/inventory/assemble/`)
- **Header Action:** `+ Add Assembled Unit` button opens popup build modal.
- **Assembled Inventory Table:** Placed directly below the header with category filtering.
- **Configuration Set Field:** Hidden by default. Shows `Single`, `Dual`, `Triple` ONLY when Water Filters are selected. Hidden for RO Systems.
- **Stage Count Field:** Compulsory for RO Systems.
- **Table RO Configuration:** RO Systems display `Triple` by default under Set Configuration.
- **Delete Redirect:** Preserves `next` URL so deleting from Assembled Hub returns to Assembled Hub.
- **Sorting Order:** Products across Inventory and Assembled pages are sorted by `-updated_at`, `-id` so updated/created items appear at the very top.
