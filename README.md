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

## Muestra PySpark aislada

`03_alt_spark_etl.py` sirve exclusivamente para comparar código PySpark imperativo
con SDP. Crea una muestra determinista en tres tablas descartables:

- `demo_spark_network_sample`
- `demo_spark_customer_product_sample`
- `demo_spark_kpis`

Ningún artefacto posterior las consume. Si SDP no está disponible, use checkpoints
preparados por el instructor; no continúe DQX o Gold desde esta muestra.

## Preflight del repositorio — solo instructor/CI

Este preflight verifica archivos, contratos, impurezas, sintaxis y aislamiento de la
muestra. No forma parte de los 150 minutos y no valida SDP, DQX, SQL Warehouse,
Metric Views, Genie, permisos ni la App desplegada.

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
- [Informe del dry run técnico](docs/DRY_RUN_REPORT.md)
