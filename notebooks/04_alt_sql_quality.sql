-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 04 alternativa — Calidad con SQL
-- MAGIC Úselo si la biblioteca DQX no puede instalarse. Mantiene el flujo del workshop,
-- MAGIC pero no sustituye las capacidades declarativas y reutilizables de DQX.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

USE CATALOG IDENTIFIER(:catalog);
USE SCHEMA IDENTIFIER(:schema);

-- COMMAND ----------

CREATE OR REPLACE TABLE cell_tower_metrics_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN measurement_id IS NULL OR trim(measurement_id) = '' THEN 'measurement_id_required' END,
  CASE WHEN cell_id IS NULL OR trim(cell_id) = '' THEN 'cell_id_required' END,
  CASE WHEN site_id IS NULL THEN 'cell_resolved' END,
  CASE WHEN availability_pct NOT BETWEEN 0 AND 100 THEN 'availability_range' END,
  CASE WHEN signal_strength_dbm NOT BETWEEN -120 AND -40 THEN 'signal_range' END,
  CASE WHEN latency_ms NOT BETWEEN 0 AND 500 THEN 'latency_range' END,
  CASE WHEN downlink_mbps IS NULL OR downlink_mbps < 0 THEN 'downlink_required' END
)) AS failed_rules
FROM cell_tower_metrics_silver_fallback
WHERE measurement_id IS NULL OR trim(measurement_id) = ''
   OR cell_id IS NULL OR trim(cell_id) = '' OR site_id IS NULL
   OR availability_pct NOT BETWEEN 0 AND 100
   OR signal_strength_dbm NOT BETWEEN -120 AND -40
   OR latency_ms NOT BETWEEN 0 AND 500
   OR downlink_mbps IS NULL OR downlink_mbps < 0;

CREATE OR REPLACE TABLE cell_tower_metrics_validated AS
SELECT *, CASE WHEN downlink_mbps < 20 THEN array('downlink_workshop_sla') ELSE array() END AS _warnings
FROM cell_tower_metrics_silver_fallback
WHERE measurement_id IS NOT NULL AND trim(measurement_id) <> ''
  AND cell_id IS NOT NULL AND trim(cell_id) <> '' AND site_id IS NOT NULL
  AND availability_pct BETWEEN 0 AND 100
  AND signal_strength_dbm BETWEEN -120 AND -40
  AND latency_ms BETWEEN 0 AND 500
  AND downlink_mbps IS NOT NULL AND downlink_mbps >= 0;

-- COMMAND ----------

CREATE OR REPLACE TABLE subscriptions_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN subscription_id IS NULL THEN 'subscription_id_required' END,
  CASE WHEN customer_segment IS NULL THEN 'customer_resolved' END,
  CASE WHEN product_name IS NULL THEN 'product_resolved' END,
  CASE WHEN end_date < start_date THEN 'dates_consistent' END,
  CASE WHEN monthly_fee_clp < 0 THEN 'monthly_fee_non_negative' END
)) AS failed_rules
FROM subscriptions_silver_fallback
WHERE subscription_id IS NULL OR customer_segment IS NULL OR product_name IS NULL
   OR end_date < start_date OR monthly_fee_clp < 0;

CREATE OR REPLACE TABLE subscriptions_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM subscriptions_silver_fallback
WHERE subscription_id IS NOT NULL AND customer_segment IS NOT NULL AND product_name IS NOT NULL
  AND (end_date IS NULL OR end_date >= start_date) AND monthly_fee_clp >= 0;

-- COMMAND ----------

CREATE OR REPLACE TABLE usage_daily_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN customer_id IS NULL THEN 'subscription_resolved' END,
  CASE WHEN site_id IS NULL THEN 'cell_resolved' END,
  CASE WHEN data_gb < 0 THEN 'data_non_negative' END,
  CASE WHEN data_5g_pct NOT BETWEEN 0 AND 100 THEN 'data_5g_range' END
)) AS failed_rules
FROM usage_daily_silver_fallback
WHERE customer_id IS NULL OR site_id IS NULL OR data_gb < 0 OR data_5g_pct NOT BETWEEN 0 AND 100;

