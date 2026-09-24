-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 — Unity Catalog
-- MAGIC Secuencia Tell–Show–Tell: jerarquía, demostración, ejercicio y verificación.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

-- El catálogo debe ser preparado por el instructor. Crear catálogos dentro del
-- workshop depende de storage root y privilegios de metastore.
DESCRIBE CATALOG EXTENDED IDENTIFIER(:catalog);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema);
CREATE VOLUME IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_data');

-- COMMAND ----------

DESCRIBE CATALOG EXTENDED IDENTIFIER(:catalog);

-- COMMAND ----------

SHOW SCHEMAS IN IDENTIFIER(:catalog);

-- COMMAND ----------

SHOW VOLUMES IN IDENTIFIER(:catalog || '.' || :schema);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Verificación
-- MAGIC Confirme en Catalog Explorer la jerarquía `catálogo > schema > volumen raw_data`.
-- MAGIC Después ejecute `00_setup.py` para llenar el volumen y crear los puntos de contingencia.
