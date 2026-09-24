# Informe de dry run técnico

## Resultado

**Fecha:** 24 de septiembre de 2026  
**Resultado técnico:** PASS  
**Confianza:** 9/10

El recorrido completo fue ejecutado en un workspace aislado, con catálogo, schema,
Warehouse, usuario e identificadores omitidos de este informe y del repositorio. El
flujo principal, las contingencias y las experiencias de consumo funcionaron con los
datos sintéticos versionados.

La única comprobación no concluida fue la inspección visual de la App desplegada: el
navegador mostró el consentimiento OAuth «actuar en su nombre». No se concedió un
permiso persistente sin autorización explícita. El estado del servicio, el despliegue,
los recursos, los grants y la interfaz local sí fueron verificados.

## Criterios y resultados

| Componente | Criterio | Resultado | Evidencia sanitizada |
|---|---|---|---|
| Repositorio | Preflight, compilación, Ruff y App local | PASS | Sin excepciones; smoke test Streamlit aprobado |
| Datos | 11 CSV, seed determinista y sin PII | PASS | 100.398 filas |
| Lectura guiada | Los 11 CSV se leen desde UC Volume | PASS | Cantidades y schemas verificados |
| Lakeflow SDP | Full refresh del DAG medallion | PASS | 11 Bronze, 11 Silver y 1 Gold preliminar |
| DQX | Seis fuentes con validated/quarantine | PASS | Conservación integral de filas |
| Checkpoint SQL | Ruta completa sin Lakeflow/DQX | PASS | 11 Silver fallback y seis pares de calidad |
| PySpark comparativo | Muestra aislada, no downstream | PASS | 1.981 + 2.970 filas y 18 KPI |
| Gold | Cinco vistas analíticas consultables | PASS | Conteos documentados abajo |
| Metric Views | Dos vistas y consultas `MEASURE()` | PASS | Ambas consultas de ejemplo finalizaron |
| Dashboard | Publicado y datasets ejecutables | PASS | 4 datasets, 6 widgets, 4 consultas aprobadas |
| Genie Chat | Dos preguntas con SQL revisable | PASS | Respuestas y SQL correctos |
| Genie Agent/Deep Research | Dos investigaciones completas | PASS | Informe, consultas, gráficos, supuestos y acciones |
| Databricks App | Servicio y despliegue | PASS | `RUNNING`, compute activo y deployment exitoso |
| Databricks App | Inspección visual remota | PENDIENTE | Requiere consentimiento OAuth explícito |
| Seguridad del repositorio | Sin PII, secretos o IDs reales | PASS | Búsqueda automatizada sin hallazgos |

## Arquitectura medallion validada

```text
11 CSV sintéticos
  → 11 tablas Bronze con Auto Loader
  → 11 vistas materializadas Silver con enriquecimiento y deduplicación determinista
  → 6 fuentes críticas evaluadas por DQX
  → 5 vistas Gold
  → 2 Metric Views
  → AI/BI Dashboard + Genie Space + Databricks App inicial
```

El SDP usa `pyspark.pipelines`. La deduplicación Silver selecciona de forma
determinista el registro más reciente o el orden de desempate documentado. Esta
corrección eliminó diferencias entre DQX y el checkpoint SQL.

## Calidad de datos

DQX y la contingencia SQL produjeron exactamente los mismos resultados:

| Fuente | Entrada | Validated | Quarantine | Delta |
|---|---:|---:|---:|---:|
| `cell_tower_metrics` | 29.941 | 28.723 | 1.218 | 0 |
| `customer_surveys` | 797 | 779 | 18 | 0 |
| `network_alarms` | 1.195 | 1.162 | 33 | 0 |
| `subscriptions` | 4.179 | 4.093 | 86 | 0 |
| `support_tickets` | 1.493 | 1.469 | 24 | 0 |
| `usage_daily` | 58.041 | 55.854 | 2.187 | 0 |

