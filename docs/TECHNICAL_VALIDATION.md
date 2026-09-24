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

La corrección reserva al pipeline los nombres de sus objetos. Las rutas alternativas
crean objetos `_fallback`, y DQX/SQL reciben el nombre de la tabla fuente mediante
widgets. Esto permite ejecutar la contingencia y luego volver al SDP sin borrar
objetos. La validación posterior completó un full refresh del DAG ampliado con once
Bronze, once Silver y Gold preliminares.

Una segunda validación detectó que `input_file_name()` no está soportado en esta ruta
de Unity Catalog. Las tablas Bronze ahora obtienen la procedencia desde
`_metadata.file_path`, que es la interfaz compatible con Auto Loader y UC.

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
