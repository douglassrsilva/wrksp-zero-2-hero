-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 — Unity Catalog
-- MAGIC Sequencia Tell–Show–Tell: hierarquia, demonstracao, exercicio e verificacao.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT "telco_workshop";
CREATE WIDGET TEXT schema DEFAULT "red_calidad";

-- COMMAND ----------

-- Se CREATE CATALOG nao for permitido, informe no widget um catalogo compartilhado ja existente.
CREATE CATALOG IF NOT EXISTS IDENTIFIER(:catalog);
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
-- MAGIC ## Verificacao
-- MAGIC Confirme no Catalog Explorer a hierarquia `catalogo > schema > volume raw_data`.
-- MAGIC Depois execute `00_setup.py` para preencher o volume e criar os checkpoints.

