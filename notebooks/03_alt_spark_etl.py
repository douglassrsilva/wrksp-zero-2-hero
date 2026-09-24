# Databricks notebook source
# MAGIC %md
# MAGIC # 03 alternativa — ETL PySpark imperativo
# MAGIC
# MAGIC Este notebook implementa manualmente una parte equivalente del DAG de SDP y
# MAGIC sirve como contingencia. Compare el volumen de coordinación explícita:
# MAGIC lectura, orden, deduplicación, joins, escrituras, nombres, reintentos y control
# MAGIC de dependencias quedan bajo responsabilidad del autor.
# MAGIC
# MAGIC Las tablas terminan en `_fallback`, de modo que nunca colisionan con objetos
# MAGIC administrados por el pipeline.

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catálogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
raw_root = f"/Volumes/{catalog}/{schema}/raw_data"

DATASETS = [
    "network_sites", "radio_cells", "cell_tower_metrics", "network_alarms",
    "maintenance_orders", "products", "customers", "subscriptions",
    "usage_daily", "support_tickets", "customer_surveys",
]

# COMMAND ----------

from pyspark.sql import functions as F

raw = {}
for dataset_name in DATASETS:
    raw[dataset_name] = (
        spark.read.option("header", True).option("inferSchema", True)
        .csv(f"{raw_root}/{dataset_name}")
    )
    raw[dataset_name].write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
        f"{catalog}.{schema}.{dataset_name}_bronze_fallback"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deduplicación y dimensiones
# MAGIC
# MAGIC En SDP, el DAG resuelve estas dependencias. Aquí el orden es manual.

# COMMAND ----------

sites = raw["network_sites"].dropDuplicates(["site_id"])
cells = raw["radio_cells"].dropDuplicates(["cell_id"])
products = raw["products"].dropDuplicates(["product_id"])
customers = (
    raw["customers"].dropDuplicates(["customer_id"])
    .withColumn("tenure_months", F.floor(F.months_between(F.lit("2026-08-14"), "created_date")).cast("int"))
)

subscriptions = (
    raw["subscriptions"].dropDuplicates(["subscription_id"]).alias("sub")
    .join(customers.alias("cus"), "customer_id", "left")
    .join(products.alias("pro"), "product_id", "left")
    .select(
        "sub.*", "cus.customer_type", "cus.customer_segment", "cus.region", "cus.commune",
        "cus.age_band", "cus.digital_engagement_score", "cus.customer_status",
        "pro.product_name", "pro.product_family", "pro.data_allowance_gb",
        "pro.unlimited_data", "pro.is_5g_enabled", "pro.product_status",
    )
)

# COMMAND ----------

metrics = (
    raw["cell_tower_metrics"].dropDuplicates(["measurement_id"]).alias("m")
    .join(cells.alias("c"), F.col("m.cell_id") == F.col("c.cell_id"), "left")
    .join(sites.alias("s"), F.col("c.site_id") == F.col("s.site_id"), "left")
    .select(
        "m.*", F.col("c.site_id").alias("site_id"), "c.technology", "c.frequency_band",
        "c.bandwidth_mhz", "c.capacity_users", "s.region", "s.commune", "s.environment",
        "s.latitude", "s.longitude",
    )
    .withColumn("event_date", F.to_date("event_ts"))
    .withColumn("event_hour", F.date_trunc("hour", "event_ts"))
    .withColumn(
        "network_status",
        F.when((F.col("availability_pct") < 99) | (F.col("latency_ms") > 120) | (F.col("downlink_mbps") < 10), "Crítico")
        .when((F.col("latency_ms") > 80) | (F.col("downlink_mbps") < 25), "Atención")
        .otherwise("Saludable"),
    )
)

alarms = (
    raw["network_alarms"].dropDuplicates(["alarm_id"]).alias("a")
    .join(cells.alias("c"), F.col("a.cell_id") == F.col("c.cell_id"), "left")
    .join(sites.alias("s"), F.col("c.site_id") == F.col("s.site_id"), "left")
    .select("a.*", F.col("c.site_id").alias("site_id"), "c.technology", "s.region", "s.commune")
    .withColumn("opened_date", F.to_date("opened_at"))
)

maintenance = (
    raw["maintenance_orders"].dropDuplicates(["work_order_id"]).alias("o")
    .join(sites.alias("s"), "site_id", "left")
    .select("o.*", "s.region", "s.commune", "s.environment")
    .withColumn("created_date", F.to_date("created_at"))
)

