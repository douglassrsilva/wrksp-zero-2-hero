# Plan de generación de datos sintéticos

## Alcance y decisiones

- Caso anónimo: calidad de red, Customer 360 y desempeño de productos de un
  operador móvil chileno ficticio. No se menciona ninguna empresa real.
- Volumen: aproximadamente 100.000 filas distribuidas en once fuentes.
- Motor: PySpark nativo, por decisión del workshop y porque la ejecución ocurre
  en Databricks. El volumen permitiría una generación local más liviana, pero el
  mismo código Spark se reutilizará en el notebook y en las pruebas.
- Seed: `42`.
- Período fijo: agosto de 2026, para que las ejecuciones sean reproducibles.
- Datos personales: no se generan nombres, RUT, teléfonos, correos, direcciones,
  IMSI, IMEI ni números de línea reales. Todos los identificadores son claves
  ficticias sin significado fuera del conjunto de datos.
- Salida versionada: `data/generated/<dataset>.csv`.
- Salida en Databricks:
  `/Volumes/<catalog>/<schema>/raw_data/<dataset>/`.
- Ejecución local de control:
  `uv run --extra dev python scripts/generate_repo_data.py`.
- Ejecución del workshop: notebook `00_setup.py` en el cómputo Databricks ya
  preparado, con catálogo y schema recibidos por widgets.

## Fuentes

### `network_sites` — 60 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `site_id` | STRING | `SIT-0001`; PK determinista y única. |
| `region` | STRING | Distribución ponderada entre regiones chilenas. |
| `commune` | STRING | Comuna coherente con `region`. |
| `latitude` | DOUBLE | Centro aproximado de la comuna más variación pequeña; no representa una instalación real. |
| `longitude` | DOUBLE | Centro aproximado de la comuna más variación pequeña; no representa una instalación real. |
| `environment` | STRING | `Urbano denso`, `Urbano`, `Periurbano`, `Rural`, `Costero`, `Minero`. |
| `site_type` | STRING | `Azotea`, `Torre`, `Poste`, `Interior`; ponderado por entorno. |
| `ownership_type` | STRING | `Propio` o `Compartido`. |
| `commissioned_date` | DATE | Entre 2017-01-01 y 2026-06-30. |
| `backup_power_hours` | DOUBLE | Entre 0 y 12 horas, correlacionado con entorno. |
| `site_status` | STRING | `Activo`, `Mantenimiento`, `Fuera de servicio`; mayoría activa. |

Impurezas: 1 sitio con `backup_power_hours < 0` y 1 fila duplicada, para
demostrar reglas de dimensión sin afectar el conjunto completo.

### `radio_cells` — 180 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `cell_id` | STRING | `CEL-00001`; PK, tres celdas por sitio. |
| `site_id` | STRING | FK a `network_sites.site_id`. |
| `sector_number` | INT | 1, 2 o 3. |
| `azimuth_degrees` | INT | 0, 120 o 240, con variación controlada. |
| `technology` | STRING | `4G` o `5G`; penetración 5G mayor en áreas urbanas. |
| `frequency_band` | STRING | `B28-700`, `B3-1800`, `B7-2600`, `n28-700` o `n78-3500`, coherente con tecnología. |
| `bandwidth_mhz` | INT | 10, 15, 20, 40, 80 o 100 según banda. |
| `capacity_users` | INT | Entre 600 y 3.500, correlacionado con banda y entorno. |
| `vendor_family` | STRING | `Proveedor A`, `Proveedor B` o `Proveedor C`; sin marca real. |
| `cell_status` | STRING | `Activa`, `Mantenimiento` o `Fuera de servicio`. |

Impurezas: aproximadamente 0,6% con `site_id` inexistente y 0,6% con combinación
tecnología/banda inválida.

### `cell_tower_metrics` — 30.240 filas

