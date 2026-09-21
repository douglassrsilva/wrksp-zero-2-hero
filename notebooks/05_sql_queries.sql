-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 05 — Databricks SQL: KPIs de qualidade de rede
-- MAGIC Conecte o notebook a um SQL Warehouse. As vistas alimentam dashboard, Genie e App.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

CREATE OR REPLACE VIEW IDENTIFIER(:catalog || '.' || :schema || '.v_network_kpis')
COMMENT 'KPIs de qualidade por regiao e tecnologia sobre dados validados pelo DQX'
AS
SELECT
  region,
  technology,
  count(DISTINCT tower_id) AS total_towers,
  round(avg(signal_strength_dbm), 1) AS avg_signal_dbm,
  round(avg(latency_ms), 1) AS avg_latency_ms,
  round(avg(throughput_mbps), 1) AS avg_throughput_mbps,
  sum(dropped_calls) AS total_dropped_calls,
  round(avg(active_users), 0) AS avg_active_users,
  round(100.0 * avg(CASE WHEN latency_ms <= 80 AND throughput_mbps >= 20 AND signal_strength_dbm >= -95 THEN 1 ELSE 0 END), 1) AS sla_compliance_pct
FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated')
GROUP BY region, technology;

-- COMMAND ----------

CREATE OR REPLACE VIEW IDENTIFIER(:catalog || '.' || :schema || '.v_tower_health')
COMMENT 'Saude por torre, incluindo tickets correlacionados'
AS
WITH metrics AS (
  SELECT
    tower_id,
    first(region) AS region,
    first(commune) AS commune,
    first(latitude) AS latitude,
    first(longitude) AS longitude,
    first(environment) AS environment,
    first(technology) AS technology,
    first(frequency_band) AS frequency_band,
    round(avg(signal_strength_dbm), 1) AS avg_signal_dbm,
    round(avg(latency_ms), 1) AS avg_latency_ms,
    round(avg(throughput_mbps), 1) AS avg_throughput_mbps,
    sum(dropped_calls) AS total_dropped_calls,
    round(avg(active_users), 0) AS avg_active_users,
    max(timestamp) AS last_measurement
  FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated')
  GROUP BY tower_id
), tickets AS (
  SELECT
    tower_id,
    count(*) AS total_tickets,
    count_if(status = 'Abierto') AS open_tickets,
    count_if(severity = 'Critica') AS critical_tickets
  FROM IDENTIFIER(:catalog || '.' || :schema || '.support_tickets_silver')
  GROUP BY tower_id
)
SELECT
  m.*,
  coalesce(t.total_tickets, 0) AS total_tickets,
  coalesce(t.open_tickets, 0) AS open_tickets,
  coalesce(t.critical_tickets, 0) AS critical_tickets,
  CASE
    WHEN m.avg_latency_ms > 120 OR m.avg_throughput_mbps < 15 OR m.total_dropped_calls > 700 THEN 'Critico'
    WHEN m.avg_latency_ms > 80 OR m.avg_throughput_mbps < 30 OR m.total_dropped_calls > 400 THEN 'Atencao'
    ELSE 'Saudavel'
  END AS health_status
FROM metrics m
LEFT JOIN tickets t USING (tower_id);

-- COMMAND ----------

CREATE OR REPLACE VIEW IDENTIFIER(:catalog || '.' || :schema || '.v_problem_towers')
COMMENT 'Torres que exigem atencao operacional'
AS
SELECT *
FROM IDENTIFIER(:catalog || '.' || :schema || '.v_tower_health')
WHERE health_status IN ('Critico', 'Atencao');

-- COMMAND ----------

CREATE OR REPLACE VIEW IDENTIFIER(:catalog || '.' || :schema || '.v_hourly_network_trend')
COMMENT 'Tendencia horaria para dashboard e Genie'
AS
SELECT
  date_trunc('hour', timestamp) AS metric_hour,
  region,
  technology,
  round(avg(latency_ms), 1) AS avg_latency_ms,
  round(avg(throughput_mbps), 1) AS avg_throughput_mbps,
  sum(dropped_calls) AS dropped_calls
FROM IDENTIFIER(:catalog || '.' || :schema || '.tower_metrics_validated')
GROUP BY date_trunc('hour', timestamp), region, technology;

-- COMMAND ----------

SELECT * FROM IDENTIFIER(:catalog || '.' || :schema || '.v_network_kpis') ORDER BY region, technology;

-- COMMAND ----------

SELECT * FROM IDENTIFIER(:catalog || '.' || :schema || '.v_problem_towers')
ORDER BY avg_latency_ms DESC, total_dropped_calls DESC
LIMIT 10;
