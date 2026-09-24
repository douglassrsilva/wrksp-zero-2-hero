-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Punto de recuperación
-- MAGIC Ejecútelo únicamente si Lakeflow/DQX fallan y es necesario continuar con SQL.
-- MAGIC Crea las once Silver desde los checkpoints Delta y seis pares
-- MAGIC `validated`/`quarantine`. Los objetos usan el sufijo `_fallback` durante la
-- MAGIC transformación y publican los contratos que Gold espera.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

CREATE OR REPLACE TABLE network_sites_silver_fallback AS
SELECT * FROM network_sites_raw_checkpoint QUALIFY row_number() OVER (PARTITION BY site_id ORDER BY commissioned_date DESC) = 1;

CREATE OR REPLACE TABLE radio_cells_silver_fallback AS
SELECT * FROM radio_cells_raw_checkpoint QUALIFY row_number() OVER (PARTITION BY cell_id ORDER BY site_id) = 1;

CREATE OR REPLACE TABLE products_silver_fallback AS
SELECT * FROM products_raw_checkpoint QUALIFY row_number() OVER (PARTITION BY product_id ORDER BY valid_from DESC) = 1;

CREATE OR REPLACE TABLE customers_silver_fallback AS
SELECT *, CAST(floor(months_between(DATE'2026-08-14', created_date)) AS INT) AS tenure_months
FROM customers_raw_checkpoint
QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY created_date DESC) = 1;

CREATE OR REPLACE TABLE subscriptions_silver_fallback AS
SELECT s.*, c.customer_type, c.customer_segment, c.region, c.commune, c.age_band,
       c.digital_engagement_score, c.customer_status, p.product_name, p.product_family,
       p.data_allowance_gb, p.unlimited_data, p.is_5g_enabled, p.product_status
FROM subscriptions_raw_checkpoint s
LEFT JOIN customers_silver_fallback c USING (customer_id)
LEFT JOIN products_silver_fallback p USING (product_id)
QUALIFY row_number() OVER (PARTITION BY subscription_id ORDER BY start_date DESC) = 1;

CREATE OR REPLACE TABLE cell_tower_metrics_silver_fallback AS
SELECT m.*, c.site_id, c.technology, c.frequency_band, c.bandwidth_mhz, c.capacity_users,
       s.region, s.commune, s.environment, s.latitude, s.longitude,
       to_date(m.event_ts) AS event_date, date_trunc('hour', m.event_ts) AS event_hour,
       CASE WHEN m.availability_pct < 99 OR m.latency_ms > 120 OR m.downlink_mbps < 10 THEN 'Crítico'
            WHEN m.latency_ms > 80 OR m.downlink_mbps < 25 THEN 'Atención' ELSE 'Saludable' END AS network_status
FROM cell_tower_metrics_raw_checkpoint m
LEFT JOIN radio_cells_silver_fallback c USING (cell_id)
LEFT JOIN network_sites_silver_fallback s USING (site_id)
QUALIFY row_number() OVER (PARTITION BY measurement_id ORDER BY event_ts DESC) = 1;

CREATE OR REPLACE TABLE network_alarms_silver_fallback AS
SELECT a.*, c.site_id, c.technology, s.region, s.commune, to_date(a.opened_at) AS opened_date
FROM network_alarms_raw_checkpoint a
LEFT JOIN radio_cells_silver_fallback c USING (cell_id)
LEFT JOIN network_sites_silver_fallback s USING (site_id)
QUALIFY row_number() OVER (PARTITION BY alarm_id ORDER BY opened_at DESC) = 1;

CREATE OR REPLACE TABLE maintenance_orders_silver_fallback AS
SELECT o.*, s.region, s.commune, s.environment, to_date(o.created_at) AS created_date
FROM maintenance_orders_raw_checkpoint o LEFT JOIN network_sites_silver_fallback s USING (site_id)
QUALIFY row_number() OVER (PARTITION BY work_order_id ORDER BY created_at DESC) = 1;

CREATE OR REPLACE TABLE usage_daily_silver_fallback AS
SELECT u.*, sub.customer_id, sub.product_id, sub.line_id, sub.subscription_status,
       sub.contract_type, sub.monthly_fee_clp, sub.customer_type, sub.customer_segment,
       sub.digital_engagement_score, sub.customer_status, sub.region AS customer_region,
       sub.commune AS customer_commune, sub.product_name, sub.product_family,
       sub.data_allowance_gb, sub.unlimited_data, c.site_id, c.technology, c.frequency_band,
       ns.region AS network_region, ns.commune AS network_commune
FROM usage_daily_raw_checkpoint u
LEFT JOIN subscriptions_silver_fallback sub USING (subscription_id)
LEFT JOIN radio_cells_silver_fallback c ON u.primary_cell_id = c.cell_id
LEFT JOIN network_sites_silver_fallback ns USING (site_id)
QUALIFY row_number() OVER (PARTITION BY usage_date, subscription_id ORDER BY ingestion_batch_id DESC) = 1;

CREATE OR REPLACE TABLE support_tickets_silver_fallback AS
SELECT t.*, sub.product_id, sub.product_name, sub.product_family, sub.customer_type,
       sub.customer_segment, sub.contract_type, c.site_id, c.technology,
       coalesce(ns.region, sub.region) AS region, coalesce(ns.commune, sub.commune) AS commune,
       to_date(t.created_at) AS created_date,
       t.resolution_hours IS NOT NULL AND t.resolution_hours <= t.sla_target_hours AS sla_met