Una medición por hora para 180 celdas durante siete días.

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `measurement_id` | STRING | Clave única derivada de celda y hora. |
| `cell_id` | STRING | FK a `radio_cells.cell_id`. |
| `event_ts` | TIMESTAMP | Horario entre 2026-08-01 y 2026-08-07. |
| `availability_pct` | DOUBLE | 85–100; degradada durante alarmas de impacto. |
| `signal_strength_dbm` | DOUBLE | Distribución por tecnología, entorno y carga. |
| `sinr_db` | DOUBLE | Correlacionado con señal y congestión. |
| `latency_ms` | DOUBLE | Menor en 5G; aumenta con carga, señal débil y alarmas. |
| `downlink_mbps` | DOUBLE | Correlacionado con tecnología, banda, señal y carga. |
| `uplink_mbps` | DOUBLE | Correlacionado con downlink y congestión. |
| `packet_loss_pct` | DOUBLE | Aumenta con señal débil y congestión. |
| `dropped_calls` | INT | Poisson aproximada; mayor en celdas degradadas. |
| `active_users` | INT | Curva horaria y capacidad de la celda. |
| `data_traffic_gb` | DOUBLE | Función de usuarios, hora y tecnología. |
| `ingestion_batch_id` | STRING | `BATCH-YYYYMMDD-HH`; permite explicar incrementalidad. |

Impurezas deliberadas: 0,3% de `cell_id` nulo/inexistente; 0,4% de latencia
negativa o superior a 500 ms; 0,4% de señal fuera del rango físico; 0,5% de
downlink nulo; 0,3% de disponibilidad fuera de 0–100; 1% de duplicados.

### `network_alarms` — 1.200 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `alarm_id` | STRING | `ALM-000001`; PK. |
| `cell_id` | STRING | FK a `radio_cells.cell_id`, ponderada hacia celdas degradadas. |
| `opened_at` | TIMESTAMP | Dentro del período de métricas. |
| `closed_at` | TIMESTAMP | Nulo si abierta; posterior a apertura si cerrada. |
| `alarm_type` | STRING | `Energía`, `Transporte`, `Radio`, `Saturación`, `Hardware`, `Software`. |
| `severity` | STRING | `Crítica`, `Alta`, `Media`, `Baja`. |
| `alarm_status` | STRING | `Abierta`, `Reconocida`, `Cerrada`. |
| `probable_cause` | STRING | Categoría coherente con el tipo de alarma. |
| `service_impact` | BOOLEAN | Probabilidad mayor para severidad crítica/alta. |
| `affected_users_est` | INT | Basado en usuarios activos y severidad. |
| `source_system` | STRING | `NMS`, `RAN Monitor` o `Energy Monitor`. |

Impurezas: 0,8% de celda desconocida; 0,5% con cierre anterior a apertura; 0,5%
con severidad inválida; 0,5% de IDs duplicados.

### `maintenance_orders` — 400 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `work_order_id` | STRING | `OT-00001`; PK. |
| `site_id` | STRING | FK a `network_sites.site_id`. |
| `alarm_id` | STRING | FK opcional a `network_alarms.alarm_id`; alrededor de 65% informada. |
| `created_at` | TIMESTAMP | Posterior o igual a la alarma cuando existe. |
| `scheduled_at` | TIMESTAMP | Posterior a creación. |
| `completed_at` | TIMESTAMP | Nulo para órdenes no terminadas. |
| `order_type` | STRING | `Preventiva`, `Correctiva`, `Emergencia`. |
| `priority` | STRING | `P1`, `P2`, `P3`, `P4`. |
| `order_status` | STRING | `Creada`, `Asignada`, `En terreno`, `Completada`, `Cancelada`. |
| `provider_code` | STRING | Código ficticio `PRV-01` a `PRV-05`; no identifica personas. |
| `downtime_minutes` | INT | 0–720; correlacionado con prioridad e impacto. |
| `cost_clp` | DECIMAL(12,2) | Distribución log-normal aproximada en pesos chilenos. |
| `sla_target_hours` | INT | 2, 4, 8, 24 o 72 según prioridad. |

Impurezas: 0,5% de sitio desconocido; 0,5% con finalización anterior a creación;
0,5% con costo negativo; 0,5% de prioridad inválida.

### `products` — 18 filas

