-- Sample source database for local demos (runs once, on first start of pg-source).
-- Intentionally includes things the Check screen should flag:
--   * sales.order_items and public.audit_raw have no primary key
--   * a timestamptz column (lossy when the target is MySQL)

CREATE SCHEMA sales;

CREATE TABLE sales.customers (
    customer_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       varchar(255) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sales.orders (
    order_id    bigint PRIMARY KEY,
    customer_id integer NOT NULL REFERENCES sales.customers (customer_id),
    total       numeric(10, 2) NOT NULL,
    placed_at   timestamptz NOT NULL
);

CREATE TABLE sales.order_items (
    order_id bigint NOT NULL,
    sku      text NOT NULL,
    qty      integer NOT NULL
);

CREATE TABLE public.audit_raw (payload jsonb);

INSERT INTO sales.customers (email)
SELECT 'customer' || g || '@example.com' FROM generate_series(1, 20000) AS g;

INSERT INTO sales.orders (order_id, customer_id, total, placed_at)
SELECT g, 1 + g % 20000, (g % 500) + 0.99, now() - (g || ' minutes')::interval
FROM generate_series(1, 120000) AS g;

INSERT INTO sales.order_items (order_id, sku, qty)
SELECT 1 + g % 120000, 'SKU-' || (g % 900), 1 + g % 3 FROM generate_series(1, 300000) AS g;

ANALYZE;
