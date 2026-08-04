# Business Logic Reference
# Aqua Classic Water Filters (Pakistan)

## 1. Currency & Pricing Rules
- Currency is strictly **PKR** (Pakistani Rupee).
- All stock additions capture unit purchase cost and log into purchase history.
- All stock deductions capture unit sale price and log into sales history under Walk-in Customer or Salesman.

## 2. Stock Ledger Rules (Option A)
- Stock In/Out is an immutable, read-only audit log.
- All inventory changes are initiated from the Products Catalog page via modal forms.
- Deductions are blocked when stock is 0.

## 3. Product Catalog & Packaging Rules
- 13 official categories.
- Standard Triple Water Filter BOM: 2 PPF + 1 CTO + 3 Housings + 3 Heads + 1 Plate.
- 10" & 20" Slim UDF cartridges are reserved for RO systems.
- Assembled units support dynamic stage counting (1..8).
