# Cleaning Log

## Ferramenta usada

- Script principal: `scripts/analyze_cyclistic.py`
- Estratégia: leitura dos ZIPs em chunks com `pandas` para evitar carregar o ano inteiro na memória.

## Padronização e preparação

1. Leitura apenas das colunas necessárias:
   `ride_id`, `rideable_type`, `started_at`, `ended_at`, `start_station_name`, `end_station_name`, `member_casual`.
2. Conversão de `started_at` e `ended_at` para `datetime`.
3. Criação de variáveis derivadas:
   `ride_length_min`, `month`, `day_of_week`, `day_of_week_num`, `start_hour`, `is_weekend`, `is_commute_window`, `is_round_trip`.

## Regras de limpeza

1. Mantidos apenas registros com `member_casual` em `casual` ou `member`.
2. Mantidos apenas registros com `started_at` entre `2025-03-01 00:00:00` e `2026-03-01 00:00:00`.
3. Removidas corridas com duração menor ou igual a zero.
4. Removidas corridas com duração acima de 24 horas para reduzir distorções analíticas.
5. Registros com estação ausente foram preservados para análise temporal, mas excluídos do ranking de estações.

## Resumo da qualidade dos dados

- Linhas lidas: `5,601,662`
- Linhas válidas após limpeza: `5,595,842`
- Registros fora da janela: `36`
- Durações não positivas: `29`
- Durações acima de 24h: `5,755`
- Estação inicial ausente em linhas válidas: `1,192,506`
- Estação final ausente em linhas válidas: `1,248,788`

## Saídas geradas

- `data/processed/overall_summary.csv`
- `data/processed/rides_by_month.csv`
- `data/processed/rides_by_weekday.csv`
- `data/processed/rides_by_hour.csv`
- `data/processed/rides_by_bike_type.csv`
- `data/processed/top_start_stations.csv`
- `data/processed/data_quality_summary.csv`
- `data/processed/behavior_flags_summary.csv`
