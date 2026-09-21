# Databricks notebook source
# MAGIC %md
# MAGIC # 02.1 — Ler e validar os CSVs do Volume
# MAGIC
# MAGIC Execute depois de `00_setup.py`. Este exercício mostra a leitura em batch com
# MAGIC PySpark antes de o Lakeflow fazer a ingestão incremental com Auto Loader.

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catalogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
volume_root = f"/Volumes/{catalog}/{schema}/raw_data"

metrics_path = f"{volume_root}/cell_tower_metrics"
tickets_path = f"{volume_root}/support_tickets"

print(f"Metricas: {metrics_path}")
print(f"Tickets:  {tickets_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Ler métricas das torres
# MAGIC `header=true` usa a primeira linha como nomes das colunas. `inferSchema=true`
# MAGIC é adequado para esta amostra pequena; no pipeline usaremos schema explícito.

# COMMAND ----------

metrics_df = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load(metrics_path)
)

metrics_df.printSchema()
print(f"Linhas de métricas: {metrics_df.count():,}")
display(metrics_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Ler tickets de suporte

# COMMAND ----------

tickets_df = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load(tickets_path)
)

tickets_df.printSchema()
print(f"Linhas de tickets: {tickets_df.count():,}")
display(tickets_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Verificar integridade básica
# MAGIC O resultado esperado é 5.000 métricas, 500 tickets e 50 torres fictícias.

# COMMAND ----------

from pyspark.sql import functions as F

validation = metrics_df.agg(
    F.count("*").alias("metric_rows"),
    F.countDistinct("tower_id").alias("distinct_towers"),
    F.min("timestamp").alias("first_measurement"),
    F.max("timestamp").alias("last_measurement"),
).crossJoin(tickets_df.agg(F.count("*").alias("ticket_rows")))

display(validation)

row = validation.first()
assert row.metric_rows == 5_000, f"Esperado 5.000; obtido {row.metric_rows}"
assert row.ticket_rows == 500, f"Esperado 500; obtido {row.ticket_rows}"
assert row.distinct_towers == 50, f"Esperado 50; obtido {row.distinct_towers}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Consultar com SQL sem criar tabela
# MAGIC As views temporárias existem apenas nesta sessão e ajudam a comparar PySpark e SQL.

# COMMAND ----------

metrics_df.createOrReplaceTempView("csv_tower_metrics")
tickets_df.createOrReplaceTempView("csv_support_tickets")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT region, technology,
# MAGIC        count(*) AS measurements,
# MAGIC        round(avg(latency_ms), 1) AS avg_latency_ms,
# MAGIC        round(avg(throughput_mbps), 1) AS avg_throughput_mbps
# MAGIC FROM csv_tower_metrics
# MAGIC GROUP BY region, technology
# MAGIC ORDER BY region, technology;

