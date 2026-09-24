"""Crea o actualiza un AI/BI Dashboard parametrizado para el workshop.

No almacena host, token, warehouse, catálogo, schema ni usuario. La versión inicial
incluye tres KPI, calidad de red por región, experiencia por producto y sitios
prioritarios. Los participantes la personalizan durante el reto final.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from typing import Any

DEFAULT_TITLE = "Experiencia móvil 360"


def _id(number: int) -> str:
    return f"{number:08x}"


def _dataset(name: str, display_name: str, sql: str) -> dict[str, Any]:
    # Lakeview concatena `queryLines` sin insertar separadores. Una única línea
    # normalizada evita uniones inválidas como `active_customersFROM`.
    normalized_sql = " ".join(line.strip() for line in sql.splitlines() if line.strip())
    return {"name": name, "displayName": display_name, "queryLines": [normalized_sql]}


def _query(dataset: str, *fields: str) -> list[dict[str, Any]]:
    query_name = hashlib.sha256("|".join((dataset, *fields)).encode()).hexdigest()[:8]
    return [
        {
            "name": query_name,
            "query": {
                "datasetName": dataset,
                "fields": [{"name": field, "expression": f"`{field}`"} for field in fields],
                "disaggregated": True,
            },
        }
    ]


def _counter(name: str, dataset: str, field: str, title: str) -> dict[str, Any]:
    return {
        "name": name,
        "queries": _query(dataset, field),
        "spec": {
            "version": 2,
            "widgetType": "counter",
            "encodings": {"value": {"fieldName": field, "displayName": title}},
            "frame": {"showTitle": True, "title": title},
        },
    }


def build_serialized_dashboard(catalog: str, schema: str) -> dict[str, Any]:
    namespace = f"`{catalog}`.`{schema}`"
    datasets = [
        _dataset(
            "kpis",
            "Indicadores ejecutivos",
            f"""SELECT
  ROUND(AVG(avg_availability_pct), 2) AS availability_pct,
  ROUND(AVG(avg_latency_ms), 1) AS latency_ms,
  (SELECT COUNT(DISTINCT customer_id) FROM {namespace}.gold_customer_360) AS active_customers
FROM {namespace}.gold_network_hourly""",
        ),
        _dataset(
            "network_quality",
            "Calidad de red",
            f"""SELECT
  `Región` AS region,
  `Tecnología` AS technology,
  MEASURE(`Disponibilidad media`) AS availability_pct,
  MEASURE(`Latencia media`) AS latency_ms,
  MEASURE(`Downlink medio`) AS downlink_mbps,
  MEASURE(`Cumplimiento SLA de red`) AS network_sla_pct
FROM {namespace}.mv_network_quality
GROUP BY `Región`, `Tecnología`""",
        ),
        _dataset(
            "customer_product",
            "Clientes y productos",
            f"""SELECT
  `Región` AS region,
  `Segmento` AS customer_segment,
  `Producto` AS product_name,
  MEASURE(`Clientes activos`) AS active_customers,
  MEASURE(`ARPU`) AS arpu_clp,
  MEASURE(`NPS`) AS nps,
  MEASURE(`Tickets por 100 líneas`) AS tickets_per_100_lines,
  MEASURE(`Cumplimiento SLA de cliente`) AS customer_network_sla_pct
FROM {namespace}.mv_customer_product_experience
GROUP BY `Región`, `Segmento`, `Producto`""",
        ),
        _dataset(
            "priority_sites",
            "Sitios prioritarios",
            f"""SELECT
  event_date, site_id, region, commune, site_health_status,
  avg_availability_pct, avg_latency_ms, avg_downlink_mbps,
  open_tickets, impacted_subscriptions