Catálogo ficticio con planes prepago, postpago y empresas. Los nombres son
genéricos y no corresponden a ofertas reales.

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `product_id` | STRING | `PRD-001`; PK. |
| `product_name` | STRING | Nombre ficticio en español, por ejemplo `Plan Móvil 80 GB`. |
| `product_family` | STRING | `Prepago`, `Postpago`, `Empresa`, `Datos`. |
| `customer_type` | STRING | `Persona` o `Empresa`. |
| `data_allowance_gb` | DOUBLE | 5–300; nulo cuando el plan es ilimitado. |
| `unlimited_data` | BOOLEAN | Coherente con franquicia nula. |
| `voice_minutes` | INT | 100–2.000; nulo cuando la voz es ilimitada. |
| `unlimited_voice` | BOOLEAN | Coherente con minutos nulos. |
| `sms_allowance` | INT | 50–2.000. |
| `monthly_price_clp` | DECIMAL(10,2) | 5.000–79.990 CLP según familia y beneficios. |
| `overage_price_per_gb_clp` | DECIMAL(10,2) | Cero o 500–3.000 CLP. |
| `is_5g_enabled` | BOOLEAN | Mayoría de planes postpago y empresa. |
| `product_status` | STRING | `Activo` o `Retirado`. |
| `valid_from` | DATE | Entre 2022-01-01 y 2026-06-30. |
| `valid_to` | DATE | Nulo para activos; posterior a `valid_from` para retirados. |

Impurezas: 1 producto con precio negativo y 1 producto con franquicia/ilimitado
inconsistente.

### `customers` — 3.000 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `customer_id` | STRING | `CLI-000001`; clave ficticia, sin relación con RUT. |
| `customer_type` | STRING | `Persona` o `Empresa`. |
| `customer_segment` | STRING | `Prepago`, `Postpago`, `Pyme`, `Corporativo`. |
| `region` | STRING | Región agregada; no es dirección. |
| `commune` | STRING | Comuna agregada coherente con la región; no es dirección. |
| `age_band` | STRING | `18-24`, `25-34`, `35-44`, `45-54`, `55+`; nulo para empresas. |
| `created_date` | DATE | Entre 2018-01-01 y 2026-07-31. |
| `acquisition_channel` | STRING | `Digital`, `Tienda`, `Call center`, `Distribuidor`. |
| `preferred_channel` | STRING | `App`, `Web`, `WhatsApp`, `Call center`, `Tienda`; preferencia sintética, sin dato de contacto. |
| `digital_engagement_score` | INT | 0–100, correlacionado con canal y antigüedad. |
| `analytics_consent` | BOOLEAN | Bandera sintética para conversación de gobierno y privacidad. |
| `customer_status` | STRING | `Activo`, `Suspendido`, `Baja`. |

Impurezas: 0,5% de IDs duplicados; 0,5% con segmento nulo/incompatible; 0,4%
con score fuera de 0–100; 0,4% con comuna incompatible con región.

### `subscriptions` — 4.200 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `subscription_id` | STRING | `SUB-000001`; PK. |
| `customer_id` | STRING | FK a `customers.customer_id`. |
| `product_id` | STRING | FK a `products.product_id`, coherente con tipo/segmento. |
| `line_id` | STRING | `LIN-000001`; clave ficticia, nunca un número telefónico. |
| `start_date` | DATE | Posterior o igual a la fecha de alta del cliente. |
| `end_date` | DATE | Nulo para activas; posterior al inicio para bajas. |
| `subscription_status` | STRING | `Activa`, `Suspendida`, `Baja`. |
| `contract_type` | STRING | `Prepago`, `Sin permanencia`, `12 meses`, `24 meses`. |
| `is_port_in` | BOOLEAN | Indicador sin operador de origen. |
| `is_esim` | BOOLEAN | Probabilidad mayor en planes 5G. |
| `autopay_enabled` | BOOLEAN | Solo aplicable a productos facturados. |
| `monthly_fee_clp` | DECIMAL(10,2) | Precio del producto con descuento controlado. |
| `billing_day` | INT | 1–28 para facturados; nulo para prepago. |

Impurezas: 0,5% de cliente inexistente; 0,5% de producto inexistente; 0,4% con
fin anterior al inicio; 0,4% con mensualidad negativa; 0,5% de duplicados.

### `usage_daily` — 58.800 filas

Una fila por suscripción y día durante catorce días.

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `usage_date` | DATE | 2026-08-01 a 2026-08-14. |
| `subscription_id` | STRING | FK a `subscriptions.subscription_id`. |
| `primary_cell_id` | STRING | FK a `radio_cells.cell_id`, ponderada por comuna del cliente. |
| `data_gb` | DOUBLE | Gamma aproximada, correlacionada con plan y día de semana. |
| `voice_minutes` | DOUBLE | Sesgada a la derecha, por segmento. |
| `sms_count` | INT | Distribución de conteo, generalmente baja. |
| `data_5g_pct` | DOUBLE | 0–100; cero para líneas/productos no habilitados. |
| `roaming_data_mb` | DOUBLE | Cero en la mayoría de filas; cola larga en una minoría. |
| `dropped_calls` | INT | Correlacionado con la celda primaria y la calidad de red. |
| `recharge_amount_clp` | DECIMAL(10,2) | Nulo para postpago/empresa; eventos discretos para prepago. |
| `billed_amount_clp` | DECIMAL(10,2) | Prorrateo diario de mensualidad y excedentes. |
| `ingestion_batch_id` | STRING | `USAGE-YYYYMMDD`; incrementalidad y trazabilidad. |

