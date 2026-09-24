"""Genera los once CSV versionados con el mismo PySpark del workshop."""

from __future__ import annotations

import shutil
from pathlib import Path

from pyspark.sql import SparkSession

from telco_workshop.generator import DATASET_COUNTS, build_all_datasets

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "generated"
STAGING = ROOT / ".data_staging"


def copy_single_csv(source_dir: Path, destination: Path) -> None:
    parts = list(source_dir.glob("part-*.csv"))
    if len(parts) != 1:
        raise RuntimeError(f"Se esperaba un archivo part CSV en {source_dir}; se encontraron {len(parts)}")
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
        datasets = build_all_datasets(spark, seed=42)

        if STAGING.exists():
            shutil.rmtree(STAGING)
        counts = {}
        for dataset_name, dataframe in datasets.items():
            count = dataframe.count()
            expected = DATASET_COUNTS[dataset_name]
            assert count == expected, f"{dataset_name}: se esperaban {expected}; se obtuvieron {count}"
            counts[dataset_name] = count
            staging_path = STAGING / dataset_name
            (
                dataframe.coalesce(1)
                .write.mode("overwrite")
                .option("header", True)
                .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
                .option("dateFormat", "yyyy-MM-dd")
                .csv(str(staging_path))
            )
            copy_single_csv(staging_path, OUTPUT / f"{dataset_name}.csv")

        print(f"Se generaron {sum(counts.values()):,} filas en {OUTPUT}")
        for dataset_name, count in counts.items():
            print(f"  - {dataset_name}: {count:,}")
    finally:
        spark.stop()
        if STAGING.exists():
            shutil.rmtree(STAGING)


if __name__ == "__main__":
    main()
