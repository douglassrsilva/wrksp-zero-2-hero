# Checklist previo al workshop

## Instructor — uno o dos días antes

- [ ] Validar el acceso al workspace y registrar la nube/región utilizada.
- [ ] Confirmar Unity Catalog y un catálogo con escritura; preferir un catálogo compartido.
- [ ] Conceder `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`, `CREATE VOLUME` y `SELECT`.
- [ ] Confirmar permiso para crear y administrar Lakeflow Declarative Pipelines.
- [ ] Provisionar un SQL Warehouse Serverless o Pro Small y conceder `CAN USE`.
- [ ] Confirmar AI/BI Dashboards, Genie y Databricks Apps en la región y el plan contratado.
- [ ] Ejecutar `00_setup.py` y verificar 11 fuentes y 100.398 filas sintéticas.
- [ ] Confirmar que no existen tablas MANAGED con nombres reservados para el SDP.
- [ ] Ejecutar full refresh del pipeline y verificar 11 Bronze, 11 Silver y Gold preliminares.
- [ ] Instalar/probar DQX y materializar validated, quarantine y quality summary.
- [ ] Ejecutar `05_sql_queries.sql` y `06_metric_views.sql` en el warehouse.
- [ ] Consultar `mv_network_quality` y `mv_customer_product_experience` con `MEASURE()`.
- [ ] Preparar Dashboard, Genie Space y la App inicial.
- [ ] Validar dos preguntas Chat y preparar capturas para Deep Research.
- [ ] Asociar el SQL Warehouse a la App y conceder acceso a su service principal.
- [ ] Probar los notebooks alternativos y confirmar que solo crean tablas `_fallback`.
- [ ] Realizar un dry run cronometrado con una cuenta sin privilegios administrativos.
- [ ] Iniciar el compute 30 minutos antes y pausar los recursos después de la sesión.

## Participantes — antes de la sesión

- [ ] Acceso al workspace confirmado en un navegador actualizado.
- [ ] Repositorio disponible en el workspace o archivos importados.
- [ ] SQL básico: `SELECT`, `WHERE`, `GROUP BY` y `JOIN`.
- [ ] Conceptos básicos de tabla, schema, clave y CSV.
- [ ] Familiaridad con Python deseable, no obligatoria.
- [ ] Sin instalación local cuando todo el trabajo ocurre en el workspace.

## Verificación objetiva

```sql
SELECT current_user(), current_catalog(), current_schema();
SHOW TABLES;
SELECT count(*) FROM cell_tower_metrics_validated;
SELECT count(*) FROM gold_customer_360;
```

Resultados esperados: ambas consultas responden, las tablas de cuarentena contienen
las impurezas intencionales y las Gold no presentan regiones nulas.
