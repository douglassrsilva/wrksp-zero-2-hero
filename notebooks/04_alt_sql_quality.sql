-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 04 alternativa — Qualidade com SQL
-- MAGIC Use se a biblioteca DQX nao puder ser instalada.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

CREATE OR REPLACE TABLE IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_quarantine') AS
SELECT *,
       array_compact(array(
         CASE WHEN tower_id IS NULL OR trim(tower_id) = '' THEN 'tower_id_required' END,
         CASE WHEN timestamp IS NULL THEN 'timestamp_required' END,
         CASE WHEN signal_strength_dbm NOT BETWEEN -120 AND -40 THEN 'signal_in_physical_range' END,
         CASE WHEN latency_ms NOT BETWEEN 0 AND 500 THEN 'latency_in_physical_range' END,
         CASE WHEN throughput_mbps IS NULL THEN 'throughput_required' END,
         CASE WHEN technology NOT IN ('4G', '5G') THEN 'technology_allowed' END
       )) AS failed_rules
FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_silver')
WHERE tower_id IS NULL OR trim(tower_id) = ''
   OR timestamp IS NULL
   OR signal_strength_dbm NOT BETWEEN -120 AND -40
   OR latency_ms NOT BETWEEN 0 AND 500
   OR throughput_mbps IS NULL
   OR technology NOT IN ('4G', '5G');

-- COMMAND ----------

CREATE OR REPLACE TABLE IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated') AS
SELECT *,
       CASE WHEN throughput_mbps < 1.0 THEN array('throughput_above_workshop_sla') ELSE array() END AS _warnings
FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_silver')
WHERE tower_id IS NOT NULL AND trim(tower_id) <> ''
  AND timestamp IS NOT NULL
  AND signal_strength_dbm BETWEEN -120 AND -40
  AND latency_ms BETWEEN 0 AND 500
  AND throughput_mbps IS NOT NULL
  AND technology IN ('4G', '5G');

-- COMMAND ----------

SELECT
  (SELECT count(*) FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_silver')) AS input_rows,
  (SELECT count(*) FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated')) AS valid_rows,
  (SELECT count(*) FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_quarantine')) AS quarantined_rows;