Impurezas: 0,4% de suscripción desconocida; 0,5% de celda nula/inexistente; 0,4%
de consumo negativo; 0,3% de porcentaje 5G fuera de 0–100; 1% de duplicados.

### `support_tickets` — 1.500 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `ticket_id` | STRING | `TKT-000001`; PK. |
| `customer_id` | STRING | FK a `customers.customer_id`. |
| `subscription_id` | STRING | FK a `subscriptions.subscription_id`. |
| `cell_id` | STRING | FK opcional a la celda principal cuando el motivo es de red. |
| `created_at` | TIMESTAMP | Dentro del período de análisis. |
| `resolved_at` | TIMESTAMP | Nulo para abiertos; posterior a creación para resueltos. |
| `category` | STRING | `Cobertura`, `Velocidad`, `Llamadas`, `Facturación`, `Plan`, `Portabilidad`. |
| `severity` | STRING | `Crítica`, `Alta`, `Media`, `Baja`. |
| `ticket_status` | STRING | `Abierto`, `En progreso`, `Resuelto`, `Cerrado`. |
| `channel` | STRING | `App`, `Web`, `Call center`, `Tienda`, `WhatsApp`. |
| `first_contact_resolution` | BOOLEAN | Nulo si sigue abierto; correlacionado con categoría. |
| `sla_target_hours` | INT | 4, 8, 24, 48 o 72 según severidad. |
| `resolution_hours` | DOUBLE | Derivado de timestamps cuando está resuelto. |
| `post_service_csat` | INT | 1–5; nulo si no hubo evaluación. |

Impurezas: 0,5% de cliente/suscripción inexistente; 0,5% de celda desconocida;
0,4% con resolución anterior a creación; 0,4% de categoría nula; 0,4% de horas
de resolución negativas; 0,5% de IDs duplicados.

### `customer_surveys` — 800 filas

| Columna | Tipo | Generación y reglas |
|---|---|---|
| `survey_id` | STRING | `ENC-000001`; PK. |
| `customer_id` | STRING | FK a `customers.customer_id`. |
| `subscription_id` | STRING | FK a `subscriptions.subscription_id`. |
| `response_date` | DATE | Dentro del período de análisis. |
| `survey_trigger` | STRING | `Periódica`, `Cierre de ticket`, `Alta`, `Cambio de plan`. |
| `nps_score` | INT | 0–10; degradado por mala red o tickets repetidos. |
| `csat_score` | INT | 1–5; correlacionado con NPS. |
| `experience_area` | STRING | `Red`, `Atención`, `Producto`, `Facturación`, `App`. |
| `feedback_category` | STRING | Categoría controlada; no se genera texto libre. |
| `survey_channel` | STRING | `App`, `Web`, `SMS`; no contiene número real. |

Impurezas: 0,5% de cliente/suscripción inexistente; 0,5% de NPS fuera de 0–10;
0,5% de CSAT fuera de 1–5; 0,5% de duplicados.

## Relaciones

- `radio_cells.site_id` → `network_sites.site_id`.
- `cell_tower_metrics.cell_id` → `radio_cells.cell_id`.
- `network_alarms.cell_id` → `radio_cells.cell_id`.
- `maintenance_orders.site_id` → `network_sites.site_id`.
- `maintenance_orders.alarm_id` → `network_alarms.alarm_id`.
- `subscriptions.customer_id` → `customers.customer_id`.
- `subscriptions.product_id` → `products.product_id`.
- `usage_daily.subscription_id` → `subscriptions.subscription_id`.
- `usage_daily.primary_cell_id` → `radio_cells.cell_id`.
- `support_tickets.customer_id` → `customers.customer_id`.
- `support_tickets.subscription_id` → `subscriptions.subscription_id`.
- `support_tickets.cell_id` → `radio_cells.cell_id`.
- `customer_surveys.customer_id` → `customers.customer_id`.
- `customer_surveys.subscription_id` → `subscriptions.subscription_id`.

