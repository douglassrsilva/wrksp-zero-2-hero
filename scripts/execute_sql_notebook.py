"""Ejecuta un notebook Databricks SQL, celda por celda, en un SQL Warehouse.

El script no guarda host, token, warehouse, catálogo ni schema. Lee los valores
`CREATE WIDGET ... DEFAULT` del notebook y permite sobrescribirlos con `--set`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient

CELL_SEPARATOR = "-- COMMAND ----------"
WIDGET_PATTERN = re.compile(
    r'CREATE\s+WIDGET\s+TEXT\s+(\w+)\s+DEFAULT\s+"([^"]*)"\s*;',
    flags=re.IGNORECASE,
)
IDENTIFIER_PATTERN = re.compile(r"IDENTIFIER\(\s*:(\w+)\s*\)", flags=re.IGNORECASE)


def _quoted_identifier(value: str) -> str:
    if not value or any(character in value for character in ("`", "\n", "\r", "\x00")):
        raise ValueError(f"Identificador no válido: {value!r}")
    return f"`{value}`"


def parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Use --set nombre=valor; se recibió {item!r}")
        name, value = item.split("=", 1)
        overrides[name.strip()] = value.strip()
    return overrides


def split_sql_statements(source: str) -> list[str]:
    """Separa sentencias por `;` sin romper literales, identificadores ni bloques `$$`."""

    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    dollar_quoted = False
    index = 0
    while index < len(source):
        pair = source[index : index + 2]
        character = source[index]

        if quote is None and pair == "$$":
            dollar_quoted = not dollar_quoted
            current.append(pair)
            index += 2
            continue

        if not dollar_quoted:
            if quote is None and character in {"'", '"', "`"}:
                quote = character
            elif quote == character:
                if index + 1 < len(source) and source[index + 1] == character:
                    current.extend((character, character))
                    index += 2
                    continue
                quote = None

        if character == ";" and quote is None and not dollar_quoted:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(character)
        index += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements


def prepare_cells(path: Path, overrides: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    widgets = {name: default for name, default in WIDGET_PATTERN.findall(source)}
    widgets.update(overrides)

    cells: list[str] = []
    for raw_cell in source.split(CELL_SEPARATOR):
        lines = [
            line
            for line in raw_cell.splitlines()
            if not line.startswith("-- Databricks notebook source") and not line.startswith("-- MAGIC")
        ]
        cell = "\n".join(lines).strip()
        if not cell:
            continue

        def replace_identifier(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in widgets:
                raise KeyError(f"El widget :{name} no tiene valor")
            return _quoted_identifier(widgets[name])

        cell = IDENTIFIER_PATTERN.sub(replace_identifier, cell)
        for statement in split_sql_statements(cell):
            if re.match(r"^CREATE\s+WIDGET\b", statement, flags=re.IGNORECASE):
                continue
            if re.match(r"^(USE\s+CATALOG|USE\s+SCHEMA)\b", statement, flags=re.IGNORECASE):
                continue
            cells.append(statement)
    return cells, widgets


def wait_for_statement(client: WorkspaceClient, statement_id: str):
    while True:
        response = client.statement_execution.get_statement(statement_id)
        state = response.status.state.value
        if state not in {"PENDING", "RUNNING"}:
            return response
        time.sleep(2)


def execute_cell(
    client: WorkspaceClient,
    statement: str,
    warehouse_id: str,
    catalog: str,
    schema: str,
):
    response = client.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=warehouse_id,
        catalog=catalog,
        schema=schema,
        wait_timeout="50s",
        row_limit=100,
    )
    state = response.status.state.value
    if state in {"PENDING", "RUNNING"}:
        response = wait_for_statement(client, response.statement_id)
        state = response.status.state.value
    if state != "SUCCEEDED":
        message = response.status.error.message if response.status.error else state
        raise RuntimeError(message)
    return response


def _run_cli(cli: str, profile: str, method: str, path: str, payload: dict | None = None) -> dict:
    command = [cli, "api", method, path, "--profile", profile]
    if payload is not None:
        command.extend(["--json", json.dumps(payload, ensure_ascii=False)])
    environment = os.environ.copy()
    environment.setdefault("DATABRICKS_AUTH_STORAGE", "plaintext")
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def execute_cell_cli(
    cli: str,
    profile: str,
    statement: str,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> dict:
    response = _run_cli(
        cli,
        profile,
        "post",
        "/api/2.0/sql/statements",
        {
            "statement": statement,
            "warehouse_id": warehouse_id,
            "catalog": catalog,
            "schema": schema,
            "format": "JSON_ARRAY",
            "wait_timeout": "50s",
            "row_limit": 100,
        },
    )
    while response.get("status", {}).get("state") in {"PENDING", "RUNNING"}:
        time.sleep(2)
        response = _run_cli(
            cli,
            profile,
            "get",
            f"/api/2.0/sql/statements/{response['statement_id']}",
        )
    state = response.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        error = response.get("status", {}).get("error", {})
        raise RuntimeError(error.get("message", state))
    return response


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta un notebook SQL en un Warehouse")
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--cli", help="Ruta opcional a Databricks CLI; evita cargar ~/.databrickscfg con el SDK")
    parser.add_argument("--set", action="append", default=[], metavar="NOMBRE=VALOR")
    args = parser.parse_args()

    cells, widgets = prepare_cells(args.notebook, parse_overrides(args.set))
    client = None if args.cli else WorkspaceClient(profile=args.profile)
    for index, statement in enumerate(cells, start=1):
        headline = next((line.strip() for line in statement.splitlines() if line.strip()), "SQL")
        print(f"[{index:02d}/{len(cells):02d}] {headline[:100]}")
        if args.cli:
            execute_cell_cli(
                args.cli,
                args.profile,
                statement,
                args.warehouse_id,
                args.catalog,
                args.schema,
            )
        else:
            execute_cell(client, statement, args.warehouse_id, args.catalog, args.schema)

    print(
        f"Notebook SQL finalizado: {args.notebook.name}; "
        f"catálogo={args.catalog}; schema={args.schema}; widgets={sorted(widgets)}"
    )


if __name__ == "__main__":
    main()
