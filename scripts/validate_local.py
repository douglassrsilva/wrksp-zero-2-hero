"""Preflight del repositorio para instructores/CI, sin validar servicios remotos."""

from __future__ import annotations

import ast
import csv
import importlib.util
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DATASETS = {
    "network_sites": (60, {"site_id", "region", "commune", "latitude", "longitude"}),
    "radio_cells": (180, {"cell_id", "site_id", "technology", "frequency_band"}),
    "cell_tower_metrics": (
        30_240,
        {"measurement_id", "cell_id", "event_ts", "availability_pct", "latency_ms", "downlink_mbps"},
    ),
    "network_alarms": (1_200, {"alarm_id", "cell_id", "opened_at", "severity", "service_impact"}),
    "maintenance_orders": (400, {"work_order_id", "site_id", "alarm_id", "cost_clp"}),
    "products": (18, {"product_id", "product_name", "product_family", "monthly_price_clp"}),
    "customers": (3_000, {"customer_id", "customer_segment", "region", "analytics_consent"}),
    "subscriptions": (4_200, {"subscription_id", "customer_id", "product_id", "line_id"}),
    "usage_daily": (58_800, {"usage_date", "subscription_id", "primary_cell_id", "data_gb"}),
    "support_tickets": (1_500, {"ticket_id", "customer_id", "subscription_id", "category"}),
    "customer_surveys": (800, {"survey_id", "subscription_id", "nps_score", "csat_score"}),
}

FORBIDDEN_PII_COLUMNS = {
    "name",
    "full_name",
    "first_name",
    "last_name",
    "rut",
    "email",
    "phone",
    "telephone",
    "address",
    "imsi",
    "imei",
}


def validate_python() -> None:
    for path in ROOT.rglob("*.py"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_yaml() -> None:
    for path in ROOT.rglob("*.yml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in ROOT.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_json() -> None:
    for path in ROOT.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def csv_shape(path: Path) -> tuple[int, list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        return sum(1 for _ in reader), header


def validate_data() -> None:
    data_dir = ROOT / "data" / "generated"
    actual_files = {path.stem for path in data_dir.glob("*.csv")}
    assert actual_files == set(EXPECTED_DATASETS), (actual_files, set(EXPECTED_DATASETS))

    total_rows = 0
    for dataset_name, (expected_rows, required_columns) in EXPECTED_DATASETS.items():
        rows, columns = csv_shape(data_dir / f"{dataset_name}.csv")
        normalized_columns = {column.lower() for column in columns}
        assert rows == expected_rows, f"{dataset_name}: {rows} != {expected_rows}"
        assert required_columns <= set(columns), f"{dataset_name}: faltan {required_columns - set(columns)}"
        assert not (normalized_columns & FORBIDDEN_PII_COLUMNS), (
            dataset_name,
            normalized_columns & FORBIDDEN_PII_COLUMNS,
        )
        total_rows += rows

    assert total_rows == 100_398, total_rows


def _read_dicts(dataset_name: str) -> list[dict[str, str]]:
    path = ROOT / "data" / "generated" / f"{dataset_name}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_impurities() -> None:
    """Comprueba que DQX tenga anomalías deliberadas, no solo datos perfectos."""

    metrics = _read_dicts("cell_tower_metrics")
    surveys = _read_dicts("customer_surveys")
    subscriptions = _read_dicts("subscriptions")
    tickets = _read_dicts("support_tickets")

    assert any(not row["cell_id"] for row in metrics)
    assert any(row["downlink_mbps"] == "" for row in metrics)
    assert any(float(row["latency_ms"]) < 0 or float(row["latency_ms"]) > 500 for row in metrics)
    assert len({row["measurement_id"] for row in metrics}) < len(metrics)
    assert any(int(row["nps_score"]) > 10 for row in surveys)
    assert any(row["product_id"] == "PRD-999" for row in subscriptions)
    assert any(not row["category"] for row in tickets)


def validate_demo_isolation() -> None:
    """Impide que la muestra PySpark se convierta en una ruta downstream."""

    demo_path = ROOT / "notebooks" / "03_alt_spark_etl.py"
    demo_source = demo_path.read_text(encoding="utf-8")
    expected_tables = {
        "demo_spark_network_sample",
        "demo_spark_customer_product_sample",
        "demo_spark_kpis",
    }

    assert "_fallback" not in demo_source
    assert demo_source.count(".saveAsTable(") == 3
    assert all(table_name in demo_source for table_name in expected_tables)

    downstream_paths = [
        ROOT / "notebooks" / "04_dqx_quality.py",
        ROOT / "notebooks" / "04_alt_sql_quality.sql",
        ROOT / "notebooks" / "05_checkpoint_if_needed.sql",
        ROOT / "notebooks" / "05_sql_queries.sql",
        ROOT / "notebooks" / "06_metric_views.sql",
        ROOT / "config" / "genie_space_instructions.md",
        ROOT / "apps" / "network-monitor" / "data_access.py",
    ]
    for path in downstream_paths:
        source = path.read_text(encoding="utf-8")
        assert not any(table_name in source for table_name in expected_tables), path


def validate_dashboard_queries() -> None:
    """Evita que Lakeview una fragmentos SQL sin espacios entre palabras clave."""

    path = ROOT / "scripts" / "create_dashboard.py"
    spec = importlib.util.spec_from_file_location("workshop_dashboard_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    dashboard = module.build_serialized_dashboard("catalog_demo", "schema_demo")
    assert len(dashboard["datasets"]) == 4
    forbidden_fragments = {
        "customersFROM",
        "pctFROM",
        "experienceGROUP",
        "subscriptionsFROM",
        "360ORDER",
        "DESCLIMIT",
    }
    for dataset in dashboard["datasets"]:
        assert len(dataset["queryLines"]) == 1, dataset["name"]
        statement = dataset["queryLines"][0]
        assert not any(fragment in statement for fragment in forbidden_fragments), dataset["name"]


def main() -> None:
    validate_python()
    validate_yaml()
    validate_json()
    validate_data()
    validate_impurities()
    validate_demo_isolation()
    validate_dashboard_queries()
    print("Preflight local del repositorio finalizado correctamente.")


if __name__ == "__main__":
    main()
