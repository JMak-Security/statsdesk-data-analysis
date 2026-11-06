# Pre-analysis plan: country-level GDP per capita and population

**Plan version:** 1.0  
**Prepared:** 2026-11-06  
**Status:** Committed before fetching or inspecting observation values.

## Question

Among country/economy observations with valid values for both selected World Bank indicators in
2022, how are GDP per capita and population distributed, and what is their descriptive
rank-order association?

This is an exploratory descriptive analysis, not a causal or confirmatory study. No directional
hypothesis will be tested.

## Data and unit

- Source: World Bank World Development Indicators via the official V2 Indicators API.
- Year: 2022 only.
- Unit of analysis: one country/economy identified by ISO3 code.
- `NY.GDP.PCAP.CD`: GDP per capita in current US dollars; it is not purchasing-power-adjusted or
  inflation-adjusted.
- `SP.POP.TOTL`: total population.
- Dataset metadata identifies Creative Commons Attribution 4.0; retain World Bank attribution
  and the source/license links with redistributed data and reports.

## Inclusion and exclusion rules

1. Keep records for which World Bank country metadata identifies a country/economy, excluding
   entries whose region is `Aggregates`.
2. Require the exact requested year and a non-empty ISO3 identifier.
3. Require one observation for each indicator and ISO3; duplicates are errors, not silently
   averaged.
4. For the primary pairwise analysis, require both values to be present, numeric, finite, and
   greater than zero.
5. Preserve and report counts for aggregate records, missing indicator values, invalid values,
   and valid paired observations. Do not impute missing data.

## Predefined analysis

- For each of GDP per capita and population, report `n`, mean, median, sample standard deviation,
  minimum, 25th percentile, 75th percentile, and maximum.
- Percentiles use linear interpolation between adjacent sorted observations.
- Compute Spearman's rank correlation between GDP per capita and population using average ranks
  for ties. Report the coefficient and paired `n`; do not calculate or interpret a p-value.
- Sensitivity check: recompute Spearman's coefficient after removing the `ceil(1% * n)` largest
  population observations. Report the changed sample size and coefficient; treat it as a
  robustness description only.
- Report the five highest and five lowest GDP-per-capita observations with ISO3 code and country
  label. Ties are ordered by ISO3 code for stable output.

## Quality and interpretation

- Record data retrieval time, source URL, indicator codes, data license, and SHA-256 digest.
- Confirm each retained country has at most one value per indicator and that joined data use the
  same year and ISO3.
- A missing value is not evidence of zero or absence.
- Population and GDP per capita are highly skewed measures; medians, quantiles, and rank
  association are included to reduce dependence on means and scale.
- Any association is country-level and descriptive. Do not infer individual outcomes, causality,
  policy effectiveness, or future values.
- No alternative years, indicators, exclusions, or transformations will be added after observing
  the data without recording an amended plan and rationale.

## Schema amendment

After committing this plan and before retrieving a complete snapshot, an API schema check on
2026-11-06 established that indicator records expose `countryiso3code`, while country metadata
exposes the matching three-character `id` and `region.value`. The implementation will join those
fields and apply the already specified `region.value == "Aggregates"` exclusion. This clarifies
field mapping only; the year, indicators, inclusion rules, and statistics are unchanged.
