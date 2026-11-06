# StatsDesk Data Analysis

## Status and scope

Design baseline for Project 7. The referenced `Qoder_Master_Prompt_9_Projects_Senior.md` is not
present in this workspace, so the project scope is conservatively inferred from its name and the
portfolio log. The analysis plan is committed separately before any observation values are
downloaded or inspected.

StatsDesk is a reproducible, offline-first Python analysis of an openly licensed, country-level
World Development Indicators (WDI) snapshot. The project will report descriptive distributions
and rank association; it will not claim causation, policy effects, or forecasts.

## Data source

- World Bank World Development Indicators, retrieved through the official Indicators API.
- Fixed year: 2022.
- Indicators: `NY.GDP.PCAP.CD` (GDP per capita, current US$) and `SP.POP.TOTL` (population, total).
- WDI Data Catalog metadata identifies the dataset license as Creative Commons Attribution 4.0.
- Source URLs, retrieval date, indicator definitions, attribution, and SHA-256 digest are retained
  with the snapshot.
- The checked-in data snapshot is aggregated country/economy data; no personal records are used.

## Pipeline

1. Fetch the two named indicators from the official API, with bounded timeouts and explicit API
   errors, or use the checked-in snapshot offline.
2. Validate schema, year, ISO3 identifiers, duplicates, types, and positive numeric values.
3. Use country metadata to exclude regional/income/world aggregates.
4. Build a pairwise-complete analysis set and report exclusions and missingness.
5. Compute predefined descriptive statistics and Spearman rank correlation with average ranks for
   ties.
6. Emit deterministic JSON and Markdown reports plus a clean analysis CSV.

## Reproducibility and boundaries

- Python 3.12; prefer the standard library unless a dependency is justified by the analysis.
- Analysis is deterministic for an identical source snapshot and options.
- No request is made at report-generation time; network access is limited to the explicit fetch
  command.
- Report source version and excluded-record counts so the analysis can be audited.
- Statistical outputs describe only the selected WDI snapshot and do not establish causal or
  individual-level relationships.

## Assumptions

- With no detailed project prompt or analyst-supplied dataset available, WDI is a conservative,
  open-licensed global source.
- A fixed year and predefined descriptive methods reduce post-hoc method changes.
- World Bank API country metadata is the authority for excluding aggregate groups.