`04_dqx_quality.py`, `04_alt_sql_quality.sql` y
`05_checkpoint_if_needed.sql` comparten las mismas condiciones críticas. El preflight
también comprueba que existan impurezas deliberadas para el ejercicio.

## Gold y capa semántica

| Objeto Gold | Filas |
|---|---:|
| `gold_customer_360` | 2.985 |
| `gold_customer_product_daily` | 55.854 |
| `gold_incident_impact` | 1.162 |
| `gold_network_hourly` | 18.998 |
| `gold_site_daily_360` | 413 |

Se crearon y consultaron `mv_network_quality` y
`mv_customer_product_experience`. Las consultas de ejemplo validaron agrupaciones de
red, ARPU, NPS, tickets y SLA con `MEASURE()`.

## Dashboard

El dashboard corregido contiene cuatro datasets y seis widgets: tres KPI, una barra,
una dispersión y una tabla. Las consultas devolvieron respectivamente 1, 16, 82 y
100 filas de muestra.

Durante el dry run se descubrió que Lakeview concatena `queryLines` sin insertar
separadores. El generador producía términos unidos como `active_customersFROM`.
`create_dashboard.py` ahora normaliza cada consulta a una única línea y el preflight
incluye una regresión para impedir que el error vuelva.

## Genie

El AI/BI Genie Space usa exclusivamente Gold y Metric Views. Se verificaron dos
preguntas Chat con SQL correcto. También se ejecutaron dos prompts en el modo nativo
**Agent/Deep Research**; ambos concluyeron con metodología, consultas, visualizaciones,
supuestos, limitaciones, sensibilidad y recomendaciones. Los prompts públicos están
en `config/genie_space_instructions.md`.

## App

La App inicial permanece deliberadamente simple: una página, un filtro, tres KPI, un
gráfico y una tabla. Consume cinco Gold mediante un módulo separado de acceso a datos.

Validaciones realizadas:

- smoke test local con Streamlit: PASS;
- estado remoto: `RUNNING`;
- compute remoto: activo;
- deployment: exitoso;
- SQL Warehouse asociado con `CAN_USE`;
- cinco recursos UC asociados con `SELECT`;
- ningún host, perfil, token, catálogo, schema o Warehouse está fijado en código.

La modernización visual continúa siendo el reto posterior al workshop. La pantalla
remota solo debe autorizarse cuando el propietario acepte explícitamente el
consentimiento OAuth.

## Correcciones realizadas durante el dry run

1. Cálculo de filas DQX sin hallazgos corregido para arrays nulos.
2. Parser SQL corregido para no descartar instrucciones después de `USE`.
3. Deduplicación SDP hecha determinista y alineada con el checkpoint.
4. Reglas DQX, alternativa SQL y checkpoint armonizadas.
5. Grants explícitos de las cinco Gold añadidos a la App.
6. Generador parametrizado del AI/BI Dashboard añadido y consultas corregidas.
7. Target genérico de smoke test añadido al bundle.
8. Ruff configurado para reconocer los globals inyectados por Databricks Runtime.

## Seguridad

La revisión no encontró:

- nombre de una operadora real;
- nombres, RUT, teléfonos, correos o direcciones de personas;
- token, password, API key, clave SSH o archivo `.env`;
- host, perfil, e-mail, catálogo, schema, Warehouse o ID real del dry run;
- contenido público en portugués.

Los nombres predeterminados `telco_workshop` y `red_calidad` son ejemplos ficticios,
no identificadores del entorno utilizado.

## Recomendación para el instructor

Ejecute el checklist uno o dos días antes. Mantenga preparado el checkpoint SQL, pero
use SDP y DQX como recorrido principal. Abra la App una vez con la cuenta que hará la
demostración y conceda el consentimiento solo si la política del workspace lo permite.
Después de la sesión, detenga App, pipeline, compute y Warehouse que no sean necesarios.
