# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Lakeflow Declarative Pipelines
# MAGIC
# MAGIC Este notebook e uma **biblioteca de pipeline**. Adicione-o a um Lakeflow
# MAGIC Declarative Pipeline. Nao o execute como notebook interativo.

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType, TimestampType

catalog = spark.conf.get("telco.catalog", "telco_workshop")
schema = spark.conf.get("telco.schema", "red_calidad")
raw_root = f"/Volumes/{catalog}/{schema}/raw_data"

metrics_schema = StructType(
    [
        StructField("tower_id", StringType()),
        StructField("timestamp", TimestampType()),
        StructField("region", StringType()),
        StructField("commune", StringType()),
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
        StructField("environment", StringType()),
        StructField("frequency_band", StringType()),
        StructField("signal_strength_dbm", DoubleType()),
        StructField("sinr_db", DoubleType()),
        StructField("latency_ms", DoubleType()),
        StructField("throughput_mbps", DoubleType()),
        StructField("packet_loss_pct", DoubleType()),
        StructField("dropped_calls", IntegerType()),
        StructField("active_users", IntegerType()),
        StructField("technology", StringType()),
    ]
)

tickets_schema = StructType(
    [
        StructField("ticket_id", StringType()),
        StructField("tower_id", StringType()),
        StructField("region", StringType()),
        StructField("commune", StringType()),
        StructField("created_at", TimestampType()),
        StructField("category", StringType()),
        StructField("severity", StringType()),
        StructField("status", StringType()),
        StructField("channel", StringType()),
        StructField("customer_segment", StringType()),
        StructField("resolution_hours", DoubleType()),
    ]
)


@dp.table(name="tower_metrics_bronze", comment="Metricas brutas ingeridas do volume com Auto Loader")
def tower_metrics_bronze():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(metrics_schema)
        .load(f"{raw_root}/cell_tower_metrics")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


@dp.table(name="support_tickets_bronze", comment="Tickets brutos ingeridos do volume com Auto Loader")
def support_tickets_bronze():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(tickets_schema)
        .load(f"{raw_root}/support_tickets")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.input_file_name())
    )


# Expectations de observacao: registram as falhas sem remover linhas.
# O DQX do modulo seguinte faz a separacao valido/quarentena.
@dp.table(name="tower_metrics_silver", comment="Metricas tipadas e enriquecidas; anomalias preservadas para DQX")
@dp.expect_all(
    {
        "tower_id_preenchido": "tower_id IS NOT NULL",
        "sinal_faixa_fisica": "signal_strength_dbm BETWEEN -120 AND -40",
        "latencia_faixa_fisica": "latency_ms BETWEEN 0 AND 500",
        "throughput_preenchido": "throughput_mbps IS NOT NULL",
    }
)
def tower_metrics_silver():
    return (
        spark.readStream.table("tower_metrics_bronze")
        .withColumn("event_date", F.to_date("timestamp"))
        .withColumn(
            "network_status",
            F.when(
                (F.col("signal_strength_dbm") < -100)
                | (F.col("latency_ms") > 120)
                | (F.col("throughput_mbps") < 10),
                F.lit("Critico"),
            )
            .when(
                (F.col("signal_strength_dbm") < -90) | (F.col("latency_ms") > 80),
                F.lit("Atencao"),
            )
            .otherwise(F.lit("Saudavel")),
        )
    )


@dp.table(name="support_tickets_silver", comment="Tickets padronizados")
def support_tickets_silver():
    return (
        spark.readStream.table("support_tickets_bronze")
        .withColumn("severity", F.initcap("severity"))
        .withColumn("status", F.initcap("status"))
        .withColumn("created_date", F.to_date("created_at"))
    )


@dp.materialized_view(name="tower_kpis_pipeline", comment="KPIs preliminares do pipeline por regiao e tecnologia")
def tower_kpis_pipeline():
    return (
        spark.read.table("tower_metrics_silver")
        .where(
            F.col("tower_id").isNotNull()
            & F.col("signal_strength_dbm").between(-120, -40)
            & F.col("latency_ms").between(0, 500)
            & F.col("throughput_mbps").isNotNull()
        )
        .groupBy("region", "technology")
        .agg(
            F.countDistinct("tower_id").alias("total_towers"),
            F.round(F.avg("signal_strength_dbm"), 1).alias("avg_signal_dbm"),
            F.round(F.avg("latency_ms"), 1).alias("avg_latency_ms"),
            F.round(F.avg("throughput_mbps"), 1).alias("avg_throughput_mbps"),
            F.sum("dropped_calls").alias("total_dropped_calls"),
        )
    )
