# Conta trial e preparação opcional

Faça esta preparação fora dos 150 minutos. A disponibilidade, duração, créditos e
serviços de trials mudam por cloud, região e data; confirme na página de contratação
antes de convidar participantes. Não presuma que Genie ou Databricks Apps estejam
habilitados.

## Pré-requisitos

- Workspace AWS, Azure ou Google Cloud com Unity Catalog.
- Catálogo existente ou permissão `CREATE CATALOG`.
- Compute compatível com notebooks PySpark; serverless é preferível.
- Lakeflow Declarative Pipelines e permissão de gerenciamento.
- SQL Warehouse Serverless/Pro e `CAN USE`.
- AI/BI Dashboards e Genie habilitados.
- Databricks Apps habilitado, quota disponível e permissão de criação.
- Saída para PyPI se o DQX for instalado com `%pip`.

## Preparação

1. Crie o workspace na cloud/região autorizada pela organização.
2. Habilite Unity Catalog e associe o workspace a um metastore.
3. Crie um catálogo compartilhado se participantes não puderem criar catálogos.
4. Importe este repositório ou implante o bundle.
5. Execute `00_setup.py` e `05_checkpoint_if_needed.sql` como contingência.
6. Crie e inicie um SQL Warehouse tamanho Small.
7. Verifique Lakeflow, AI/BI, Genie e Apps separadamente.
8. Registre quais módulos serão “hands-on”, “demo” ou “fallback” naquela conta.

## Custos e encerramento

Use compute pequeno e auto-stop curto. Não deixe pipeline contínuo. Ao terminar,
pause warehouse e compute, interrompa Apps desnecessárias e remova pipelines de teste.
Não execute `DROP CATALOG ... CASCADE` em catálogo compartilhado.

## Variante com 15 minutos de setup dentro da sessão

| Bloco | Minutos |
|---|---:|
| Login e setup mínimo | 15 |
| Introdução | 10 |
| Unity Catalog | 15 |
| Lakeflow | 18 |
| DQX | 12 |
| SQL | 16 |
| Dashboard | 16 |
| Genie | 12 |
| App | 15 |
| Desafio | 6 |
| Buffer de autenticação/provisionamento | 15 |
| **Total** | **150** |

Nesta variante, pipeline, dashboard, Genie Space e App devem estar pré-criados; os
participantes executam ou adaptam artefatos, sem provisionar serviços do zero.

