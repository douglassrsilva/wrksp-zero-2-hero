# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Preparación y generación de datos sintéticos
# MAGIC
# MAGIC Genera once fuentes sintéticas con PySpark nativo: red, operaciones, clientes,
# MAGIC productos, consumo y experiencia. El notebook crea un volumen de Unity Catalog,
# MAGIC escribe los CSV para Lakeflow y mantiene checkpoints Delta de contingencia.
# MAGIC Ninguna fuente contiene PII. Ejecútelo una vez antes del workshop.

# COMMAND ----------

dbutils.widgets.text("catalog", "telco_workshop", "Catálogo")
dbutils.widgets.text("schema", "red_calidad", "Schema")
dbutils.widgets.text("seed", "42", "Seed")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
seed = int(dbutils.widgets.get("seed"))

assert catalog.replace("_", "").isalnum(), "Nombre de catálogo no válido"
assert schema.replace("_", "").isalnum(), "Nombre de schema no válido"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unity Catalog
# MAGIC El catálogo debe existir antes del workshop. El notebook crea solamente el
# MAGIC schema y el volumen, si el participante tiene permisos. Esto evita que
# MAGIC `CREATE CATALOG IF NOT EXISTS` falle en metastores sin storage root.

# COMMAND ----------

spark.sql(f"DESCRIBE CATALOG EXTENDED `{catalog}`").limit(1).collect()
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`raw_data`")

volume_root = f"/Volumes/{catalog}/{schema}/raw_data"
print(f"Volumen de entrada: {volume_root}")

# COMMAND ----------

import sys
from pathlib import Path

for candidate in (Path.cwd() / "src", Path.cwd().parent / "src"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))
        break

from telco_workshop.generator import DATASET_COUNTS, build_all_datasets

datasets = build_all_datasets(spark, seed=seed)
for dataset_name, dataframe in datasets.items():
    actual = dataframe.count()
    expected = DATASET_COUNTS[dataset_name]
    assert actual == expected, f"{dataset_name}: se esperaban {expected}; se obtuvieron {actual}"

display(datasets["cell_tower_metrics"].limit(10))
display(datasets["customers"].limit(10))
display(datasets["products"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Zona de aterrizaje en CSV
# MAGIC Auto Loader lee los siguientes directorios en el pipeline de Lakeflow.

# COMMAND ----------

for dataset_name, dataframe in datasets.items():
    (
        dataframe.coalesce(1)
        .write.mode("overwrite")
        .option("header", True)
        .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
        .option("dateFormat", "yyyy-MM-dd")
        .csv(f"{volume_root}/{dataset_name}")
    )
    print(f"CSV listo: {volume_root}/{dataset_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Punto de contingencia
# MAGIC Estas tablas permiten continuar el workshop aunque Lakeflow no esté disponible.

# COMMAND ----------

for dataset_name, dataframe in datasets.items():
    dataframe.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{catalog}.{schema}.{dataset_name}_raw_checkpoint"
    )

summary_rows = [(name, DATASET_COUNTS[name]) for name in DATASET_COUNTS]
summary = spark.createDataFrame(summary_rows, "dataset string, filas long").orderBy("dataset")
display(summary)