FROM {namespace}.gold_site_daily_360
ORDER BY avg_latency_ms DESC, open_tickets DESC
LIMIT 100""",
        ),
    ]

    widgets = [
        {
            "widget": _counter(_id(101), "kpis", "availability_pct", "Disponibilidad media"),
            "position": {"x": 0, "y": 0, "width": 2, "height": 2},
        },
        {
            "widget": _counter(_id(102), "kpis", "latency_ms", "Latencia media (ms)"),
            "position": {"x": 2, "y": 0, "width": 2, "height": 2},
        },
        {
            "widget": _counter(_id(103), "kpis", "active_customers", "Clientes activos"),
            "position": {"x": 4, "y": 0, "width": 2, "height": 2},
        },
        {
            "widget": {
                "name": _id(104),
                "queries": _query("network_quality", "region", "technology", "network_sla_pct"),
                "spec": {
                    "version": 3,
                    "widgetType": "bar",
                    "encodings": {
                        "x": {"fieldName": "region", "scale": {"type": "categorical"}, "displayName": "Región"},
                        "y": {"fieldName": "network_sla_pct", "scale": {"type": "quantitative"}, "displayName": "SLA (%)"},
                        "color": {"fieldName": "technology", "scale": {"type": "categorical"}, "displayName": "Tecnología"},
                    },
                    "frame": {"showTitle": True, "title": "SLA de red por región y tecnología"},
                    "mark": {"colors": ["#00A972", "#8BCAE7"]},
                },
            },
            "position": {"x": 0, "y": 2, "width": 3, "height": 5},
        },
        {
            "widget": {
                "name": _id(105),
                "queries": _query("customer_product", "product_name", "customer_segment", "arpu_clp", "nps"),
                "spec": {
                    "version": 3,
                    "widgetType": "scatter",
                    "encodings": {
                        "x": {"fieldName": "arpu_clp", "scale": {"type": "quantitative"}, "displayName": "ARPU (CLP)"},
                        "y": {"fieldName": "nps", "scale": {"type": "quantitative"}, "displayName": "NPS"},
                        "color": {"fieldName": "customer_segment", "scale": {"type": "categorical"}, "displayName": "Segmento"},
                    },
                    "frame": {"showTitle": True, "title": "ARPU frente a NPS por producto"},
                },
            },
            "position": {"x": 3, "y": 2, "width": 3, "height": 5},
        },
        {
            "widget": {
                "name": _id(106),
                "queries": _query(
                    "priority_sites",
                    "site_id",
                    "region",
                    "commune",
                    "site_health_status",
                    "avg_latency_ms",
                    "avg_downlink_mbps",
                    "open_tickets",
                    "impacted_subscriptions",
                ),
                "spec": {
                    "version": 1,
                    "widgetType": "table",
                    "encodings": {
                        "columns": [
                            {"fieldName": name, "type": "string" if name in {"site_id", "region", "commune", "site_health_status"} else "float", "displayAs": "string" if name in {"site_id", "region", "commune", "site_health_status"} else "number", "title": name}
                            for name in (
                                "site_id", "region", "commune", "site_health_status",
                                "avg_latency_ms", "avg_downlink_mbps", "open_tickets", "impacted_subscriptions",
                            )
                        ]
                    },
                    "frame": {"showTitle": True, "title": "Sitios que requieren atención"},
                },
            },
            "position": {"x": 0, "y": 7, "width": 6, "height": 5},
        },
    ]

    return {
        "datasets": datasets,
        "pages": [
            {
                "name": _id(1),
                "displayName": "Resumen 360",
                "pageType": "PAGE_TYPE_CANVAS",
                "layout": widgets,
            }
        ],
        "uiSettings": {
            "theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"},
            "applyModeEnabled": False,
        },
    }


def _run_cli(cli: str, profile: str, method: str, path: str, payload: dict | None = None) -> dict:
    command = [cli, "api", method, path, "--profile", profile]
    if payload is not None:
        command.extend(["--json", json.dumps(payload, ensure_ascii=False)])
    environment = os.environ.copy()
    environment.setdefault("DATABRICKS_AUTH_STORAGE", "plaintext")
    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout) if completed.stdout.strip() else {}


def _payload(args: argparse.Namespace, parent_path: str) -> dict[str, Any]:
    serialized = build_serialized_dashboard(args.catalog, args.schema)
    return {
        "display_name": args.title,
        "warehouse_id": args.warehouse_id,
        "parent_path": parent_path,
        "serialized_dashboard": json.dumps(serialized, ensure_ascii=False, separators=(",", ":")),
    }


def create_dashboard(args: argparse.Namespace) -> dict[str, Any]:
    if args.cli:
        current_user = _run_cli(args.cli, args.profile, "get", "/api/2.0/preview/scim/v2/Me")["userName"]
        parent_path = args.parent_path or f"/Users/{current_user}"
        existing = _run_cli(args.cli, args.profile, "get", "/api/2.0/lakeview/dashboards")
        match = next((item for item in existing.get("dashboards", []) if item.get("display_name") == args.title), None)
        if match:
            dashboard_id = match["dashboard_id"]
            response = _run_cli(
                args.cli,
                args.profile,
                "patch",
                f"/api/2.0/lakeview/dashboards/{dashboard_id}",
                _payload(args, parent_path),
            )
        else:
            response = _run_cli(
                args.cli,
                args.profile,
                "post",
                "/api/2.0/lakeview/dashboards",
                _payload(args, parent_path),
            )
            dashboard_id = response["dashboard_id"]
        if args.publish:
            _run_cli(
                args.cli,
                args.profile,
                "post",
                f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
                {"embed_credentials": True, "warehouse_id": args.warehouse_id},
            )
        print(f"AI/BI Dashboard listo: {dashboard_id}")
        return response

    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(profile=args.profile)
    current_user = client.current_user.me().user_name
    parent_path = args.parent_path or f"/Users/{current_user}"
    existing = client.api_client.do("GET", "/api/2.0/lakeview/dashboards")
    match = next((item for item in existing.get("dashboards", []) if item.get("display_name") == args.title), None)
    if match:
        dashboard_id = match["dashboard_id"]
        response = client.api_client.do(
            "PATCH", f"/api/2.0/lakeview/dashboards/{dashboard_id}", body=_payload(args, parent_path)
        )
    else:
        response = client.api_client.do("POST", "/api/2.0/lakeview/dashboards", body=_payload(args, parent_path))
        dashboard_id = response["dashboard_id"]
    if args.publish:
        client.api_client.do(
            "POST",
            f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
            body={"embed_credentials": True, "warehouse_id": args.warehouse_id},
        )
    print(f"AI/BI Dashboard listo: {dashboard_id}")
    return response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea el AI/BI Dashboard inicial del workshop")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--parent-path")
    parser.add_argument("--cli", help="Ruta opcional a Databricks CLI")
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    create_dashboard(parse_args())
