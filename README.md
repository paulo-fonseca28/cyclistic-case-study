# Cyclistic Bike-Share Case Study

Este repositório contém a execução completa do estudo de caso `How does a bike-share navigate speedy success?`, do programa Google Data Analytics. O objetivo do projeto é responder à pergunta de negócio:

**Como membros anuais e usuários casuais usam as bicicletas da Cyclistic de forma diferente?**

A análise foi desenvolvida em Python com base nos dados públicos da Divvy e organizada para publicação no GitHub com todos os artefatos relevantes.

## Objetivo do projeto

O foco analítico é entender diferenças de comportamento entre `member` e `casual` para apoiar estratégias de marketing voltadas à conversão de usuários casuais em assinantes anuais.

O projeto cobre:

- definição da tarefa de negócio
- documentação das fontes de dados
- limpeza e preparação dos dados
- análise exploratória e agregada
- visualizações executivas
- recomendações finais

## Fontes de dados

- Enunciado do case study: `Case Study 1_ How does a bike-share navigate speedy success.pdf`
- Dados oficiais: https://divvybikes.com/system-data
- Arquivos mensais utilizados: março de 2025 a fevereiro de 2026
- Licença: https://divvybikes.com/data-license-agreement

## Estrutura do repositório

- `data/processed/`: tabelas agregadas geradas pelo pipeline
- `figures/`: visualizações finais
- `docs/`: brief do case study, fontes, log de limpeza e extração textual do PDF
- `reports/`: relatório final e texto curto para portfólio
- `scripts/`: scripts reproduzíveis de download, análise e geração do PDF final
- `Deliverables.pdf`: arquivo consolidado com todos os entregáveis pedidos pelo case study
- `revisao.md`: revisão de conformidade do projeto com base no PDF

## Ambiente e dependências

O projeto foi executado com Python 3.12 em ambiente virtual local.

Instalação das dependências:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Como reproduzir

1. Baixar os dados brutos:

```bash
./.venv/bin/python scripts/download_divvy_data.py
```

2. Rodar a análise e regenerar os artefatos:

```bash
./.venv/bin/python scripts/analyze_cyclistic.py
```

3. Gerar o PDF consolidado com os deliverables:

```bash
./.venv/bin/python scripts/generate_deliverables_pdf.py
```

## Principais saídas

### Relatório

- `Deliverables.pdf`

### Dados tratados

- `data/processed/overall_summary.csv`
- `data/processed/rides_by_month.csv`
- `data/processed/rides_by_weekday.csv`
- `data/processed/rides_by_hour.csv`
- `data/processed/rides_by_bike_type.csv`
- `data/processed/top_start_stations.csv`
- `data/processed/data_quality_summary.csv`
- `data/processed/behavior_flags_summary.csv`

### Visualizações

- `figures/monthly_ride_volume.png`
- `figures/usage_heatmap.png`
- `figures/top_stations_comparison.png`
- `figures/rides_by_weekday.png`
- `figures/avg_ride_length_by_weekday.png`
- `figures/rides_by_hour.png`
- `figures/bike_type_mix.png`

## Resumo dos achados

- Membros representaram `64,1%` das viagens analisadas.
- Usuários casuais tiveram duração média de viagem maior que membros.
- Casuais concentram mais uso em verão, fins de semana e pontos de lazer.
- Membros mostram padrão mais forte de deslocamento recorrente em dias úteis e horários de commute.
- As diferenças mais relevantes entre os grupos estão em contexto de uso, sazonalidade, horário e localização, não no tipo de bicicleta.

