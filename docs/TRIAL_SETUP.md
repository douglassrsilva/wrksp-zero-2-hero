# Cuenta trial y preparación opcional

Realice esta preparación fuera de los 150 minutos. La disponibilidad, duración,
créditos y servicios de los trials cambian según nube, región y fecha. No suponga que
Genie o Databricks Apps están habilitados.

## Requisitos previos

- Workspace de AWS, Azure o Google Cloud con Unity Catalog.
- Catálogo existente con permiso para crear un schema; el workshop no crea catálogos.
- Compute compatible con notebooks PySpark; se recomienda serverless.
- Lakeflow Declarative Pipelines y permiso de administración.
- SQL Warehouse Serverless/Pro y `CAN USE`.
- AI/BI Dashboards y Genie habilitados.
- Metric Views habilitadas en el SQL Warehouse utilizado.
- Databricks Apps habilitado, cuota disponible y permiso de creación.
- Salida hacia PyPI si DQX se instala con `%pip`.

## Preparación

1. Cree el workspace en la nube/región autorizada por la organización.
2. Habilite Unity Catalog y asocie el workspace a un metastore.
3. Cree un catálogo compartido si los participantes no pueden crear catálogos.
4. Importe este repositorio o despliegue el bundle.
5. Ejecute `00_setup.py`; reserve `05_checkpoint_if_needed.sql` para contingencias.
6. Cree e inicie un SQL Warehouse Small.
7. Verifique Lakeflow, AI/BI, Genie y Apps por separado.
8. Registre qué módulos serán hands on, demo o fallback en esa cuenta.

## Costos y cierre

Use compute pequeño y auto stop corto. No deje el pipeline continuo. Al terminar,
detenga warehouse y compute, detenga Apps innecesarias y retire pipelines de prueba.
No ejecute `DROP CATALOG ... CASCADE` en un catálogo compartido.

## Variante con 15 minutos de preparación dentro de la sesión

| Bloque | Minutos |
|---|---:|
| Login y preparación mínima | 15 |
| Introducción | 10 |
| Unity Catalog | 15 |
| Lakeflow | 18 |
| DQX | 12 |
| SQL | 16 |
| Dashboard | 19 |
| Genie | 12 |
| App inicial | 10 |
| Reto de modernización | 8 |
| Buffer de autenticación/provisionamiento | 15 |
| **Total** | **150** |

En esta variante, pipeline, dashboard, Genie Space y App deben estar creados antes de
la sesión. Los participantes ejecutan o adaptan artefactos sin provisionar servicios.