usage = (
    raw["usage_daily"].dropDuplicates(["usage_date", "subscription_id"]).alias("u")
    .join(subscriptions.alias("sub"), "subscription_id", "left")
    .join(cells.alias("c"), F.col("u.primary_cell_id") == F.col("c.cell_id"), "left")
    .join(sites.alias("s"), F.col("c.site_id") == F.col("s.site_id"), "left")
    .select(
        "u.*", "sub.customer_id", "sub.product_id", "sub.line_id", "sub.subscription_status",
        "sub.contract_type", "sub.monthly_fee_clp", "sub.customer_type", "sub.customer_segment",
        "sub.digital_engagement_score", "sub.customer_status",
        F.col("sub.region").alias("customer_region"), F.col("sub.commune").alias("customer_commune"),
        "sub.product_name", "sub.product_family", "sub.data_allowance_gb", "sub.unlimited_data",
        F.col("c.site_id").alias("site_id"), "c.technology", "c.frequency_band",
        F.col("s.region").alias("network_region"), F.col("s.commune").alias("network_commune"),
    )
)

tickets = (
    raw["support_tickets"].dropDuplicates(["ticket_id"]).alias("t")
    .join(subscriptions.alias("sub"), "subscription_id", "left")
    .join(cells.alias("c"), F.col("t.cell_id") == F.col("c.cell_id"), "left")
    .join(sites.alias("s"), F.col("c.site_id") == F.col("s.site_id"), "left")
    .select(
        "t.*", "sub.product_id", "sub.product_name", "sub.product_family",
        "sub.customer_type", "sub.customer_segment", "sub.contract_type",
        F.col("c.site_id").alias("site_id"), "c.technology",
        F.coalesce(F.col("s.region"), F.col("sub.region")).alias("region"),
        F.coalesce(F.col("s.commune"), F.col("sub.commune")).alias("commune"),
    )
    .withColumn("created_date", F.to_date("created_at"))
    .withColumn("sla_met", F.col("resolution_hours").isNotNull() & (F.col("resolution_hours") <= F.col("sla_target_hours")))
)

surveys = (
    raw["customer_surveys"].dropDuplicates(["survey_id"]).alias("e")
    .join(subscriptions.alias("sub"), "subscription_id", "left")
    .select(
        "e.*", "sub.product_id", "sub.product_name", "sub.product_family",
        "sub.customer_type", "sub.customer_segment", "sub.region", "sub.commune",
    )
    .withColumn("nps_class", F.when(F.col("nps_score") >= 9, "Promotor").when(F.col("nps_score") >= 7, "Pasivo").otherwise("Detractor"))
)

# COMMAND ----------

silver_outputs = {
    "network_sites": sites,
    "radio_cells": cells,
    "products": products,
    "customers": customers,
    "subscriptions": subscriptions,
    "cell_tower_metrics": metrics,
    "network_alarms": alarms,
    "maintenance_orders": maintenance,
    "usage_daily": usage,
    "support_tickets": tickets,
    "customer_surveys": surveys,
}

for dataset_name, dataframe in silver_outputs.items():
    dataframe.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
        f"{catalog}.{schema}.{dataset_name}_silver_fallback"
    )

display(
    spark.createDataFrame(
        [(name, dataframe.count()) for name, dataframe in silver_outputs.items()],
        "tabla string, filas long",
    ).orderBy("tabla")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comparación para la recapitulación
# MAGIC
# MAGIC | Capacidad | SDP | PySpark imperativo |
# MAGIC |---|---|---|
# MAGIC | DAG y orden | Derivado de las dependencias | Coordinado por el autor |
# MAGIC | Ingesta incremental | Auto Loader administrado | Checkpoints y estado manuales |
# MAGIC | Calidad | Expectations y métricas del pipeline | Código y tablas auxiliares |
# MAGIC | Reintentos | Por flujo y dataset | Lógica externa o rerun completo |
# MAGIC | Lineage | Automático en Unity Catalog | Depende de cada escritura |
# MAGIC | Observabilidad | Event log y UI del pipeline | Logs y métricas construidos a mano |
# MAGIC | Mantenimiento | Definición declarativa | Orquestación y efectos colaterales explícitos |
