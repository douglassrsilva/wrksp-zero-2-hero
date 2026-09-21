# AI/BI Dashboard — roteiro de construção

Nome: `Qualidade de Rede — <participante>`.

O dashboard é criado pela UI porque o exercício ensina datasets, canvas, filtros e
publicação. As views são preparadas por `05_sql_queries.sql`.

## Datasets

1. `network_kpis`: `SELECT * FROM telco_workshop.red_calidad.v_network_kpis`
2. `tower_health`: `SELECT * FROM telco_workshop.red_calidad.v_tower_health`
3. `hourly_trend`: `SELECT * FROM telco_workshop.red_calidad.v_hourly_network_trend`
4. `quality_summary`: `SELECT * FROM telco_workshop.red_calidad.dqx_quality_summary`

## Canvas de referência

1. Counter: média de `avg_latency_ms`, título “Latência média”.
2. Counter: soma de `total_dropped_calls`, título “Chamadas derrubadas”.
3. Barras: `region` no eixo X e média de `avg_throughput_mbps` no eixo Y; cor por `technology`.
4. Tabela: `tower_id`, `commune`, `health_status`, `avg_latency_ms`, `open_tickets`.
5. Linha: `metric_hour` e `avg_latency_ms`, cor por `technology`.
6. Mapa opcional: `latitude`, `longitude`, cor por `health_status` e tamanho por `total_tickets`.

Adicione filtros de `region`, `technology` e `health_status`. Publique e valide que
alterar tecnologia de 4G para 5G atualiza counters e gráficos.

## Atividade mínima viável

Se o tempo cair abaixo de oito minutos, o instrutor duplica um dashboard previamente
preparado e cada participante cria apenas um filtro e uma visualização. Se AI/BI
Dashboards estiver indisponível, execute os quatro datasets no SQL Editor e mostre o
dashboard de referência do instrutor.

