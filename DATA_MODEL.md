# Data Model Overview

This system tracks inventory for domestic water-filter assembly and sales.

## Catalog

- `Category` groups products such as Basic Filter, RO Filter, RO Parts, Cartridges, and Alkaline/Add-on.
- `Brand` stores reusable origin or quality labels such as Local, China, Vietnam, or Imported-Generic.
- `Product` stores each stockable item with a SKU, category, brand, unit type, stage count, configuration, reorder level, and cost.
- `ProductComponent` defines the bill of materials for a finished unit. It says how many of each component are needed to build one finished product.

## Inventory

- `Location` represents a shop branch or storage place. The app defaults to a single Main Shop location, but it is not limited to one.
- `StockMovement` is the audit ledger. Every stock change is written here as an append-only row.
- `StockItem` stores the current balance for each product and location. It is updated transactionally when a new movement is recorded.

## How Assembly Works

When an owner or staff member assembles a finished unit, the app:

1. Checks the product BOM.
2. Verifies that all required components are available.
3. Writes component-consumption movements.
4. Writes a production movement for the finished unit.

If any required component is short, the whole action is blocked.

## Purchase Orders and Sales

- Purchase orders record incoming stock from suppliers.
- Sales records track stock leaving the shop.
- Both flows generate stock movements so the ledger always matches business activity.

## Stock Balance Rule

The system keeps `StockItem.quantity_on_hand` in sync inside the same transaction that creates a stock movement. If you ever need to rebuild balances from the ledger, use the `rebuild_stock_balances` management command.
