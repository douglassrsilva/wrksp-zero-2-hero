# Workshop Databricks — do Zero ao Herói para Telecom

Pacote executável para uma oficina de 150 minutos sobre qualidade de rede móvel. O
caso usa dados sintéticos e anônimos com características geográficas e operacionais
plausíveis para o Chile.

## Jornada

```text
UC Volume → Lakeflow bronze/silver → DQX validated/quarantine
          → SQL views → AI/BI Dashboard + Genie Space + Databricks App
```

## Estrutura

- `notebooks/`: setup, UC, Lakeflow, DQX, SQL e contingências.
- `src/telco_workshop/`: gerador PySpark reutilizável.
- `data/generated/`: CSVs prontos para participantes.
- `config/`: regras DQX e instruções do Genie.
- `apps/network-monitor/`: App Streamlit com fallback local.
- `docs/`: roteiro do instrutor, dashboard, checklist, trial e validação.
- `resources/` e `databricks.yml`: Databricks Asset Bundle.

## Execução recomendada

1. Leia `docs/TECHNICAL_VALIDATION.md` e `docs/PREWORKSHOP_CHECKLIST.md`.
2. Autentique o profile: `databricks auth login --profile vibe-coding`.
3. Valide: `databricks bundle validate -t dev --profile vibe-coding`.
4. Faça deploy: `databricks bundle deploy -t dev --profile vibe-coding`.
5. Execute o job `prepare_workshop` ou o notebook `00_setup.py`.
6. Execute `02_read_csvs.py` para validar caminhos, schemas e contagens dos CSVs.
7. Rode o pipeline `Telco - Qualidade de Rede`.
8. Execute DQX e SQL; prepare Dashboard, Genie e App conforme os guias.

Os CSVs ficam em:

```text
/Volumes/<catalog>/<schema>/raw_data/cell_tower_metrics/
/Volumes/<catalog>/<schema>/raw_data/support_tickets/
```

O notebook `02_read_csvs.py` usa `spark.read.format("csv")`; o Lakeflow usa
`spark.readStream.format("cloudFiles")` sobre os mesmos diretórios.

O catálogo padrão é `telco_workshop.red_calidad`. Em ambientes sem `CREATE CATALOG`,
use um catálogo compartilhado alterando a variável `catalog` do bundle e os widgets.

## Validação local

```bash
uv run --extra dev python scripts/generate_repo_data.py
uv run --extra dev python scripts/validate_local.py
uv run --extra app streamlit run apps/network-monitor/app.py
```

O roteiro completo está em `docs/INSTRUCTOR_GUIDE.md`.
