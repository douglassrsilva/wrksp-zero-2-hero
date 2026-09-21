# Configuração do Genie Space

Nome sugerido: `Qualidade de Rede Móvel — <participante>`.

## Objetos de dados

- `telco_workshop.red_calidad.v_network_kpis`
- `telco_workshop.red_calidad.v_tower_health`
- `telco_workshop.red_calidad.v_problem_towers`
- `telco_workshop.red_calidad.v_hourly_network_trend`
- `telco_workshop.red_calidad.support_tickets_silver`

Se o catálogo/schema forem diferentes, substitua os nomes antes de publicar.

## Instruções gerais

Você analisa qualidade operacional de uma rede móvel chilena fictícia.
Responda em português, mantendo os valores categóricos dos dados em espanhol.
Use somente os objetos fornecidos ao Space. Ao comparar qualidade, considere:

- latência menor é melhor;
- throughput, SINR e conformidade de SLA maiores são melhores;
- sinal mais próximo de zero é mais forte; abaixo de -100 dBm é crítico;
- perda de pacotes e chamadas derrubadas menores são melhores;
- uma torre crítica exige priorização quando também possui tickets abertos.

Não interprete `active_users` como pessoas identificadas: é uma contagem sintética agregada.
Não invente cobertura, clientes, receitas ou localidades ausentes.

## Sinônimos

| Termo de negócio | Coluna/definição |
|---|---|
| torre, site, estação | `tower_id` |
| comuna, município | `commune` |
| sinal | `avg_signal_dbm` ou `signal_strength_dbm` |
| velocidade | `avg_throughput_mbps` |
| quedas | `total_dropped_calls` |
| reclamações | `total_tickets` |
| chamados abertos | `open_tickets` |
| SLA | latência ≤ 80 ms, throughput ≥ 20 Mbps e sinal ≥ -95 dBm |

## Consultas certificadas

```sql
-- Cinco torres com maior latência média
SELECT tower_id, region, commune, avg_latency_ms, open_tickets
FROM telco_workshop.red_calidad.v_tower_health
ORDER BY avg_latency_ms DESC
LIMIT 5;
```

```sql
-- Comparação de 4G e 5G por região
SELECT region, technology, avg_latency_ms, avg_throughput_mbps, sla_compliance_pct
FROM telco_workshop.red_calidad.v_network_kpis
ORDER BY region, technology;
```

## Perguntas para o exercício

1. Quais são as cinco torres com maior latência média?
2. Quantos tickets críticos existem por região?
3. Compare o throughput médio entre 4G e 5G por região.
4. Quais torres críticas também possuem tickets abertos?
5. Mostre a tendência horária de latência na região de Antofagasta.

