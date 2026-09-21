# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Preparacao e geracao dos dados sinteticos
# MAGIC
# MAGIC Gera 5.000 medicoes de rede e 500 tickets ficticios com PySpark nativo.
# MAGIC O notebook cria um volume do Unity Catalog, grava CSVs para o Lakeflow e
# MAGIC mantem tabelas Delta de contingencia. Execute uma vez antes da oficina.

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catalogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")
dbutils.widgets.text("seed", "42", "Seed")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
seed = int(dbutils.widgets.get("seed"))

assert catalog.replace("_", "").isalnum(), "Nome de catalogo invalido"
assert schema.replace("_", "").isalnum(), "Nome de schema invalido"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unity Catalog
# MAGIC Se voce nao tem `CREATE CATALOG`, troque o widget `catalog` pelo catalogo compartilhado do instrutor.

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`raw_data`")

volume_root = f"/Volumes/{catalog}/{schema}/raw_data"
print(f"Volume de entrada: {volume_root}")

# COMMAND ----------

import sys
from pathlib import Path

for candidate in (Path.cwd() / "src", Path.cwd().parent / "src"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))
        break

from telco_workshop.generator import build_support_tickets, build_tower_metrics

metrics = build_tower_metrics(spark, seed=seed)
tickets = build_support_tickets(spark, metrics, seed=seed)

assert metrics.count() == 5_000
assert tickets.count() == 500

display(metrics.limit(10))
display(tickets.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Landing zone em CSV
# MAGIC Os diretórios abaixo sao lidos pelo Auto Loader no pipeline Lakeflow.

# COMMAND ----------

(
    metrics.coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
    .csv(f"{volume_root}/cell_tower_metrics")
)
(
    tickets.coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
    .csv(f"{volume_root}/support_tickets")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Checkpoint de contingencia
# MAGIC Estas tabelas permitem continuar o workshop mesmo que Lakeflow nao esteja disponivel.

# COMMAND ----------

metrics.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{catalog}.{schema}.cell_tower_metrics_raw_checkpoint"
)
tickets.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{catalog}.{schema}.support_tickets_raw_checkpoint"
)

summary = spark.sql(
    f"""
    SELECT 'metricas' AS dataset, count(*) AS linhas
      FROM `{catalog}`.`{schema}`.`cell_tower_metrics_raw_checkpoint`
    UNION ALL
    SELECT 'tickets', count(*)
      FROM `{catalog}`.`{schema}`.`support_tickets_raw_checkpoint`
    """
)
display(summary)
