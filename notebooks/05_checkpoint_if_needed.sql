-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Checkpoint de recuperacao
-- MAGIC Execute somente se os modulos Lakeflow/DQX falharem e for necessario continuar no SQL.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

CREATE OR REPLACE TABLE IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_silver') AS
SELECT *,
       to_date(timestamp) AS event_date,
       CASE
         WHEN signal_strength_dbm < -100 OR latency_ms > 120 OR throughput_mbps < 10 THEN 'Critico'
         WHEN signal_strength_dbm < -90 OR latency_ms > 80 THEN 'Atencao'
         ELSE 'Saudavel'
       END AS network_status
FROM IDENTIFIER(:catalog || '.' || :schema || '.cell_tower_metrics_raw_checkpoint');

CREATE OR REPLACE TABLE IDENTIFIER(:catalog || '.' || :schema || '.support_tickets_silver') AS
SELECT *, to_date(created_at) AS created_date
FROM IDENTIFIER(:catalog || '.' || :schema || '.support_tickets_raw_checkpoint');

CREATE OR REPLACE TABLE IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated') AS
SELECT *, CAST(array() AS ARRAY<STRING>) AS _warnings
FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_silver')
WHERE tower_id IS NOT NULL
  AND timestamp IS NOT NULL
  AND signal_strength_dbm BETWEEN -120 AND -40
  AND latency_ms BETWEEN 0 AND 500
  AND throughput_mbps IS NOT NULL
  AND technology IN ('4G', '5G');
