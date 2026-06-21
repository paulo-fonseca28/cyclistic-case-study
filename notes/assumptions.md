# Assumptions

## Analysis Window

The project uses 12 full monthly files available in this repository: March 2025 through February 2026. The cleaning script keeps trips started on or after `2025-03-01` and before `2026-03-01`.

## Rider Types

The public data labels rider type as `casual` or `member`. This project treats `member` as the annual-member segment and `casual` as the non-member segment.

## Trip Duration

Trip duration is calculated as `ended_at - started_at` in minutes. Trips with nonpositive duration or duration above 24 hours are removed because they are not useful for comparing typical customer behavior.

## Station Fields

Station names are not required for a trip to be valid. Missing stations are common enough that dropping those rows would distort time-based analysis. Station rankings use only trips with nonblank start station names.

## Commute Window

The commute-window flag is a practical analytical proxy, not a confirmed trip purpose. It includes weekday rides that start from 7:00-9:59 or 16:00-18:59.

## Weekend Use

Weekend use is defined as Saturday and Sunday rides. This supports interpretation of leisure-oriented patterns, but the data does not directly record trip purpose.

## Recommendations

Recommendations are based on observed trip patterns. They should be validated with customer-level, campaign, pricing, or survey data before major marketing investment.
