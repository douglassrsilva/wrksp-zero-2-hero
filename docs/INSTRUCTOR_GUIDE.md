# Guia do instrutor — Databricks do Zero ao Herói

## Resumo do workshop

Público: engenheiros de dados, analistas e arquitetos iniciantes em Databricks. O
participante precisa saber navegar em aplicações web e entender SQL básico, tabelas e
schemas. Python é desejável, mas todas as alterações são pequenas e guiadas.

Objetivo: construir em 150 minutos uma solução de monitoramento de qualidade de rede
móvel, desde CSVs sintéticos até indicadores governados, dashboard, exploração em
linguagem natural e App. Ao final existirão catálogo/schema/volume, pipeline
bronze/silver/gold preliminar, quarentena DQX, views SQL, dashboard, Genie Space e App.

Os dados representam 50 sites fictícios em regiões chilenas, com ambientes urbanos,
costeiros, industriais, rurais, desérticos e de mineração. Coordenadas são aproximadas
e públicas. Não existem nomes, telefones, endereços ou identificadores de clientes.

## Agenda de 150 minutos

| # | Módulo | Min | Tell inicial | Show/prática | Tell final | Resultado |
|---:|---|---:|---:|---:|---:|---|
| 1 | Introdução | 15 | 8 | 5 | 2 | Componentes e fluxo identificados |
| 2 | Unity Catalog | 18 | 3 | 13 | 2 | Schema e volume verificados |
| 3 | Lakeflow | 20 | 3 | 15 | 2 | Bronze, silver e KPI preliminar |
| 4 | DQX | 15 | 2 | 11 | 2 | Validated, quarantine e resumo |
| 5 | SQL Warehouse | 18 | 2 | 14 | 2 | Quatro views de negócio |
| 6 | AI/BI Dashboard | 18 | 2 | 14 | 2 | Dashboard com filtro e 4+ visuais |
| 7 | Genie Space | 15 | 2 | 11 | 2 | Três perguntas respondidas |
| 8 | Databricks Apps | 18 | 2 | 14 | 2 | App adaptada e publicada |
| 9 | Desafio e fechamento | 8 | 5 | 3 | 0 | Critérios e exemplo demonstrados |
|  | Buffer distribuído | 5 |  |  |  | Dúvidas e imprevistos |
|  | **Total** | **150** | **29** | **100** | **16** | **66,7% prático** |

O buffer não é um intervalo; guarde um minuto após UC, Lakeflow, SQL, Dashboard e App.

## 1. Introdução — 15 min

**Objetivo.** Explicar plataforma, fluxo do caso e papéis dos componentes.

**Slides/Tell.** Silos de dados; Lakehouse/Data Intelligence Platform; UC, Lakeflow,
SQL, AI/BI, Genie e Apps; caso de qualidade de rede. Apresente FY27 como visão
conceitual pendente de validação, conforme `TECHNICAL_VALIDATION.md`.

**Show.** Tour de cinco minutos: Workspace, Catalog Explorer, SQL Editor, Workflows e
Apps. Abra `00_setup.py`, mostre widgets e duas amostras sem executar tudo.

**Participantes.** Localizam catálogo compartilhado, SQL Warehouse e pasta do repo.

**Verificação.** Peça que apontem onde governança, transformação e consumo ocorrerão.

**Falha.** Use capturas do instrutor e prossiga; nenhum artefato depende deste tour.

## 2. Unity Catalog — 18 min

**Objetivo.** Entender metastore → catálogo → schema → tabela/volume e permissões.

**Slides (3).** Hierarquia, grants, lineage e por que governança importa em telecom.

**Demo (3).** Catalog Explorer, propriedades de uma tabela e grants do schema.

**Exercício (10).** Abrir `02_unity_catalog.sql`; ajustar widgets; criar/verificar
schema e volume; executar `00_setup.py`; abrir `02_read_csvs.py`; ler os dois diretórios
CSV, conferir schemas, amostras e contagens; localizar arquivos e checkpoints no Explorer.

**Recap (2).** `SHOW VOLUMES` deve retornar `raw_data`; a leitura dos CSVs e os
checkpoints devem retornar 5.000 métricas, 500 tickets e 50 torres.

**Artefato.** Volume e duas tabelas de checkpoint.

**Falha.** Sem `CREATE CATALOG`, use catálogo compartilhado. Sem upload, checkpoints
permitem continuar. UC ausente é incompatível com o hands-on completo; faça demo.

## 3. Lakeflow — 20 min

**Objetivo.** Ingerir CSV com Auto Loader e construir bronze/silver/KPI declarativamente.

**Slides (3).** Lakeflow Declarative Pipelines, arquitetura medallion, DAG e expectations.

**Demo (4).** Abra `03_lakeflow_pipeline.py`, mostre `dp.table`, schema explícito e
expectations. Explique que elas observam anomalias sem removê-las, preservando o DQX.

**Exercício (11).** Abrir pipeline pré-criado; conferir catálogo/schema; executar update;
acompanhar DAG; abrir métricas das expectations; modificar `latencia_faixa_fisica` de
500 para 200; executar novo update se houver tempo.

**Recap (2).** Confirmar `tower_metrics_bronze`, `support_tickets_bronze`, duas silver
e `tower_kpis_pipeline`.

**Falha.** Execute `03_alt_spark_etl.py`. Se dados faltarem, rode `00_setup.py`.

