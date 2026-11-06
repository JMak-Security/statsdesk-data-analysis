# StatsDesk WDI descriptive analysis

- Dataset: World Development Indicators
- Year: 2022
- Snapshot SHA-256: `f565721805e75bd3cd86ab65d59bae05c372a968875478276be3225b3a0b7ddb`
- Valid paired country/economy observations: 209

## Data accounting

| Measure | Count |
| --- | ---: |
| Input records | 266 |
| Aggregate records excluded | 49 |
| Incomplete records | 8 |
| Invalid records | 0 |

## Descriptive statistics

| Indicator | n | Mean | Median | Sample SD | Min | P25 | P75 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GDP per capita (current US$) | 209 | 21200.873571 | 7655.59421 | 31131.453884 | 301.832256 | 2899.160475 | 28360.304147 | 226052.060665 |
| Population total | 209 | 37680463.923445 | 6664449.0 | 144111856.708269 | 9992.0 | 834188.0 | 26018721.0 | 1425423212.0 |

## Rank association

Spearman rho: **-0.340391** (n=209).
No p-value is reported; this is descriptive and does not establish causation.

Sensitivity after removing the largest-population observations: rho=-0.357264 (n=206, removed=3).

## Highest GDP per capita

| Code | Economy | Current US$ per capita | Population |
| --- | --- | ---: | ---: |
| MCO | Monaco | 226052.060665 | 38931 |
| LIE | Liechtenstein | 188055.003235 | 39493 |
| LUX | Luxembourg | 123719.658916 | 653103 |
| BMU | Bermuda | 119969.173269 | 64749 |
| NOR | Norway | 113122.130766 | 5457127 |

## Lowest GDP per capita

| Code | Economy | Current US$ per capita | Population |
| --- | --- | ---: | ---: |
| BDI | Burundi | 301.832256 | 13321097 |
| AFG | Afghanistan | 357.261153 | 40578842 |
| CAF | Central African Republic | 467.359825 | 5098039 |
| MDG | Madagascar | 504.059107 | 30437261 |
| SOM | Somalia, Fed. Rep. | 573.141166 | 17801897 |

## Interpretation limits

- Country/economy-level descriptive association is not causal evidence.
- GDP per capita is current US dollars, not purchasing-power-adjusted or inflation-adjusted.
- Missing values are not imputed; only valid paired observations are analyzed.
