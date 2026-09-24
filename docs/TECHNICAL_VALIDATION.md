# Supuestos y validación técnica

## Decisiones adoptadas

- Público inicial con SQL básico y conceptos de tablas y schemas.
- Entorno recomendado: Unity Catalog, serverless cuando esté disponible y catálogo compartido.
- Caso: calidad y experiencia de una red móvil chilena ficticia, sin datos personales.
- Lakeflow: **Lakeflow Declarative Pipelines**, nombre actual del producto antes conocido
  como Delta Live Tables. El código usa `pyspark.pipelines as dp`.
- DQX: **databricks-labs/dqx**, proyecto de Databricks Labs sin SLA de soporte.
- “Genie Agent”: interpretado como **AI/BI Genie Space**, sin agente personalizado.
- App: **Databricks Apps** con una plantilla Streamlit inicial y Statement Execution
  API sobre SQL Warehouse. La modernización visual es el reto posterior.

## Causa raíz de la falla observada del SDP

Las ejecuciones fallidas del 22/09/2026 muestran `DLTAnalysisException`: las tablas
MANAGED `tower_metrics_silver` y `support_tickets_silver` ya existían cuando el
pipeline intentó materializarlas. Los notebooks de contingencia usaban los mismos
nombres que el SDP.

La corrección reserva al pipeline los nombres de sus objetos. La comparación PySpark
ahora crea únicamente tres tablas descartables `demo_spark_*`; ninguna etapa posterior
las referencia. Las contingencias operacionales usan checkpoints independientes,
preparados por el instructor. La validación posterior completó un full refresh del
DAG ampliado con once Bronze, once Silver y Gold preliminares.

El dry run final también sustituyó `dropDuplicates` por ventanas con orden explícito.
Así, los duplicados se resuelven de forma determinista y SDP produce las mismas
cantidades `validated/quarantine` que el checkpoint SQL.

Una segunda validación detectó que `input_file_name()` no está soportado en esta ruta
de Unity Catalog. Las tablas Bronze ahora obtienen la procedencia desde
`_metadata.file_path`, que es la interfaz compatible con Auto Loader y UC.

## Validación final ejecutada

El informe sanitizado con conteos, contingencias y limitaciones se encuentra en
`DRY_RUN_REPORT.md`. El resultado técnico fue PASS. La inspección visual de la App
remota requiere aceptar un consentimiento OAuth persistente y, por seguridad, quedó
pendiente hasta contar con autorización explícita.

## Validación de la muestra PySpark aislada

`03_alt_spark_etl.py` se ejecutó como tarea serverless independiente. La ejecución
finalizó correctamente y registró exactamente tres tablas:

| Tabla | Filas |
|---|---:|
| `demo_spark_network_sample` | 1.981 |
| `demo_spark_customer_product_sample` | 2.970 |
| `demo_spark_kpis` | 18 |

Los límites solicitados son 2.000 y 3.000; las cantidades finales son menores por la
deduplicación intencional. El preflight falla si cualquiera de estas tablas aparece
como fuente de DQX, checkpoint, Gold, Metric Views, Genie o App.

## Arquitectura FY27

No existe en el material suministrado una referencia oficial verificable llamada
“arquitectura FY27”. La lámina debe presentarse como una visión conceptual provisional
de Data Intelligence Platform. Antes de una sesión externa, el responsable debe
validarla con material FY27 autorizado internamente.

## Puntos que dependen del workspace

- Genie y Apps varían por nube, región, entitlement y plan.
- Crear un catálogo suele exigir privilegios administrativos; use un catálogo compartido.
- DQX requiere acceso al paquete o una biblioteca preinstalada.
- `pyspark.pipelines` requiere un runtime compatible con la versión actual de Lakeflow.
- La App necesita un SQL Warehouse asociado y grants de UC para su service principal.

## Corrección del deck

La agenda del HTML original declaraba 96 minutos de Show, pero sus valores por módulo
sumaban 86. La guía corregida usa 97 minutos de Show/práctica, 48 de Tell y 5 de
margen: 64,7 % de práctica y exactamente 150 minutos.
