"""Validacoes rapidas, sem acesso a um workspace Databricks."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


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
    metrics_rows, metrics_columns = csv_shape(ROOT / "data/generated/cell_tower_metrics.csv")
    tickets_rows, ticket_columns = csv_shape(ROOT / "data/generated/support_tickets.csv")
    assert metrics_rows == 5_000, metrics_rows
    assert tickets_rows == 500, tickets_rows
    assert {"tower_id", "timestamp", "region", "commune", "technology"} <= set(metrics_columns)
    assert {"ticket_id", "tower_id", "severity", "customer_segment"} <= set(ticket_columns)


def main() -> None:
    validate_python()
    validate_yaml()
    validate_json()
    validate_data()
    print("Validacao local concluida com sucesso.")


if __name__ == "__main__":
    main()

