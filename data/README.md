# Dados sintéticos

Os arquivos representam uma rede móvel chilena fictícia. Todos os IDs são gerados e
não existe informação pessoal. As coordenadas são aproximações de centros urbanos,
deslocadas deterministicamente para criar sites fictícios.

## `cell_tower_metrics.csv` — 5.000 linhas

| Coluna | Tipo | Uso |
|---|---|---|
| `tower_id` | string | Site fictício `TWR-001` a `TWR-050` |
| `timestamp` | timestamp | Cem medições por site em sete dias |
| `region`, `commune` | string | Localização operacional |
| `latitude`, `longitude` | double | Coordenadas aproximadas do site fictício |
| `environment` | string | Urbano, costeiro, rural, industrial, desértico etc. |
| `frequency_band` | string | `B28-700`, `B3-1800`, `B7-2600` ou `n78-3500` |
| `signal_strength_dbm` | double | Proxy simplificada de RSRP, em dBm |
| `sinr_db` | double | Relação sinal-interferência-ruído |
| `latency_ms` | double | Latência estimada |
| `throughput_mbps` | double | Vazão estimada |
| `packet_loss_pct` | double | Percentual de perda de pacotes |
| `dropped_calls` | integer | Quedas no intervalo |
| `active_users` | integer | Contagem agregada sintética |
| `technology` | string | 4G ou 5G |

Há falhas controladas: IDs nulos, sinal fora de faixa, latência negativa/acima do
limite e throughput nulo. Elas existem para Lakeflow expectations e DQX.

## `support_tickets.csv` — 500 linhas

| Coluna | Tipo | Uso |
|---|---|---|
| `ticket_id` | string | Ticket fictício |
| `tower_id` | string | FK para torre |
| `region`, `commune` | string | Área afetada |
| `created_at` | timestamp | Abertura |
| `category` | string | Señal, Velocidad, Llamadas ou Cobertura |
| `severity` | string | Baja, Media, Alta ou Critica |
| `status` | string | Abierto, En progreso ou Resuelto |
| `channel` | string | App, call center, web ou tienda |
| `customer_segment` | string | Prepago, Postpago ou Empresas |
| `resolution_hours` | double | Preenchido para tickets resolvidos |

Sites com maior risco técnico recebem entre 5 e 15 tickets; assim, a correlação é
perceptível em SQL, dashboard, Genie e App.

