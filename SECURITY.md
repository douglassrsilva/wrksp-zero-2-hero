# Segurança e privacidade

Este repositório contém somente dados sintéticos. Não inclua exports de produção,
credenciais, tokens, URLs privadas de workspace ou identificadores reais de clientes.

## Valores intencionalmente públicos

- `telco_workshop`: catálogo fictício usado como padrão didático.
- `red_calidad`: schema fictício usado como padrão didático.
- `DATABRICKS_WAREHOUSE_ID`: nome de variável; nenhum valor real é versionado.
- Regiões/comunas e coordenadas aproximadas: informações geográficas públicas usadas
  para gerar sites fictícios.

## Configuração segura

Use Databricks CLI profiles locais, variáveis de ambiente e recursos associados a
Databricks Apps. Nunca grave tokens ou IDs de recursos reais nos arquivos versionados.
O arquivo `databricks.yml` não fixa profile, host ou workspace.

Antes de publicar alterações, execute:

```bash
uv run --extra dev python scripts/validate_local.py
```