CREATE OR REPLACE TABLE usage_daily_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM usage_daily_silver_fallback
WHERE customer_id IS NOT NULL AND site_id IS NOT NULL
  AND data_gb >= 0 AND data_5g_pct BETWEEN 0 AND 100;

-- COMMAND ----------

CREATE OR REPLACE TABLE support_tickets_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN ticket_id IS NULL THEN 'ticket_id_required' END,
  CASE WHEN category IS NULL THEN 'category_required' END,
  CASE WHEN product_name IS NULL THEN 'subscription_resolved' END,
  CASE WHEN resolved_at < created_at THEN 'dates_consistent' END,
  CASE WHEN resolution_hours < 0 THEN 'resolution_non_negative' END
)) AS failed_rules
FROM support_tickets_silver_fallback
WHERE ticket_id IS NULL OR category IS NULL OR product_name IS NULL
   OR resolved_at < created_at OR resolution_hours < 0;

CREATE OR REPLACE TABLE support_tickets_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM support_tickets_silver_fallback
WHERE ticket_id IS NOT NULL AND category IS NOT NULL AND product_name IS NOT NULL
  AND (resolved_at IS NULL OR resolved_at >= created_at)
  AND (resolution_hours IS NULL OR resolution_hours >= 0);

-- COMMAND ----------

CREATE OR REPLACE TABLE network_alarms_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN alarm_id IS NULL THEN 'alarm_id_required' END,
  CASE WHEN site_id IS NULL THEN 'cell_resolved' END,
  CASE WHEN severity NOT IN ('Crítica', 'Alta', 'Media', 'Baja') THEN 'severity_allowed' END,
  CASE WHEN closed_at < opened_at THEN 'dates_consistent' END
)) AS failed_rules
FROM network_alarms_silver_fallback
WHERE alarm_id IS NULL OR site_id IS NULL
   OR severity NOT IN ('Crítica', 'Alta', 'Media', 'Baja')
   OR closed_at < opened_at;

CREATE OR REPLACE TABLE network_alarms_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM network_alarms_silver_fallback
WHERE alarm_id IS NOT NULL AND site_id IS NOT NULL
  AND severity IN ('Crítica', 'Alta', 'Media', 'Baja')
  AND (closed_at IS NULL OR closed_at >= opened_at);

-- COMMAND ----------

CREATE OR REPLACE TABLE customer_surveys_quarantine AS
SELECT *, array_compact(array(
  CASE WHEN survey_id IS NULL THEN 'survey_id_required' END,
  CASE WHEN product_name IS NULL THEN 'subscription_resolved' END,
  CASE WHEN nps_score NOT BETWEEN 0 AND 10 THEN 'nps_range' END,
  CASE WHEN csat_score NOT BETWEEN 1 AND 5 THEN 'csat_range' END
)) AS failed_rules
FROM customer_surveys_silver_fallback
WHERE survey_id IS NULL OR product_name IS NULL
   OR nps_score NOT BETWEEN 0 AND 10 OR csat_score NOT BETWEEN 1 AND 5;

CREATE OR REPLACE TABLE customer_surveys_validated AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM customer_surveys_silver_fallback
WHERE survey_id IS NOT NULL AND product_name IS NOT NULL
  AND nps_score BETWEEN 0 AND 10 AND csat_score BETWEEN 1 AND 5;

-- COMMAND ----------

SELECT 'cell_tower_metrics' AS dataset, count(*) AS quarantine_rows FROM cell_tower_metrics_quarantine
UNION ALL SELECT 'subscriptions', count(*) FROM subscriptions_quarantine
UNION ALL SELECT 'usage_daily', count(*) FROM usage_daily_quarantine
UNION ALL SELECT 'support_tickets', count(*) FROM support_tickets_quarantine
UNION ALL SELECT 'network_alarms', count(*) FROM network_alarms_quarantine
UNION ALL SELECT 'customer_surveys', count(*) FROM customer_surveys_quarantine
ORDER BY dataset;
