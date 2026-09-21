"""Databricks App: monitor anonimo de qualidade de rede movel."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Monitor de qualidade de rede", page_icon="📡", layout="wide")


def _statement_to_dataframe(statement: str) -> pd.DataFrame:
    from databricks.sdk import WorkspaceClient

    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    client = WorkspaceClient()
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="30s",
        row_limit=10_000,
    )
    if response.status and response.status.state and response.status.state.value != "SUCCEEDED":
        raise RuntimeError(f"Falha na consulta: {response.status}")
    columns = [column.name for column in response.manifest.schema.columns]
    rows = response.result.data_array or []
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=120, show_spinner="Consultando indicadores...")
def load_remote_data(catalog: str, schema: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    kpis = _statement_to_dataframe(f"SELECT * FROM `{catalog}`.`{schema}`.`v_network_kpis`")
    towers = _statement_to_dataframe(f"SELECT * FROM `{catalog}`.`{schema}`.`v_tower_health`")
    return kpis, towers


@st.cache_data(show_spinner=False)
def load_demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = Path(__file__).resolve().parents[2] / "data" / "generated"
    metrics = pd.read_csv(data_dir / "cell_tower_metrics.csv", parse_dates=["timestamp"])
    tickets = pd.read_csv(data_dir / "support_tickets.csv", parse_dates=["created_at"])

    valid = metrics[
        metrics["tower_id"].notna()
        & metrics["signal_strength_dbm"].between(-120, -40)
        & metrics["latency_ms"].between(0, 500)
        & metrics["throughput_mbps"].notna()
    ].copy()

    kpis = (
        valid.groupby(["region", "technology"], as_index=False)
        .agg(
            total_towers=("tower_id", "nunique"),
            avg_signal_dbm=("signal_strength_dbm", "mean"),
            avg_latency_ms=("latency_ms", "mean"),
            avg_throughput_mbps=("throughput_mbps", "mean"),
            total_dropped_calls=("dropped_calls", "sum"),
            avg_active_users=("active_users", "mean"),
        )
        .round(1)
    )

    tower_dimensions = [
        "region",
        "commune",
        "latitude",
        "longitude",
        "environment",
        "technology",
        "frequency_band",
    ]
    towers = (
        valid.groupby("tower_id", as_index=False)
        .agg(
            **{column: (column, "first") for column in tower_dimensions},
            avg_signal_dbm=("signal_strength_dbm", "mean"),
            avg_latency_ms=("latency_ms", "mean"),
            avg_throughput_mbps=("throughput_mbps", "mean"),
            total_dropped_calls=("dropped_calls", "sum"),
            avg_active_users=("active_users", "mean"),
        )
        .round(1)
    )
    ticket_kpis = (
        tickets.groupby("tower_id", as_index=False)
        .agg(
            total_tickets=("ticket_id", "count"),
            open_tickets=("status", lambda values: (values == "Abierto").sum()),
            critical_tickets=("severity", lambda values: (values == "Critica").sum()),
        )
    )
    towers = towers.merge(ticket_kpis, on="tower_id", how="left").fillna(0)
    towers["health_status"] = "Saudavel"
    towers.loc[
        (towers.avg_latency_ms > 80)
        | (towers.avg_throughput_mbps < 30)
        | (towers.total_dropped_calls > 400),
        "health_status",
    ] = "Atencao"
    towers.loc[
        (towers.avg_latency_ms > 120)
        | (towers.avg_throughput_mbps < 15)
        | (towers.total_dropped_calls > 700),
        "health_status",
    ] = "Critico"
    return kpis, towers


catalog = os.getenv("TELCO_CATALOG", "telco_workshop")
schema = os.getenv("TELCO_SCHEMA", "red_calidad")
remote_enabled = bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))

try:
    kpis_df, towers_df = load_remote_data(catalog, schema) if remote_enabled else load_demo_data()
    data_source = "Unity Catalog" if remote_enabled else "dados sinteticos locais"
except Exception as exc:
    st.warning(f"Consulta remota indisponivel; usando amostra local. Detalhe: {exc}")
    kpis_df, towers_df = load_demo_data()
    data_source = "dados sinteticos locais"

numeric_columns = [
    "latitude",
    "longitude",
    "avg_signal_dbm",
    "avg_latency_ms",
    "avg_throughput_mbps",
    "total_dropped_calls",
    "total_tickets",
    "open_tickets",
    "critical_tickets",
]
for column in numeric_columns:
    if column in towers_df:
        towers_df[column] = pd.to_numeric(towers_df[column], errors="coerce")

st.title("📡 Monitor de qualidade de rede")
st.caption(f"Visao operacional de uma rede movel chilena ficticia · Fonte: {data_source}")

with st.sidebar:
    st.header("Filtros")
    region_options = sorted(towers_df["region"].dropna().unique())
    selected_regions = st.multiselect("Regiao", region_options, default=region_options)
    technology_options = sorted(towers_df["technology"].dropna().unique())
    selected_technologies = st.multiselect("Tecnologia", technology_options, default=technology_options)
    status_options = sorted(towers_df["health_status"].dropna().unique())
    selected_status = st.multiselect("Status", status_options, default=status_options)

filtered = towers_df[
    towers_df["region"].isin(selected_regions)
    & towers_df["technology"].isin(selected_technologies)
    & towers_df["health_status"].isin(selected_status)
].copy()

if filtered.empty:
    st.info("Nenhuma torre corresponde aos filtros escolhidos.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latencia media", f"{filtered.avg_latency_ms.mean():.1f} ms")
col2.metric("Throughput medio", f"{filtered.avg_throughput_mbps.mean():.1f} Mbps")
col3.metric("Chamadas derrubadas", f"{int(filtered.total_dropped_calls.sum()):,}".replace(",", "."))
col4.metric("Tickets abertos", f"{int(filtered.open_tickets.sum())}")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Distribuicao geografica")
    map_figure = px.scatter_map(
        filtered,
        lat="latitude",
        lon="longitude",
        color="health_status",
        size="total_tickets",
        hover_name="tower_id",
        hover_data=["commune", "technology", "frequency_band", "avg_latency_ms", "avg_throughput_mbps"],
        color_discrete_map={"Saudavel": "#00A972", "Atencao": "#FFAB00", "Critico": "#D32F2F"},
        zoom=3.2,
        height=470,
    )
    map_figure.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(map_figure, width="stretch")

with right:
    st.subheader("Torres com maior latencia")
    worst = filtered.nlargest(12, "avg_latency_ms").sort_values("avg_latency_ms")
    bar_figure = px.bar(
        worst,
        x="avg_latency_ms",
        y="tower_id",
        color="health_status",
        orientation="h",
        labels={"avg_latency_ms": "Latencia media (ms)", "tower_id": "Torre"},
        color_discrete_map={"Saudavel": "#00A972", "Atencao": "#FFAB00", "Critico": "#D32F2F"},
        height=470,
    )
    st.plotly_chart(bar_figure, width="stretch")

st.subheader("Fila de priorizacao operacional")
priority_columns = [
    "tower_id",
    "region",
    "commune",
    "environment",
    "technology",
    "frequency_band",
    "health_status",
    "avg_signal_dbm",
    "avg_latency_ms",
    "avg_throughput_mbps",
    "total_dropped_calls",
    "open_tickets",
]
st.dataframe(
    filtered.sort_values(["health_status", "avg_latency_ms"], ascending=[True, False])[priority_columns],
    hide_index=True,
    width="stretch",
)
