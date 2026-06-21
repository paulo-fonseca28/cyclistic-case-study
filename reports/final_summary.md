# Bike-Share Rider Behavior Final Summary

## Business Task

The marketing team needs to understand how annual members and casual riders use bike-share trips differently so it can design strategies that convert casual riders into annual members.

## Data Scope

- Source data: 12 monthly Divvy trip files from March 2025 through February 2026.
- Rows read: 5,601,662
- Valid rows after cleaning: 5,595,842
- Rows removed by cleaning rules: 5,820
- Analysis unit: individual bike trips, not individual customers.

## Key Findings

1. Members account for 64.1% of valid rides, while casual riders account for 35.9%.
2. Casual rides average 19.13 minutes, 59.3% longer than member rides at 12.01 minutes.
3. Casual riders are more weekend-oriented: 37.2% of casual rides occur on Saturday or Sunday, compared with 23.3% for members.
4. Members show a stronger commute pattern: their weekday commute-window share is 38.6%, 13.3 percentage points higher than casual riders.
5. Casual share peaks in 2025-06 at 43.0% of monthly rides, while casual ride volume peaks in 2025-08 with 337,246 rides.
6. Top casual start stations include DuSable Lake Shore Dr & Monroe St, Navy Pier, Streeter Dr & Grand Ave, suggesting that lakefront, park, and visitor-oriented locations are important contexts for casual use.

## Recommendations

1. Launch seasonal conversion campaigns during the summer casual-riding window.
   - Evidence: casual share peaks in 2025-06 and casual volume peaks in 2025-08.
   - Action: promote annual membership upgrades in app, email, and paid digital channels from May through September.
   - Expected impact: higher conversion efficiency by concentrating spend when casual riders are most active.
   - Caveat: the trip data does not identify repeat individual riders, so targeting should use available app or transaction data if available.

2. Focus location-based messaging around the highest casual start stations.
   - Evidence: casual station leaders are concentrated around recognizable lakefront and visitor destinations such as DuSable Lake Shore Dr & Monroe St, Navy Pier, Streeter Dr & Grand Ave.
   - Action: use geotargeted digital ads, station signage, and QR-based offers near these locations.
   - Expected impact: reach casual riders close to the moment of recreational use, when the membership value proposition is concrete.
   - Caveat: station data is missing for some valid rides, so station rankings should not be treated as a full location census.

3. Position membership around repeated weekend and leisure convenience, not only commuting.
   - Evidence: casual rides are longer and more weekend-heavy than member rides.
   - Action: test messages that frame membership as a lower-friction way to ride repeatedly on weekends, paired with pass-to-membership upgrade credits.
   - Expected impact: connects the annual plan to the behavior casual riders already demonstrate.
   - Caveat: price sensitivity and customer intent are not available in the public trip data and should be validated with campaign tests or surveys.

## Limitations

- The dataset is anonymized and cannot connect trips to a single rider over time.
- The data does not include demographics, income, pricing plan history, marketing exposure, or conversion outcomes.
- Missing station names limit location analysis, although time-based patterns remain usable.
- Recommendations are directional and should be tested before large campaign investment.