## 4. DQX — 15 min

**Objetivo.** Aplicar regras declarativas e separar dados válidos de quarentena.

**Slides (2).** Dimensões de qualidade, criticality error/warn e posição do DQX no fluxo.

**Demo (3).** Mostre YAML, valide regras e execute uma célula do `04_dqx_quality.py`.

**Exercício (8).** Executar o notebook; examinar `_errors` e `_warnings`; mudar
`min_throughput` de 1 para 10; comparar o resumo; abrir quarantine no Catalog Explorer.

**Recap (2).** Erros são quarentenados; warnings acompanham registros válidos.

**Artefato.** `tower_metrics_validated`, `tower_metrics_quarantine`, `dqx_quality_summary`.

**Falha.** Use `04_alt_sql_quality.sql`; as expectations continuam visíveis no pipeline.

## 5. SQL Warehouse — 18 min

**Objetivo.** Criar uma camada semântica pequena para todos os consumidores.

**Slides (2).** Warehouse, Photon, views e diferença entre dado técnico e KPI.

**Demo (4).** Selecione warehouse, rode um `SELECT`, mostre histórico e perfil.

**Exercício (10).** Execute `05_sql_queries.sql`; inspecione `v_network_kpis`;
identifique três torres problemáticas; altere o SLA de throughput de 20 para 25 em uma
consulta ad hoc; salve a consulta.

**Recap (2).** Dashboard, Genie e App devem consumir as mesmas views.

**Falha.** Execute SQL em notebook conectado a compute. Se etapas anteriores falharam,
rode `05_checkpoint_if_needed.sql` e depois as views.

## 6. AI/BI Dashboard — 18 min

**Objetivo.** Construir uma visão operacional filtrável.

**Slides (2).** Datasets, canvas, filtros, publicação e permissões.

**Demo (4).** Crie o dataset `network_kpis` e uma barra de throughput por região.

**Exercício (10).** Siga `DASHBOARD_GUIDE.md`: dois counters, barras, tabela e filtro
por tecnologia. Participantes rápidos adicionam tendência ou mapa.

**Recap (2).** Trocar o filtro 4G/5G deve atualizar todos os componentes relacionados.

**Falha.** Duplique dashboard de referência ou apresente os resultados no SQL Editor.

## 7. Genie Space — 15 min

**Objetivo.** Explorar dados em linguagem natural com semântica controlada.

**Slides (2).** AI/BI Genie Space, tabelas confiáveis, instruções e SQL gerado. Esclareça
que não é um agente customizado neste workshop.

**Demo (3).** Vincule as quatro views e cole as instruções de `genie_space_instructions.md`.

**Exercício (8).** Faça três perguntas sugeridas; abra o SQL gerado; refine uma instrução
ou sinônimo quando a resposta não usar a view correta.

**Recap (2).** Compare pergunta, SQL e resultado. Registre cinco perguntas úteis.

**Falha.** Demonstração pelo instrutor; participantes executam as consultas certificadas no SQL Editor.

## 8. Databricks Apps — 18 min

**Objetivo.** Adaptar e publicar uma interface operacional sobre as views.

**Slides (2).** Apps, service principal, recurso SQL Warehouse e grants UC.

**Demo (4).** Abra `apps/network-monitor`, mostre `app.py`, `app.yaml` e fallback local.
Inicie o deploy no começo do módulo para absorver latência.

**Exercício (10).** Duplicar template; mudar título; adicionar filtro de banda ou
comuna; publicar; validar mapa, KPIs e tabela. Participantes não provisionam App do zero.

**Recap (2).** Confirme URL e explique compartilhamento/permissões.

**Falha.** Use a app local/amostra do instrutor. Se o deploy demorar, continue com a URL
pré-publicada e deixe o deploy do participante finalizar em segundo plano.

## 9. Desafio final — 8 min

Apresente níveis e critérios em cinco minutos. Nos três minutos práticos, demonstre onde
alterar filtro, gráfico e consulta, e peça que cada participante escolha um nível. A
execução completa é pós-workshop.

**Critério mínimo.** Dashboard com quatro visuais e filtro de data; App com dois filtros
e um gráfico modificado; Genie Space com cinco perguntas documentadas.

**Extensões.** SLA por região; mapa hora/comuna; correlação de tickets; alerta; pipeline
incremental; previsão de anomalias; job programado.

## Riscos e controle de tempo

| Risco | Contingência | Gatilho de decisão |
|---|---|---|
| Permissão UC | Catálogo compartilhado e checkpoints | Primeira falha de `CREATE` |
| Compute atrasado | Serverless/warehouse e demo | Não disponível no minuto 10 |
| Lakeflow indisponível | `03_alt_spark_etl.py` | Erro de entitlement/provisionamento |
| DQX não instala | `04_alt_sql_quality.sql` | Instalação excede 2 minutos |
| Warehouse indisponível | Notebook Spark SQL | Startup excede 3 minutos |
| Dashboard/Genie indisponível | Artefato do instrutor + SQL | Recurso ausente na UI |
| App indisponível/lenta | Fallback local ou App publicada | Deploy excede 3 minutos |
| Atraso geral | Próximo módulo vira demo guiada | Módulo excede 3 minutos |

Não corte o lançamento do desafio. Use os checkpoints para saltar etapas técnicas sem
quebrar a narrativa ponta a ponta.
