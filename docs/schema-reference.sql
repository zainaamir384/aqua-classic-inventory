-- =============================================================
-- Schema Reference — Aqua Classic Inventory Management System
-- Generated: 2026-07-31
-- Database: SQLite (dev) / PostgreSQL (prod)
-- =============================================================

-- NOTE: This is a REFERENCE file for documentation purposes.
-- Django manages the actual schema via migrations.
-- Do NOT run this file against the database directly.

-- =============================================================
-- ACCOUNTS
-- =============================================================

CREATE TABLE accounts_user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(150) NOT NULL UNIQUE,
    first_name      VARCHAR(150) NOT NULL DEFAULT '',
    last_name       VARCHAR(150) NOT NULL DEFAULT '',
    email           VARCHAR(254) NOT NULL DEFAULT '',
    password        VARCHAR(128) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'STAFF',       -- OWNER | STAFF
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    is_staff        BOOLEAN      NOT NULL DEFAULT 0,
    is_superuser    BOOLEAN      NOT NULL DEFAULT 0,
    date_joined     DATETIME     NOT NULL,
    last_login      DATETIME
);

-- =============================================================
-- CATALOG
-- =============================================================

CREATE TABLE catalog_category (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(120) NOT NULL UNIQUE,
    description     TEXT         NOT NULL DEFAULT '',
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL
);

CREATE TABLE catalog_brand (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(120) NOT NULL UNIQUE,
    origin_label    VARCHAR(120) NOT NULL,
    notes           TEXT         NOT NULL DEFAULT '',
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL
);

CREATE TABLE catalog_product (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 VARCHAR(160) NOT NULL,
    sku                  VARCHAR(64)  NOT NULL UNIQUE,
    category_id          INTEGER      NOT NULL REFERENCES catalog_category(id),
    brand_id             INTEGER      REFERENCES catalog_brand(id),
    configuration        VARCHAR(20)  NOT NULL DEFAULT 'N_A',    -- SINGLE | DUAL | TRIPLE | N_A
    stage_count          INTEGER,                                 -- NULL for non-staged items
    unit_type            VARCHAR(30)  NOT NULL,                   -- FINISHED_UNIT | COMPONENT | SPARE_PART
    unit_of_measure      VARCHAR(40)  NOT NULL DEFAULT 'piece',
    reorder_level        DECIMAL(12,3) NOT NULL DEFAULT 0,
    cost_price           DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    notes                TEXT         NOT NULL DEFAULT '',
    allow_negative_stock BOOLEAN      NOT NULL DEFAULT 0,
    is_active            BOOLEAN      NOT NULL DEFAULT 1,
    created_at           DATETIME     NOT NULL,
    updated_at           DATETIME     NOT NULL
    -- PENDING: pieces_per_box  INTEGER  (for box-to-piece conversion)
);

CREATE TABLE catalog_productcomponent (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER       NOT NULL REFERENCES catalog_product(id) ON DELETE CASCADE,
    component_id    INTEGER       NOT NULL REFERENCES catalog_product(id),
    quantity        DECIMAL(12,3) NOT NULL,
    UNIQUE (product_id, component_id)
);

-- =============================================================
-- INVENTORY
-- =============================================================

CREATE TABLE inventory_location (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(120) NOT NULL UNIQUE,
    code            VARCHAR(20)  NOT NULL UNIQUE,
    address         TEXT         NOT NULL DEFAULT '',
    notes           TEXT         NOT NULL DEFAULT '',
    is_default      BOOLEAN      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL
);

CREATE TABLE inventory_stockitem (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id        INTEGER       NOT NULL REFERENCES catalog_product(id) ON DELETE CASCADE,
    location_id       INTEGER       NOT NULL REFERENCES inventory_location(id) ON DELETE CASCADE,
    quantity_on_hand  DECIMAL(12,3) NOT NULL DEFAULT 0,
    updated_at        DATETIME      NOT NULL,
    UNIQUE (product_id, location_id)
);

CREATE TABLE inventory_stockmovement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER       NOT NULL REFERENCES catalog_product(id),
    location_id     INTEGER       NOT NULL REFERENCES inventory_location(id),
    movement_type   VARCHAR(30)   NOT NULL,
    -- Types: PURCHASE_IN, ASSEMBLY_CONSUME, ASSEMBLY_PRODUCE,
    --        SALE_OUT, ADJUSTMENT_IN, ADJUSTMENT_OUT,
    --        RETURN_IN, DAMAGE_OUT
    quantity        DECIMAL(12,3) NOT NULL,  -- always positive
    reference_note  VARCHAR(255)  NOT NULL DEFAULT '',
    unit_cost       DECIMAL(12,2),
    created_by_id   INTEGER       NOT NULL REFERENCES accounts_user(id),
    created_at      DATETIME      NOT NULL
    -- NOTE: This table is APPEND-ONLY. No updates or deletes allowed.
);

-- =============================================================
-- SUPPLIERS
-- =============================================================

CREATE TABLE suppliers_supplier (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(160) NOT NULL UNIQUE,
    contact_person  VARCHAR(160) NOT NULL DEFAULT '',
    phone           VARCHAR(40)  NOT NULL DEFAULT '',
    address         TEXT         NOT NULL DEFAULT '',
    notes           TEXT         NOT NULL DEFAULT '',
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL
);

CREATE TABLE suppliers_purchaseorder (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id             INTEGER     NOT NULL REFERENCES suppliers_supplier(id),
    order_date              DATE        NOT NULL,
    expected_delivery_date  DATE,
    status                  VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING | PARTIAL | RECEIVED
    notes                   TEXT        NOT NULL DEFAULT '',
    created_by_id           INTEGER     NOT NULL REFERENCES accounts_user(id),
    created_at              DATETIME    NOT NULL
);

CREATE TABLE suppliers_purchaseorderlineitem (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_order_id   INTEGER       NOT NULL REFERENCES suppliers_purchaseorder(id) ON DELETE CASCADE,
    product_id          INTEGER       NOT NULL REFERENCES catalog_product(id),
    ordered_qty         DECIMAL(12,3) NOT NULL,
    received_qty        DECIMAL(12,3) NOT NULL DEFAULT 0,
    unit_cost           DECIMAL(12,2)
    -- PENDING: ordered_boxes  INTEGER  (for box-entry flow)
);

-- =============================================================
-- SALES
-- =============================================================

CREATE TABLE sales_salerecord (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date       DATE          NOT NULL,
    location_id     INTEGER       NOT NULL REFERENCES inventory_location(id),
    customer_name   VARCHAR(160)  NOT NULL DEFAULT '',
    customer_phone  VARCHAR(40)   NOT NULL DEFAULT '',
    notes           TEXT          NOT NULL DEFAULT '',
    total_amount    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    created_by_id   INTEGER       NOT NULL REFERENCES accounts_user(id),
    created_at      DATETIME      NOT NULL
);

CREATE TABLE sales_saleitem (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id         INTEGER       NOT NULL REFERENCES sales_salerecord(id) ON DELETE CASCADE,
    product_id      INTEGER       NOT NULL REFERENCES catalog_product(id),
    quantity        DECIMAL(12,3) NOT NULL,
    sale_price      DECIMAL(12,2) NOT NULL
);