Las impurezas de claves foráneas son intencionales y deben terminar en las tablas
de cuarentena, no en Gold.

## Arquitectura medallón

### Bronze

- Una streaming table por fuente, ingerida con Auto Loader desde el volumen.
- Schema explícito, `_ingested_at`, `_source_file` desde `_metadata.file_path`,
  `_rescued_data` e `ingestion_batch_id` cuando aplique.
- Expectations de observación para mostrar métricas de calidad sin descartar
  silenciosamente los errores.

### Silver

- Estandarización de nombres y estados en español.
- Deduplicación por PK y timestamp de ingestión.
- Validación de tipos, rangos, fechas y claves foráneas.
- DQX genera `<dataset>_validated` y `<dataset>_quarantine` para las fuentes
  críticas. En el ejercicio guiado se trabajará con métricas, suscripciones y
  tickets; las demás reglas quedarán preparadas.
- Enriquecimiento de telemetría con sitio/celda; uso con cliente/producto; alarmas
  con mantenimiento; tickets y encuestas con contexto de red.

### Gold

- `gold_network_hourly`: KPIs por hora, región, comuna, sitio, tecnología y banda.
- `gold_site_daily_360`: red, alarmas, mantenimiento, tickets y líneas afectadas
  por sitio/día.
- `gold_customer_360`: una fila por cliente con productos, consumo, experiencia,
  atención, NPS y riesgo calculado; sin PII.
- `gold_customer_product_daily`: cliente, suscripción y producto por día, con uso,
  facturación y calidad de red asociada.
- `gold_incident_impact`: alarma/orden de trabajo con impacto de red, clientes,
  líneas y SLA.

## Metric Views de Unity Catalog

Se crearán con SQL DDL y YAML, separadas del SDP, y se consultarán con
`MEASURE()`. Dashboard y Genie usarán estos mismos objetos semánticos.

### `mv_network_quality`

Fuente: `gold_network_hourly` con dimensiones `metric_hour`, `metric_date`,
`region`, `commune`, `site_id`, `technology`, `frequency_band`, `environment` y
`health_status`.

Medidas:

- `Active Sites`, `Active Cells`, `Average Availability`, `Average Signal`,
  `Average SINR`, `Average Latency`, `Average Downlink`, `Average Uplink`,
  `Packet Loss`, `Dropped Calls`, `Data Traffic`, `Active Users`,
  `Service Impact Alarms`, `Impacted Subscriptions` y `Network SLA Compliance`.

### `mv_customer_product_experience`

Fuente: `gold_customer_product_daily` con dimensiones `usage_date`, `region`,
`commune`, `customer_type`, `customer_segment`, `product_id`, `product_name`,
`product_family`, `contract_type`, `subscription_status`, `technology` y
`primary_site_id`.

Medidas:

- `Active Customers`, `Active Subscriptions`, `Billed Revenue`, `ARPU`,
  `Data Usage`, `Voice Usage`, `Recharge Revenue`, `Tickets`, `Network Tickets`,
  `First Contact Resolution`, `Average Resolution Hours`, `Average CSAT`, `NPS`,
  `High Risk Customers` y `Customer Network SLA Compliance`.

Sinónimos, nombres visibles, formatos y comentarios en español se incorporarán
como metadatos para mejorar las respuestas de Genie.

## Genie Agent

Se creará un Genie Agent llamado `Analista 360 de Red y Clientes`. La
configuración del repositorio será parametrizada y no incluirá ID de warehouse,
usuario, catálogo, schema, token ni URL del workspace.

### Fuentes gobernadas

- Fuentes semánticas primarias: `mv_network_quality` y
  `mv_customer_product_experience`.
- Fuentes de detalle para investigación: `gold_site_daily_360`,
  `gold_customer_360` y `gold_incident_impact`.
- SQL Warehouse Pro o Serverless recibido como parámetro durante el despliegue.

### Instrucciones del Agent

- Responder en español y explicar los términos técnicos para un público de
  telecomunicaciones.
- Usar las Metric Views para todos los KPIs certificados y las tablas Gold solo
  para detalle, diagnóstico o trazabilidad.
- Interpretar ingresos, ARPU, recargas y costos en CLP.
- Respetar el período fijo del conjunto sintético; no interpretar “últimos días”
  respecto de la fecha actual.
