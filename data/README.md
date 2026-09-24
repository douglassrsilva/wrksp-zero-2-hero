# Datos sintéticos

Los archivos representan la red, los clientes y los productos de un operador móvil
chileno ficticio. Son deterministas y no contienen nombres, RUT, teléfonos, correos,
direcciones ni IDs reales. Las coordenadas parten de referencias geográficas públicas
y reciben desplazamientos reproducibles para crear sitios ficticios.

## Fuentes y volumen

| Archivo | Filas | Contenido |
|---|---:|---|
| `network_sites.csv` | 60 | Sitios, ubicación aproximada, tipo y entorno |
| `radio_cells.csv` | 180 | Celdas, tecnología, banda y capacidad |
| `cell_tower_metrics.csv` | 30.240 | Calidad, tráfico y disponibilidad por celda/hora |
| `network_alarms.csv` | 1.200 | Alarmas, causa probable e impacto estimado |
| `maintenance_orders.csv` | 400 | Órdenes, prioridad, tiempo fuera de servicio y costo |
| `customers.csv` | 3.000 | Perfil sintético sin PII, segmento y región |
| `products.csv` | 18 | Planes prepago, postpago, datos y empresa |
| `subscriptions.csv` | 4.200 | Relación anónima cliente–producto–línea |
| `usage_daily.csv` | 58.800 | Uso, facturación y celda principal por día |
| `support_tickets.csv` | 1.500 | Atención, motivo, estado y resolución |
| `customer_surveys.csv` | 800 | NPS y CSAT sintéticos |
| **Total** | **100.398** | Once fuentes relacionadas |

El esquema completo, las distribuciones y las relaciones están documentados en
[`docs/DATA_GENERATION_PLAN.md`](../docs/DATA_GENERATION_PLAN.md).

## Impurezas intencionales para DQX

Una fracción pequeña y reproducible contiene problemas como claves nulas o
duplicadas, fechas inconsistentes, región ausente, métricas fuera de rango, valores
negativos o relaciones inválidas. Las impurezas permiten demostrar:

- observación con expectations en Lakeflow;
- reglas declarativas de DQX;
- separación entre `validated` y `quarantine`;
- construcción de Gold exclusivamente con registros confiables.

Las anomalías nunca contienen información personal ni secretos. No deben corregirse
manualmente en los CSV antes del workshop.

## Generación y validación

Desde la raíz del repositorio:

```bash
uv run --extra dev python scripts/generate_repo_data.py
uv run --extra dev python scripts/validate_local.py
```

Use `seed=42` para conservar los resultados esperados del material del instructor.
