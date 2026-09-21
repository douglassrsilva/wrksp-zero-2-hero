"""Gerador PySpark deterministico para o workshop.

Plano aprovado: 5.000 metricas de 50 torres e 500 tickets, seed 42.
Os identificadores sao ficticios e nenhuma informacao pessoal e gerada.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


LOCATIONS = [
    # region, comuna, latitude, longitude, ambiente, base de usuarios
    ("Región Metropolitana de Santiago", "Santiago", -33.4489, -70.6693, "Urbano denso", 2_600),
    ("Región Metropolitana de Santiago", "Puente Alto", -33.6117, -70.5758, "Urbano periférico", 2_100),
    ("Valparaíso", "Valparaíso", -33.0472, -71.6127, "Costeiro e montanhoso", 1_250),
    ("Valparaíso", "Viña del Mar", -33.0153, -71.5500, "Costeiro urbano", 1_550),
    ("Biobío", "Concepción", -36.8201, -73.0444, "Urbano", 1_650),
    ("Biobío", "Talcahuano", -36.7249, -73.1168, "Costeiro industrial", 1_050),
    ("La Araucanía", "Temuco", -38.7359, -72.5904, "Urbano", 1_200),
    ("La Araucanía", "Padre Las Casas", -38.7669, -72.5997, "Periurbano e rural", 700),
    ("Antofagasta", "Antofagasta", -23.6509, -70.3975, "Costeiro desertico", 1_350),
    ("Antofagasta", "Calama", -22.4544, -68.9294, "Desértico e mineração", 850),
]


def build_tower_metrics(
    spark: SparkSession,
    rows: int = 5_000,
    towers: int = 50,
    seed: int = 42,
    start_timestamp: str = "2026-08-01 00:00:00",
    inject_quality_issues: bool = True,
) -> DataFrame:
    """Cria medicoes correlacionadas de qualidade de rede.

    Cada torre recebe o mesmo numero de medicoes. Para o workshop, use
    ``rows=5000`` e ``towers=50`` para obter 100 medicoes por torre.
    """
    if rows <= 0 or towers <= 0 or rows % towers:
        raise ValueError("rows deve ser positivo e divisivel por towers")

    measurements_per_tower = rows // towers
    interval_seconds = max(1, (7 * 24 * 60 * 60) // measurements_per_tower)

    df = (
        spark.range(rows)
        .withColumnRenamed("id", "row_id")
        .withColumn("tower_number", (F.floor(F.col("row_id") / measurements_per_tower) + 1).cast("int"))
        .withColumn("measurement_number", F.pmod(F.col("row_id"), F.lit(measurements_per_tower)))
        .withColumn("tower_id", F.format_string("TWR-%03d", F.col("tower_number")))
        .withColumn(
            "timestamp",
            F.expr(
                f"timestamp'{start_timestamp}' + "
                f"measurement_number * INTERVAL {interval_seconds} SECONDS"
            ),
        )
        .withColumn("location_number", (F.floor((F.col("tower_number") - 1) / 5) + 1).cast("int"))
        .withColumn("tower_in_location", F.pmod(F.col("tower_number") - 1, F.lit(5)).cast("int"))
        .withColumn("region", F.element_at(F.array(*[F.lit(x[0]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("commune", F.element_at(F.array(*[F.lit(x[1]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("base_latitude", F.element_at(F.array(*[F.lit(x[2]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("base_longitude", F.element_at(F.array(*[F.lit(x[3]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("environment", F.element_at(F.array(*[F.lit(x[4]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("base_users", F.element_at(F.array(*[F.lit(x[5]) for x in LOCATIONS]), F.col("location_number")))
        .withColumn("latitude", F.round(F.col("base_latitude") + (F.col("tower_in_location") - 2) * F.lit(0.009), 5))
        .withColumn("longitude", F.round(F.col("base_longitude") + (2 - F.col("tower_in_location")) * F.lit(0.011), 5))
        .withColumn(
            "technology",
            F.when(
                F.col("location_number").isin(1, 2, 4, 5, 9) & (F.col("tower_in_location") >= 2),
                "5G",
            )
            .when(F.col("location_number").isin(3, 6, 7) & (F.col("tower_in_location") == 4), "5G")
            .otherwise("4G"),
        )
        .withColumn(
            "frequency_band",
            F.when(F.col("technology") == "5G", "n78-3500")
            .when(F.col("environment").rlike("rural|minera"), "B28-700")
            .when(F.col("environment").rlike("denso|urbano|industrial"), "B7-2600")
            .otherwise("B3-1800"),
        )
        .withColumn("hour", F.hour("timestamp"))
        .withColumn(
            "load_factor",
            F.greatest(
                F.lit(0.15),
                F.lit(0.45) + F.lit(0.35) * F.sin((F.col("hour") - F.lit(7)) * F.lit(3.1415926535 / 12)),
            ),
        )
        .withColumn(
            "active_users",
            F.round(
                F.col("base_users") * (F.lit(0.35) + F.col("load_factor"))
                + F.rand(seed) * F.lit(420)
            ).cast("int"),
        )
        .withColumn(
            "congestion",
            F.least(F.lit(1.0), F.col("active_users") / F.lit(3_200.0)),
        )
        .withColumn(
            "signal_strength_dbm",
            F.round(
                F.lit(-78.0)
                + F.when(F.col("technology") == "5G", F.lit(4.0)).otherwise(F.lit(0.0))
                - F.pmod(F.col("tower_number"), F.lit(7)) * F.lit(1.2)
                - F.when(F.col("environment").rlike("montanhoso|industrial|minera"), F.lit(5.5)).otherwise(F.lit(0.0))
                - F.col("congestion") * F.lit(8.0)
                + F.randn(seed + 1) * F.lit(4.5),
                2,
            ),
        )
        .withColumn(
            "latency_ms",
            F.round(
                F.when(F.col("technology") == "5G", F.lit(17.0)).otherwise(F.lit(34.0))
                + F.col("congestion") * F.lit(95.0)
                + F.greatest(F.lit(0.0), F.lit(-85.0) - F.col("signal_strength_dbm")) * F.lit(2.1)
                + F.abs(F.randn(seed + 2)) * F.lit(8.0),
                2,
            ),
        )
        .withColumn(
            "throughput_mbps",
            F.round(
                F.greatest(
                    F.lit(0.5),
                    F.when(F.col("technology") == "5G", F.lit(145.0)).otherwise(F.lit(78.0))
                    - F.col("congestion") * F.lit(60.0)
                    - F.greatest(F.lit(0.0), F.lit(-82.0) - F.col("signal_strength_dbm")) * F.lit(2.0)
                    + F.randn(seed + 3) * F.lit(7.0),
                ),
                2,
            ),
        )
        .withColumn(
            "dropped_calls",
            F.greatest(
                F.lit(0),
                F.round(
                    F.col("congestion") * F.lit(7.0)
                    + F.greatest(F.lit(0.0), F.lit(-92.0) - F.col("signal_strength_dbm")) * F.lit(0.7)
                    + F.randn(seed + 4) * F.lit(1.7)
                ).cast("int"),
            ),
        )
        .withColumn(
            "sinr_db",
            F.round(
                F.greatest(
                    F.lit(-5.0),
                    F.lit(24.0)
                    - F.col("congestion") * F.lit(13.0)
                    - F.greatest(F.lit(0.0), F.lit(-88.0) - F.col("signal_strength_dbm")) * F.lit(0.65)
                    + F.randn(seed + 5) * F.lit(2.2),
                ),
                2,
            ),
        )
        .withColumn(
            "packet_loss_pct",
            F.round(
                F.greatest(
                    F.lit(0.0),
                    F.col("congestion") * F.lit(2.2)
                    + F.greatest(F.lit(0.0), F.lit(-94.0) - F.col("signal_strength_dbm")) * F.lit(0.18)
                    + F.randn(seed + 6) * F.lit(0.3),
                ),
                2,
            ),
        )
    )

    if inject_quality_issues:
        df = (
            df.withColumn(
                "tower_id",
                F.when(F.pmod("row_id", F.lit(401)) == 0, F.lit(None).cast("string")).otherwise(F.col("tower_id")),
            )
            .withColumn(
                "signal_strength_dbm",
                F.when(F.pmod("row_id", F.lit(173)) == 0, F.lit(-145.0)).otherwise(F.col("signal_strength_dbm")),
            )
            .withColumn(
                "latency_ms",
                F.when(F.pmod("row_id", F.lit(227)) == 0, F.lit(650.0))
                .when(F.pmod("row_id", F.lit(311)) == 0, F.lit(-10.0))
                .otherwise(F.col("latency_ms")),
            )
            .withColumn(
                "throughput_mbps",
                F.when(F.pmod("row_id", F.lit(263)) == 0, F.lit(None).cast("double")).otherwise(F.col("throughput_mbps")),
            )
        )

    return df.select(
        "tower_id",
        "timestamp",
        "region",
        "commune",
        "latitude",
        "longitude",
        "environment",
        "frequency_band",
        "signal_strength_dbm",
        "sinr_db",
        "latency_ms",
        "throughput_mbps",
        "packet_loss_pct",
        "dropped_calls",
        "active_users",
        "technology",
    )


def build_support_tickets(
    spark: SparkSession,
    metrics: DataFrame,
    rows: int = 500,
    seed: int = 42,
) -> DataFrame:
    """Cria tickets correlacionados com as piores medicoes da rede."""
    tower_health = (
        metrics.where(F.col("tower_id").isNotNull())
        .groupBy("tower_id", "region")
        .agg(
            F.avg("latency_ms").alias("avg_latency"),
            F.avg("throughput_mbps").alias("avg_throughput"),
            F.sum("dropped_calls").alias("total_drops"),
            F.first("commune").alias("commune"),
            F.max("timestamp").alias("max_timestamp"),
        )
        .withColumn(
            "risk_score",
            F.coalesce(F.col("avg_latency"), F.lit(0.0))
            + F.coalesce(F.col("total_drops"), F.lit(0.0)) * F.lit(0.8)
            - F.coalesce(F.col("avg_throughput"), F.lit(0.0)) * F.lit(0.15),
        )
        .withColumn("risk_rank", F.percent_rank().over(Window.orderBy("risk_score")))
    )

    ticket_base = (
        tower_health.withColumn("ticket_count", F.round(F.lit(5.0) + F.col("risk_rank") * F.lit(10.0)).cast("int"))
        .withColumn("ticket_slot", F.explode(F.sequence(F.lit(1), F.col("ticket_count"))))
        .withColumn("ticket_number", F.row_number().over(Window.orderBy("tower_id", "ticket_slot")) - 1)
        .withColumn("ticket_id", F.format_string("TKT-%05d", F.col("ticket_number") + 1))
        .withColumn(
            "created_at",
            F.expr("timestamp'2026-08-01 00:00:00' + (ticket_number * 1207) * INTERVAL 1 SECOND"),
        )
        .withColumn(
            "category",
            F.when(F.col("avg_latency") > 115, "Velocidad")
            .when(F.col("total_drops") > 600, "Llamadas")
            .when(F.col("avg_throughput") < 38, "Cobertura")
            .otherwise("Señal"),
        )
        .withColumn(
            "severity",
            F.when((F.col("risk_rank") > 0.82) & (F.pmod("ticket_number", F.lit(4)) == 0), "Critica")
            .when(F.col("risk_rank") > 0.62, "Alta")
            .when(F.col("risk_rank") > 0.30, "Media")
            .otherwise("Baja"),
        )
        .withColumn(
            "status",
            F.when(F.pmod("ticket_number", F.lit(10)) < 6, "Resuelto")
            .when(F.pmod("ticket_number", F.lit(10)) < 8, "En progreso")
            .otherwise("Abierto"),
        )
        .withColumn(
            "resolution_hours",
            F.when(F.col("status") == "Resuelto", F.round(F.lit(2.0) + F.rand(seed + 20) * F.lit(44.0), 2)).otherwise(
                F.lit(None).cast("double")
            ),
        )
        .withColumn(
            "channel",
            F.element_at(
                F.array(F.lit("App"), F.lit("Call center"), F.lit("Web"), F.lit("Tienda")),
                F.pmod(F.col("ticket_number"), F.lit(4)) + 1,
            ),
        )
        .withColumn(
            "customer_segment",
            F.element_at(
                F.array(F.lit("Prepago"), F.lit("Postpago"), F.lit("Postpago"), F.lit("Empresas")),
                F.pmod(F.col("ticket_number") + F.lit(seed), F.lit(4)) + 1,
            ),
        )
    )

    return ticket_base.select(
        "ticket_id",
        "tower_id",
        "region",
        "commune",
        "created_at",
        "category",
        "severity",
        "status",
        "channel",
        "customer_segment",
        "resolution_hours",
    )
