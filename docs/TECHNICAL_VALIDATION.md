# Premissas e validação técnica

## Decisões adotadas

- Público iniciante, com SQL básico e conceitos de tabelas/schemas.
- Ambiente recomendado: Unity Catalog, serverless quando disponível e catálogo
  compartilhado. Os nomes padrão são `telco_workshop.red_calidad`.
- Caso: qualidade e experiência de uma rede móvel chilena fictícia, sem dados pessoais.
- Lakeflow: **Lakeflow Declarative Pipelines**, nome atual do produto anteriormente
  conhecido como Delta Live Tables. O código usa `pyspark.pipelines as dp`.
- DQX: **databricks-labs/dqx**, projeto Databricks Labs sem SLA. A API usada é
  `DQEngine.apply_checks_by_metadata_and_split`.
- “Genie Agent”: interpretado como **AI/BI Genie Space**, sem agente customizado.
- App: **Databricks Apps** com Streamlit e Statement Execution API sobre SQL Warehouse.

## Arquitetura FY27

Não há no material fornecido uma referência oficial verificável chamada “arquitetura
FY27”. A lâmina deve ser apresentada como visão conceitual provisória da Data
Intelligence Platform. Antes de uma sessão externa, o responsável deve substituir ou
validar essa lâmina com o material FY27 autorizado internamente. Nenhum componente
novo deve ser apresentado como arquitetura oficial apenas com base no deck atual.

## Pontos que dependem do workspace

- Genie e Apps variam por cloud, região, entitlement e plano.
- Criação de catálogo costuma exigir privilégios administrativos; o fallback é catálogo compartilhado.
- DQX exige acesso ao pacote ou biblioteca pré-instalada.
- A API `pyspark.pipelines` requer runtime compatível com a versão atual de Lakeflow.
- A App precisa de SQL Warehouse associado e grants de UC para seu service principal.

## Correção do deck

A agenda do HTML declara 96 minutos de Show, mas os valores por módulo somam 86.
O roteiro deste repositório usa 100 minutos de Show, 45 de Tell e 5 de buffer: 66,7%
de prática e exatamente 150 minutos.

