# Data Sources

## 1. Official trip data

- Página oficial: https://divvybikes.com/system-data
- Repositório público dos arquivos: https://divvy-tripdata.s3.amazonaws.com
- Licença de uso: https://divvybikes.com/data-license-agreement
- Data de acesso: 1 de abril de 2026

## Recorte utilizado

Foram baixados 12 arquivos mensais, cobrindo corridas iniciadas entre `2025-03-01` e `2026-02-28`:

- `202503-divvy-tripdata.zip`
- `202504-divvy-tripdata.zip`
- `202505-divvy-tripdata.zip`
- `202506-divvy-tripdata.zip`
- `202507-divvy-tripdata.zip`
- `202508-divvy-tripdata.zip`
- `202509-divvy-tripdata.zip`
- `202510-divvy-tripdata.zip`
- `202511-divvy-tripdata.zip`
- `202512-divvy-tripdata.zip`
- `202601-divvy-tripdata.zip`
- `202602-divvy-tripdata.zip`

## Credibility notes

- Os dados são oficiais e publicados pela Divvy para uso público.
- Cada viagem é anonimizada, então não existe informação pessoal identificável.
- A própria página da Divvy informa que viagens de staff e viagens abaixo de 60 segundos são removidas antes da publicação.
- A licença permite análise e uso em relatórios e estudos não comerciais.

## Limitações relevantes

- Não há dados demográficos nem histórico de compra por usuário.
- Não é possível ligar corridas a uma mesma pessoa para medir recorrência individual.
- Alguns registros têm estação inicial ou final ausente, o que limita análises baseadas em localização.
