"""Crea de forma parametrizada el Genie Agent del workshop.

No almacena host, warehouse, usuario, token, catálogo ni schema. La autenticación
usa un perfil Databricks CLI y OAuth U2M/M2M administrado por el SDK.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Any

from databricks.sdk import WorkspaceClient


TITLE = "Analista 360 de Red y Clientes"


def _id(number: int) -> str:
    """ID hexadecimal de 32 caracteres; el orden numérico conserva el orden requerido."""
    return f"{number:032x}"


def _qualified(catalog: str, schema: str, object_name: str) -> str:
    return f"{catalog}.{schema}.{object_name}"


def _metric_sql(namespace: str, metric_view: str, select_clause: str, suffix: str) -> list[str]:
    return [f"SELECT {select_clause}\nFROM {namespace}.{metric_view}\n{suffix}"]


def build_serialized_space(catalog: str, schema: str) -> dict[str, Any]:
    namespace = f"{catalog}.{schema}"
    network_metric = _qualified(catalog, schema, "mv_network_quality")
    customer_metric = _qualified(catalog, schema, "mv_customer_product_experience")

    sample_questions = [
        {
            "id": _id(1),
            "question": [
                "Compara disponibilidad, latencia, throughput y SLA por región y tecnología. "
                "Muestra las tres combinaciones con peor desempeño."
            ],
        },
        {
            "id": _id(2),
            "question": [
                "¿Qué cinco productos tienen mayor ARPU y cómo se comparan en consumo, "
                "tickets por 100 líneas, NPS y SLA de red?"
            ],
        },
    ]

    instructions = (
        "Responde siempre en español. Analiza un operador móvil chileno ficticio. "
        "Usa las Metric Views para KPIs certificados y las Gold solo para detalle. "
        "En SQL sobre Metric Views usa MEASURE(). Interpreta importes como CLP. "
        "En mv_customer_product_experience, 'SLA del cliente' o 'SLA de red por producto' "
        "corresponde a MEASURE(`Cumplimiento SLA de cliente`). Para el SLA global de red usa "
        "MEASURE(`Cumplimiento SLA de red`) en mv_network_quality. "
        "El período sintético es agosto de 2026; no uses la fecha actual para 'últimos días'. "
        "Muestra filtros, período, dimensiones y medidas. Diferencia correlación de causalidad "
        "y declara supuestos y limitaciones. Los IDs CLI-*, LIN-* y SUB-* son ficticios. "
        "No infieras PII ni menciones empresas reales."
    )

    examples = [
        {
            "id": _id(10),
            "question": ["Compara calidad de red por región y tecnología"],
            "sql": _metric_sql(
                namespace,
                "mv_network_quality",
                "`Región`, `Tecnología`, "
                "MEASURE(`Disponibilidad media`) AS disponibilidad_pct, "
                "MEASURE(`Latencia media`) AS latencia_ms, "
                "MEASURE(`Downlink medio`) AS downlink_mbps, "
                "MEASURE(`Cumplimiento SLA de red`) AS sla_pct",
                "GROUP BY `Región`, `Tecnología` ORDER BY sla_pct",
            ),
        },
        {
            "id": _id(11),
            "question": ["Muestra los cinco productos con mayor ARPU y su NPS"],
            "sql": _metric_sql(
                namespace,
                "mv_customer_product_experience",
                "`Producto`, MEASURE(`ARPU`) AS arpu_clp, "
                "MEASURE(`Consumo de datos`) AS consumo_gb, "
                "MEASURE(`NPS`) AS nps, MEASURE(`Tickets por 100 líneas`) AS tickets_100, "
                "MEASURE(`Cumplimiento SLA de cliente`) AS sla_cliente_pct",
                "GROUP BY `Producto` ORDER BY arpu_clp DESC LIMIT 5",
            ),
        },
        {
            "id": _id(12),
            "question": ["¿Cuántos clientes de alto riesgo existen por región y segmento?"],
            "sql": [
                f"SELECT region, customer_segment, COUNT(DISTINCT customer_id) AS clientes_alto_riesgo\n"
                f"FROM {namespace}.gold_customer_360\n"
                "WHERE churn_risk_band = 'Alto'\n"
                "GROUP BY region, customer_segment\n"
                "ORDER BY clientes_alto_riesgo DESC"
            ],
        },
        {
            "id": _id(13),
            "question": ["Muestra los incidentes con mayor impacto de negocio"],
            "sql": [
                f"SELECT alarm_id, region, commune, severity, impacted_customers, "
                "impacted_subscriptions, billed_revenue_at_risk_clp, business_impact\n"
                f"FROM {namespace}.gold_incident_impact\n"
                "ORDER BY impacted_customers DESC, affected_users_est DESC\n"
                "LIMIT 20"
            ],
        },
        {
            "id": _id(14),
            "question": ["¿Qué sitios combinan SLA bajo y tickets abiertos?"],
            "sql": [
                f"SELECT event_date, site_id, region, commune, network_sla_compliance_pct, "
                "open_tickets, site_health_status\n"
                f"FROM {namespace}.gold_site_daily_360\n"
                "WHERE network_sla_compliance_pct < 95 AND open_tickets > 0\n"
                "ORDER BY network_sla_compliance_pct, open_tickets DESC"
            ],
        },
    ]

    benchmark_questions = [
        {
            "id": _id(20 + index),
            "question": example["question"],
            "answer": [{"format": "SQL", "content": example["sql"]}],
        }
        for index, example in enumerate(examples)
    ]

    table_identifiers = sorted(
        _qualified(catalog, schema, name)
        for name in ("gold_customer_360", "gold_incident_impact", "gold_site_daily_360")
    )
    metric_identifiers = sorted([customer_metric, network_metric])

    return {
        "version": 2,
        "config": {"sample_questions": sample_questions},
        "data_sources": {
            "tables": [
                {"identifier": identifier, "description": ["Tabla Gold sintética y gobernada del workshop"]}
                for identifier in table_identifiers
            ],
            "metric_views": [
                {"identifier": identifier, "description": ["Metric View certificada del workshop"]}
                for identifier in metric_identifiers
            ],
        },
        "instructions": {
            "text_instructions": [{"id": _id(5), "content": [instructions]}],
            "example_question_sqls": examples,
        },
        "benchmarks": {"questions": benchmark_questions},
    }


def create_agent(args: argparse.Namespace) -> dict[str, Any]:
    if args.cli:
        return create_agent_with_cli(args)

    client = WorkspaceClient(profile=args.profile)
    current_user = client.current_user.me().user_name
    parent_path = args.parent_path or f"/Workspace/Users/{current_user}"

    existing = client.api_client.do("GET", "/api/2.0/genie/spaces")
    for space in existing.get("spaces", []):
        if space.get("title") == args.title:
            print(f"El Genie Agent ya existe: {space.get('space_id')}")
            return space

    serialized = build_serialized_space(args.catalog, args.schema)
    payload = {
        "title": args.title,
        "description": "Análisis sintético y gobernado de red, clientes, productos y experiencia",
        "parent_path": parent_path,
        "warehouse_id": args.warehouse_id,
        "serialized_space": json.dumps(serialized, ensure_ascii=False, separators=(",", ":")),
    }
    response = client.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)
    print(f"Genie Agent creado: {response.get('space_id')}")
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


def create_agent_with_cli(args: argparse.Namespace) -> dict[str, Any]:
    current_user = _run_cli(args.cli, args.profile, "get", "/api/2.0/preview/scim/v2/Me")["userName"]
    parent_path = args.parent_path or f"/Workspace/Users/{current_user}"
    existing = _run_cli(args.cli, args.profile, "get", "/api/2.0/genie/spaces")
    for space in existing.get("spaces", []):
        if space.get("title") == args.title:
            print(f"El Genie Agent ya existe: {space.get('space_id')}")
            return space

    serialized = build_serialized_space(args.catalog, args.schema)
    payload = {
        "title": args.title,
        "description": "Análisis sintético y gobernado de red, clientes, productos y experiencia",
        "parent_path": parent_path,
        "warehouse_id": args.warehouse_id,
        "serialized_space": json.dumps(serialized, ensure_ascii=False, separators=(",", ":")),
    }
    response = _run_cli(args.cli, args.profile, "post", "/api/2.0/genie/spaces", payload)
    print(f"Genie Agent creado: {response.get('space_id')}")
    return response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea el Genie Agent del workshop")
    parser.add_argument("--profile", required=True, help="Perfil Databricks CLI autenticado")
    parser.add_argument("--catalog", required=True, help="Catálogo de Unity Catalog")
    parser.add_argument("--schema", required=True, help="Schema del workshop")
    parser.add_argument("--warehouse-id", required=True, help="ID de SQL Warehouse Pro o Serverless")
    parser.add_argument("--cli", help="Ruta opcional a Databricks CLI; evita cargar ~/.databrickscfg con el SDK")
    parser.add_argument("--title", default=TITLE)
    parser.add_argument("--parent-path", help="Ruta de workspace; por defecto usa el usuario autenticado")
    return parser.parse_args()


if __name__ == "__main__":
    create_agent(parse_args())
