# Databricks notebook source
# MAGIC %md
# MAGIC # 03 alternativa — ETL PySpark sem Lakeflow
# MAGIC Execute somente se Lakeflow Declarative Pipelines nao estiver disponivel.

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catalogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
raw_root = f"/Volumes/{catalog}/{schema}/raw_data"

# COMMAND ----------

from pyspark.sql import functions as F

metrics = spark.read.option("header", True).option("inferSchema", True).csv(f"{raw_root}/cell_tower_metrics")
tickets = spark.read.option("header", True).option("inferSchema", True).csv(f"{raw_root}/support_tickets")

metrics.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(f"{catalog}.{schema}.tower_metrics_bronze")
tickets.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(f"{catalog}.{schema}.support_tickets_bronze")

# COMMAND ----------

metrics_silver = (
    metrics.withColumn("event_date", F.to_date("timestamp"))
    .withColumn(
        "network_status",
        F.when(
            (F.col("signal_strength_dbm") < -100)
            | (F.col("latency_ms") > 120)
            | (F.col("throughput_mbps") < 10),
            "Critico",
        )
        .when((F.col("signal_strength_dbm") < -90) | (F.col("latency_ms") > 80), "Atencao")
        .otherwise("Saudavel"),
    )
)
tickets_silver = tickets.withColumn("created_date", F.to_date("created_at"))

metrics_silver.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.{schema}.tower_metrics_silver"
)
tickets_silver.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.{schema}.support_tickets_silver"
)

# COMMAND ----------

display(
    spark.sql(
        f"""
        SELECT 'tower_metrics_silver' AS tabela, count(*) AS linhas
          FROM `{catalog}`.`{schema}`.`tower_metrics_silver`
        UNION ALL
        SELECT 'support_tickets_silver', count(*)
          FROM `{catalog}`.`{schema}`.`support_tickets_silver`
        """
    )
)

