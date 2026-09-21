# Monitor de qualidade de rede

App Streamlit para o módulo Databricks Apps. Ela consulta as views
`v_network_kpis` e `v_tower_health` por meio da Statement Execution API.
Sem `DATABRICKS_WAREHOUSE_ID`, usa os CSVs sintéticos do repositório.

## Execução local

```bash
uv run --with-requirements requirements.txt streamlit run app.py
```

Execute a partir da raiz do repositório para habilitar o fallback local.

## Databricks Apps

1. Crie a app e associe um SQL Warehouse como recurso com `CAN USE`.
2. Defina `DATABRICKS_WAREHOUSE_ID` com o ID do warehouse associado.
3. Ajuste `TELCO_CATALOG` e `TELCO_SCHEMA` em `app.yaml`, se necessário.
4. Faça o deploy desta pasta como código-fonte da app.
5. Conceda ao service principal da app `USE CATALOG`, `USE SCHEMA` e `SELECT`
   nas views do workshop.

O exercício dos participantes é mudar o título, escolher um filtro adicional e
adicionar um gráfico. A versão entregue já funciona como solução de referência.