- Diferenciar correlación de causalidad y declarar supuestos o datos faltantes.
- Mostrar filtros, período, dimensiones y medidas utilizados; cuando corresponda,
  incluir o permitir inspeccionar el SQL generado.
- No intentar inferir nombres, teléfonos, RUT, direcciones ni otra PII. Los IDs
  `CLI-*`, `LIN-*` y `SUB-*` son identificadores ficticios.
- No mencionar ninguna empresa real ni afirmar que los resultados representan
  producción.

La configuración incluirá preguntas sugeridas, instrucciones, relaciones,
sinónimos y al menos cinco ejemplos SQL probados, siguiendo la recomendación de
calidad de Genie Agents.

### Dos preguntas para modo Chat

1. **Calidad de red:** “Compara disponibilidad, latencia, throughput y
   cumplimiento del SLA por región y tecnología durante los siete días de
   telemetría. Muéstrame las tres combinaciones con peor desempeño.”
2. **Clientes y productos:** “¿Qué cinco productos tienen mayor ARPU y cómo se
   comparan en consumo de datos, tickets por cada 100 líneas activas, NPS y
   cumplimiento del SLA de red?”

### Dos investigaciones para modo Deep Research

1. **Causa e impacto de degradaciones:** “Investiga las regiones cuyo
   cumplimiento del SLA de red esté por debajo de 95%. Cruza calidad de celdas,
   alarmas, órdenes de mantenimiento, tickets, líneas afectadas, consumo y NPS.
   Identifica patrones y causas probables, cuantifica el impacto por segmento y
   producto, diferencia correlación de causalidad y propone cinco acciones
   priorizadas con la evidencia que respalda cada una.”
2. **Churn y migración de productos:** “Evalúa conjuntamente riesgo de baja y
   oportunidad de migración de plan. Busca segmentos con consumo cercano o
   superior a la franquicia, mala experiencia de red, tickets repetidos o NPS
   bajo; compara rentabilidad y experiencia entre productos y regiones; estima
   el universo afectado y recomienda acciones de red, atención y portafolio.
   Incluye metodología, supuestos, limitaciones y análisis de sensibilidad.”

### Creación y validación

- Crear el Agent con la API oficial `POST /api/2.0/genie/spaces`, usando un
  archivo JSON templateado y `serialized_space` versión 2.
- Registrar las Metric Views, Gold, instrucciones, preguntas sugeridas, cinco
  ejemplos SQL y benchmarks.
- Ejecutar y revisar las dos preguntas de Chat; guardar los resultados esperados
  y las consultas generadas como guía del instructor.
- Ejecutar las dos preguntas de Deep Research desde la interfaz del workspace y
  registrar capturas/resultados de control cuando el recurso esté habilitado.
- Contingencia: la documentación pública consultada confirma Genie Agents y su
  API, pero no documenta un campo de API llamado `Deep Research`. La
  disponibilidad y el nombre exacto de ese modo deben validarse en el workspace.
  Si no estuviera habilitado, conservar las dos preguntas como investigación
  guiada de varios pasos en Chat, sin presentarlo como una capacidad disponible.

## Comparación SDP frente a Spark tradicional

El repositorio mostrará la misma transformación seleccionada de dos maneras:

1. SDP/Lakeflow: DAG declarativo, Auto Loader, lineage, expectations, reintentos,
   estado incremental, observabilidad y gobierno administrados.
2. PySpark tradicional: lectura, orden de ejecución, checkpoints, deduplicación,
   dependencias, reintentos y publicación coordinados manualmente.

La comparación será honesta: PySpark seguirá siendo el motor; la ventaja de SDP
está en la gestión declarativa y operativa del pipeline, no en sustituir Spark.

## Criterios de aceptación

- Las cantidades, PK/FK y correlaciones se validan automáticamente.
- Cada impureza intencional tiene una regla DQX y una expectativa asociada.
- Ninguna columna contiene PII o secretos.
- Las tablas Gold no contienen claves huérfanas ni registros en cuarentena.
- Las dos Metric Views responden consultas con `MEASURE()` en SQL Warehouse.
- El Genie Agent se crea sin secretos ni IDs personales en el repositorio y
  responde correctamente las dos preguntas de Chat.
- Las dos preguntas de Deep Research se prueban cuando el modo está disponible o
  se documenta explícitamente la contingencia de Chat guiado.
- Dashboard, Genie y App consumen Gold o Metric Views, no CSV ni Bronze.
- Todos los notebooks, valores de negocio y comentarios visibles están en español.
