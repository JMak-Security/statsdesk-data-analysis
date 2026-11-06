# StatsDesk Data Analysis

StatsDesk is an offline-first, reproducible descriptive analysis of a cited World Bank WDI
snapshot. The research question, indicators, exclusions, and statistics were committed in
[ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) before the complete observations were downloaded or examined.

The analysis is country/economy-level and descriptive. It does not establish causation, policy
effects, or forecasts.

## Install

Requires Python 3.12 or later.

```powershell
python -m pip install -e ".[dev]"
```

## Run offline

From the project directory, analyze the checked-in snapshot:

```powershell
statsdesk analyze
```

The command verifies the CSV SHA-256 against its metadata, then writes:

- `output\report.json` — versioned full report and source provenance.
- `output\report.md` — readable summary.
- `output\analysis.csv` — valid, pairwise-complete country/economy records.

## Refresh the snapshot

Network access is only used by this explicit command:

```powershell
statsdesk fetch --output-dir data
statsdesk analyze --input data\wdi_2022.csv --metadata data\dataset_metadata.json
```

Fetching targets only the two indicators and year specified in the pre-analysis plan. No API key
is required. API failures, malformed responses, duplicate codes, and pagination/size limits are
reported rather than silently substituted.

## Source and licensed dataset

- Dataset: World Bank, World Development Indicators, dataset ID `0037712`.
- Catalog metadata: https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators
- License stated in the catalog metadata: Creative Commons Attribution 4.0.
- License text: https://datacatalog.worldbank.org/public-licenses?fragment=cc
- API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- Attribution: World Bank, World Development Indicators (CC BY 4.0).

Indicators:

- `NY.GDP.PCAP.CD` — GDP per capita, current US dollars.
- `SP.POP.TOTL` — population, total.

The analysis uses 2022 and does not adjust GDP per capita for inflation or purchasing power.
`data\dataset_metadata.json` records retrieval time, source update metadata, indicator URLs, the
license, and a SHA-256 digest of the snapshot.

## Checked-in snapshot results

For the committed snapshot retrieved on 2026-11-06, 49 of 266 input records were World Bank
aggregates; 8 additional country/economy records had at least one missing indicator. The
pairwise-complete analysis contains 209 observations. Spearman rho is -0.340391; after removing
the three largest-population observations it is -0.357264 (n=206). These are descriptive
country/economy-level associations only; no p-value or causal interpretation is reported.

## Methods and limits

- Exclude World Bank records whose country metadata region is `Aggregates`.
- Use pairwise-complete observations with finite, positive values; do not impute missing data.
- Report mean, median, sample standard deviation, min, linearly interpolated P25/P75, and max.
- Compute Spearman rank correlation using average ranks for ties; report no p-value.
- Recompute the rank correlation after removing the largest `ceil(1% * n)` population records as
  a descriptive sensitivity check.
- Country/economy-level association is not a causal or individual-level conclusion.

See [DESIGN.md](DESIGN.md), [DATASET.md](DATASET.md), and
[docs/runbooks/reproducing-analysis.md](docs/runbooks/reproducing-analysis.md).

## Development

```powershell
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src tests scripts
python -m pytest --cov=statsdesk --cov-report=term-missing
python -m build
```
