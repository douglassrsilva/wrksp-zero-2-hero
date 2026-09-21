# Checklist pré-workshop

## Instrutor — 1 a 2 dias antes

- [ ] Validar acesso ao workspace e registrar cloud/região utilizada.
- [ ] Confirmar Unity Catalog e um catálogo gravável; preferir catálogo compartilhado.
- [ ] Conceder `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`, `CREATE VOLUME` e `SELECT`.
- [ ] Confirmar permissão para criar/gerenciar Lakeflow Declarative Pipelines.
- [ ] Provisionar SQL Warehouse Serverless ou Pro tamanho Small e conceder `CAN USE`.
- [ ] Confirmar AI/BI Dashboards, Genie e Databricks Apps na região e no plano contratado.
- [ ] Executar `00_setup.py` e verificar 5.000 métricas e 500 tickets.
- [ ] Executar o pipeline e conferir bronze, silver e `tower_kpis_pipeline`.
- [ ] Instalar/testar DQX e materializar validated, quarantine e quality summary.
- [ ] Executar `05_sql_queries.sql` no warehouse.
- [ ] Preparar dashboard, Genie Space e App de referência.
- [ ] Associar o SQL Warehouse à App e conceder acesso ao service principal da App.
- [ ] Testar os notebooks alternativos e o checkpoint de recuperação.
- [ ] Fazer um dry-run cronometrado com outra conta sem privilégios administrativos.
- [ ] Iniciar compute 30 minutos antes e pausar recursos depois da sessão.

## Participantes — antes da sessão

- [ ] Acesso ao workspace confirmado em navegador atualizado.
- [ ] Repo disponível no workspace ou arquivos importados.
- [ ] SQL básico: `SELECT`, `WHERE`, `GROUP BY` e `JOIN`.
- [ ] Conceitos básicos de tabela, schema e CSV.
- [ ] Familiaridade com Python é desejável, não obrigatória.
- [ ] Sem necessidade de instalação local quando todo o trabalho ocorre no workspace.

## Verificação objetiva

Execute antes de abrir a sala:

```sql
SELECT current_user(), current_catalog(), current_schema();
SELECT count(*) FROM telco_workshop.red_calidad.cell_tower_metrics_raw_checkpoint;
SELECT count(*) FROM telco_workshop.red_calidad.support_tickets_raw_checkpoint;
```

Resultados esperados: 5.000 e 500.