FROM support_tickets_raw_checkpoint t
LEFT JOIN subscriptions_silver_fallback sub USING (subscription_id)
LEFT JOIN radio_cells_silver_fallback c USING (cell_id)
LEFT JOIN network_sites_silver_fallback ns USING (site_id)
QUALIFY row_number() OVER (PARTITION BY ticket_id ORDER BY created_at DESC) = 1;

CREATE OR REPLACE TABLE customer_surveys_silver_fallback AS
SELECT e.*, sub.product_id, sub.product_name, sub.product_family, sub.customer_type,
       sub.customer_segment, sub.region, sub.commune,
       CASE WHEN e.nps_score >= 9 THEN 'Promotor' WHEN e.nps_score >= 7 THEN 'Pasivo' ELSE 'Detractor' END AS nps_class
FROM customer_surveys_raw_checkpoint e LEFT JOIN subscriptions_silver_fallback sub USING (subscription_id)
QUALIFY row_number() OVER (PARTITION BY survey_id ORDER BY response_date DESC) = 1;

-- La contingencia SQL usa las mismas condiciones críticas que DQX.
CREATE OR REPLACE TABLE cell_tower_metrics_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _errors, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM cell_tower_metrics_silver_fallback
WHERE measurement_id IS NOT NULL AND cell_id IS NOT NULL AND site_id IS NOT NULL
  AND availability_pct BETWEEN 0 AND 100 AND signal_strength_dbm BETWEEN -120 AND -40
  AND latency_ms BETWEEN 0 AND 500 AND downlink_mbps IS NOT NULL AND technology IN ('4G', '5G');
CREATE OR REPLACE TABLE cell_tower_metrics_quarantine AS
SELECT * FROM cell_tower_metrics_silver_fallback WHERE NOT (
  measurement_id IS NOT NULL AND cell_id IS NOT NULL AND site_id IS NOT NULL
  AND availability_pct BETWEEN 0 AND 100 AND signal_strength_dbm BETWEEN -120 AND -40
  AND latency_ms BETWEEN 0 AND 500 AND downlink_mbps IS NOT NULL AND technology IN ('4G', '5G'));

CREATE OR REPLACE TABLE subscriptions_validated AS SELECT * FROM subscriptions_silver_fallback
WHERE subscription_id IS NOT NULL AND customer_segment IS NOT NULL AND product_name IS NOT NULL
  AND monthly_fee_clp BETWEEN 0 AND 1000000 AND subscription_status IN ('Activa', 'Suspendida', 'Baja');
CREATE OR REPLACE TABLE subscriptions_quarantine AS SELECT * FROM subscriptions_silver_fallback
WHERE NOT (subscription_id IS NOT NULL AND customer_segment IS NOT NULL AND product_name IS NOT NULL
  AND monthly_fee_clp BETWEEN 0 AND 1000000 AND subscription_status IN ('Activa', 'Suspendida', 'Baja'));

CREATE OR REPLACE TABLE usage_daily_validated AS SELECT * FROM usage_daily_silver_fallback
WHERE usage_date IS NOT NULL AND customer_id IS NOT NULL AND site_id IS NOT NULL
  AND data_gb BETWEEN 0 AND 1000 AND data_5g_pct BETWEEN 0 AND 100;
CREATE OR REPLACE TABLE usage_daily_quarantine AS SELECT * FROM usage_daily_silver_fallback
WHERE NOT (usage_date IS NOT NULL AND customer_id IS NOT NULL AND site_id IS NOT NULL
  AND data_gb BETWEEN 0 AND 1000 AND data_5g_pct BETWEEN 0 AND 100);

CREATE OR REPLACE TABLE support_tickets_validated AS SELECT * FROM support_tickets_silver_fallback
WHERE ticket_id IS NOT NULL AND category IS NOT NULL AND product_name IS NOT NULL
  AND ticket_status IN ('Abierto', 'En progreso', 'Resuelto', 'Cerrado');
CREATE OR REPLACE TABLE support_tickets_quarantine AS SELECT * FROM support_tickets_silver_fallback
WHERE NOT (ticket_id IS NOT NULL AND category IS NOT NULL AND product_name IS NOT NULL
  AND ticket_status IN ('Abierto', 'En progreso', 'Resuelto', 'Cerrado'));

CREATE OR REPLACE TABLE network_alarms_validated AS SELECT * FROM network_alarms_silver_fallback
WHERE alarm_id IS NOT NULL AND site_id IS NOT NULL AND severity IN ('Crítica', 'Alta', 'Media', 'Baja');
CREATE OR REPLACE TABLE network_alarms_quarantine AS SELECT * FROM network_alarms_silver_fallback
WHERE NOT (alarm_id IS NOT NULL AND site_id IS NOT NULL AND severity IN ('Crítica', 'Alta', 'Media', 'Baja'));

CREATE OR REPLACE TABLE customer_surveys_validated AS SELECT * FROM customer_surveys_silver_fallback
WHERE survey_id IS NOT NULL AND product_name IS NOT NULL AND nps_score BETWEEN 0 AND 10 AND csat_score BETWEEN 1 AND 5;
CREATE OR REPLACE TABLE customer_surveys_quarantine AS SELECT * FROM customer_surveys_silver_fallback
WHERE NOT (survey_id IS NOT NULL AND product_name IS NOT NULL AND nps_score BETWEEN 0 AND 10 AND csat_score BETWEEN 1 AND 5);
