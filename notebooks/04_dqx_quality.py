# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Qualidade de dados com DQX
# MAGIC
# MAGIC DQX e um projeto Databricks Labs, open source e sem SLA de suporte.
# MAGIC Este notebook usa a API atual: `DQEngine` + regras declarativas + quarentena.

# COMMAND ----------

# MAGIC %pip install "databricks-labs-dqx>=0.9,<1" "pyyaml>=6,<7"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catalogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")
dbutils.widgets.text("min_throughput", "1.0", "SLA minimo de throughput")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
min_throughput = float(dbutils.widgets.get("min_throughput"))

# COMMAND ----------

import yaml
from databricks.labs.dqx.engine import DQEngine
from databricks.sdk import WorkspaceClient

checks = yaml.safe_load(
    f"""
- name: tower_id_required
  criticality: error
  check:
    function: is_not_null_and_not_empty
    arguments: {{column: tower_id}}

- name: timestamp_required
  criticality: error
  check:
    function: is_not_null
    arguments: {{column: timestamp}}

- name: signal_in_physical_range
  criticality: error
  check:
    function: is_in_range
    arguments: {{column: signal_strength_dbm, min_limit: -120, max_limit: -40}}

- name: latency_in_physical_range
  criticality: error
  check:
    function: is_in_range
    arguments: {{column: latency_ms, min_limit: 0, max_limit: 500}}

- name: throughput_required
  criticality: error
  check:
    function: is_not_null
    arguments: {{column: throughput_mbps}}

- name: throughput_above_workshop_sla
  criticality: warn
  check:
    function: is_in_range
    arguments: {{column: throughput_mbps, min_limit: {min_throughput}, max_limit: 150}}

- name: technology_allowed
  criticality: error
  check:
    function: is_in_list
    arguments:
      column: technology
      allowed: ["'4G'", "'5G'"]
"""
)

status = DQEngine.validate_checks(checks)
print(f"Regras validadas: {status}")

# COMMAND ----------

source_df = spark.table(f"{catalog}.{schema}.tower_metrics_silver")
dq = DQEngine(WorkspaceClient())

valid_df, quarantine_df = dq.apply_checks_by_metadata_and_split(source_df, checks)

valid_table = f"{catalog}.{schema}.tower_metrics_validated"
quarantine_table = f"{catalog}.{schema}.tower_metrics_quarantine"

valid_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(valid_table)
quarantine_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(quarantine_table)

# COMMAND ----------

from pyspark.sql import functions as F

summary = (
    dq.apply_checks_by_metadata(source_df, checks)
    .select(
        F.count("*").alias("input_rows"),
        F.sum(F.when(F.size("_errors") > 0, 1).otherwise(0)).alias("rows_with_errors"),
        F.sum(F.when(F.size("_warnings") > 0, 1).otherwise(0)).alias("rows_with_warnings"),
        F.sum(F.when((F.size("_errors") == 0) & (F.size("_warnings") == 0), 1).otherwise(0)).alias(
            "rows_without_findings"
        ),
    )
    .withColumn("evaluated_at", F.current_timestamp())
)
summary.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{catalog}.{schema}.dqx_quality_summary"
)

display(summary)
display(quarantine_df.select("tower_id", "timestamp", "_errors", "_warnings").limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercicio
# MAGIC Altere o widget `min_throughput` de `1.0` para `10.0`, execute novamente e
# MAGIC compare `rows_with_warnings`. Erros vao para quarentena; warnings permanecem
# MAGIC na tabela validada, acompanhados da coluna `_warnings`.

