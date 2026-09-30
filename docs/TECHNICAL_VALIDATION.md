# Validación técnica previa al workshop

## Decisiones adoptadas

- Público inicial con SQL básico y conceptos de tablas y schemas.
- Entorno recomendado: Unity Catalog, serverless cuando esté disponible y catálogo
  compartido.
- Caso: calidad y experiencia de una red móvil chilena ficticia, sin datos personales.
- Lakeflow: **Lakeflow Declarative Pipelines**, nombre actual del producto antes conocido
  como Delta Live Tables. El código usa `pyspark.pipelines as dp`.
- DQX: **databricks-labs/dqx**, proyecto de Databricks Labs sin SLA de soporte.
- “Genie Agent”: interpretado como **AI/BI Genie Space**, sin agente personalizado.
- App: **Databricks Apps** con una plantilla Streamlit inicial y Statement Execution
  API sobre SQL Warehouse. La modernización visual es el reto posterior.

## Arquitectura FY27

No existe en el material suministrado una referencia oficial verificable llamada
“arquitectura FY27”. La lámina debe presentarse como una visión conceptual provisional
de Data Intelligence Platform. Antes de una sesión externa, el responsable debe
validarla con material FY27 autorizado internamente.

## Validaciones obligatorias del entorno

- El workspace, la nube, la región y el plan ofrecen Unity Catalog, Lakeflow
  Declarative Pipelines, AI/BI Dashboards, Metric Views, Genie y Databricks Apps.
- El instructor puede usar un catálogo compartido o dispone de `CREATE CATALOG`; los
  participantes tienen `USE CATALOG`, `USE SCHEMA`, `SELECT` y los permisos de creación
  previstos en el laboratorio.
- El SQL Warehouse está activo y los participantes tienen `CAN USE`.
- El runtime de Lakeflow admite `pyspark.pipelines`; el pipeline es el propietario
  exclusivo de sus objetos Bronze y Silver.
- DQX está instalado o puede descargarse antes de la sesión. Por ser un proyecto de
  Databricks Labs, la alternativa SQL debe permanecer preparada.
- El Genie Space puede consultar las vistas Gold y las Metric Views.
- La identidad de servicio de la App tiene acceso al SQL Warehouse y `SELECT` en los
  objetos Gold utilizados.
- Los perfiles, hosts, IDs y credenciales permanecen en la configuración local y nunca
  en archivos versionados.

## Comprobaciones recomendadas

- Ejecute `uv run --extra dev python scripts/validate_local.py` antes de desplegar.
- Valide el bundle para el target y el perfil que serán usados en la sesión.
- Haga un ensayo del pipeline, DQX, las consultas SQL, el Dashboard, Genie y la App.
- Mantenga disponibles los checkpoints SQL documentados para una contingencia, sin
  mezclar sus tablas con los objetos administrados por Lakeflow.
