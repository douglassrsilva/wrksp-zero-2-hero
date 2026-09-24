# Workshop Databricks — de cero a héroe para telecomunicaciones

Paquete ejecutable para un workshop de 150 minutos sobre calidad de red, clientes
y productos de un operador móvil ficticio. El caso usa datos sintéticos y anónimos
con características geográficas y operativas plausibles para Chile.

## Recorrido

```text
11 CSV en UC Volume → 11 Bronze → 11 Silver → DQX validated/quarantine
                    → 5 Gold → 2 Metric Views
                    → AI/BI Dashboard + Genie Space + App inicial
```

## Estructura

- `notebooks/`: preparación, UC, Lakeflow, DQX, SQL y contingencias.
- `src/telco_workshop/`: generador PySpark reutilizable.
- `data/generated/`: archivos CSV listos para los participantes.
- `config/`: reglas DQX e instrucciones de Genie.
- `apps/network-monitor/`: App Streamlit inicial y reto de modernización.
- `docs/`: guía del instructor, dashboard, checklist, trial y validación.
- `resources/` y `databricks.yml`: Databricks Asset Bundle.

## Ejecución recomendada

1. Lea `docs/TECHNICAL_VALIDATION.md` y `docs/PREWORKSHOP_CHECKLIST.md`.
2. Autentique un perfil: `databricks auth login --profile <profile>`.
3. Valide: `databricks bundle validate -t dev --profile <profile>`.
4. Despliegue: `databricks bundle deploy -t dev --profile <profile>`.
5. Ejecute el job `prepare_workshop` o el notebook `00_setup.py`.
6. Ejecute `02_read_csvs.py` para validar rutas, schemas y cantidades de los CSV.
7. Ejecute el pipeline Lakeflow Bronze–Silver–Gold.
8. Ejecute DQX, `05_sql_queries.sql` y `06_metric_views.sql`.
9. Prepare Dashboard, Genie y la App inicial según las guías.

Los once CSV quedan en:

```text
/Volumes/<catalog>/<schema>/raw_data/<dataset>/
```

`<dataset>` representa `network_sites`, `radio_cells`, `cell_tower_metrics`,
`network_alarms`, `maintenance_orders`, `customers`, `products`, `subscriptions`,
`usage_daily`, `support_tickets` o `customer_surveys`. El notebook
`02_read_csvs.py` usa `spark.read.format("csv")`; Lakeflow usa
`spark.readStream.format("cloudFiles")` sobre los mismos directorios.

El catálogo predeterminado es `telco_workshop.red_calidad`. En entornos sin
`CREATE CATALOG`, use un catálogo compartido y cambie la variable `catalog` del
bundle y los widgets.

## Contingencia sin colisiones con el SDP

Los notebooks alternativos crean `tower_metrics_silver_fallback` y
`support_tickets_silver_fallback`. Nunca crean las tablas que pertenecen al pipeline.
Si usa la contingencia:

1. En `04_dqx_quality.py`, defina `source_table=tower_metrics_silver_fallback`.
2. En `05_sql_queries.sql`, defina `tickets_table=support_tickets_silver_fallback`.
3. Si ejecuta `05_checkpoint_if_needed.sql`, use los mismos parámetros en SQL.

Así se puede volver a ejecutar el SDP sin eliminar tablas manualmente.

## Validación local

```bash
uv run --extra dev python scripts/generate_repo_data.py
uv run --extra dev python scripts/validate_local.py
uv run --extra app streamlit run apps/network-monitor/app.py
```

## Guías visuales

- [Guía completa del instructor](docs/INSTRUCTOR_GUIDE.md)
- [Construcción del AI/BI Dashboard](docs/DASHBOARD_GUIDE.md)
- [App inicial y reto de modernización](apps/network-monitor/README.md)
- [Índice de capturas sanitizadas](docs/images/README.md)
