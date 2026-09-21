"""Gera os CSVs versionados usando exatamente o gerador PySpark do workshop."""

from __future__ import annotations

import shutil
from pathlib import Path

from pyspark.sql import SparkSession

from telco_workshop.generator import build_support_tickets, build_tower_metrics


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "generated"
STAGING = ROOT / ".data_staging"


def copy_single_csv(source_dir: Path, destination: Path) -> None:
    parts = list(source_dir.glob("part-*.csv"))
    if len(parts) != 1:
        raise RuntimeError(f"Esperado um part CSV em {source_dir}; encontrados {len(parts)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(parts[0], destination)


def main() -> None:
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("telco-workshop-data")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        metrics = build_tower_metrics(spark, seed=42)
        tickets = build_support_tickets(spark, metrics, seed=42)
        assert metrics.count() == 5_000
        assert tickets.count() == 500

        if STAGING.exists():
            shutil.rmtree(STAGING)
        metrics.coalesce(1).write.mode("overwrite").option("header", True).csv(str(STAGING / "metrics"))
        tickets.coalesce(1).write.mode("overwrite").option("header", True).csv(str(STAGING / "tickets"))
        copy_single_csv(STAGING / "metrics", OUTPUT / "cell_tower_metrics.csv")
        copy_single_csv(STAGING / "tickets", OUTPUT / "support_tickets.csv")
        print(f"Gerados {metrics.count()} registros de metricas e {tickets.count()} tickets em {OUTPUT}")
    finally:
        spark.stop()
        if STAGING.exists():
            shutil.rmtree(STAGING)


if __name__ == "__main__":
    main()
