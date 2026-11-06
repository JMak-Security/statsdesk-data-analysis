# ADR 0001: Use the open-licensed World Development Indicators source

- Status: Accepted
- Date: 2026-11-06

## Context

No dataset or detailed project prompt was supplied. The project needs a reproducible public source
with a documented reuse license and an accessible API.

## Decision

Use the World Bank World Development Indicators, with the 2022 GDP-per-capita and total-population
indicators defined in `ANALYSIS_PLAN.md`. Preserve source metadata and attribution. The Data Catalog
identifies the dataset license as Creative Commons Attribution 4.0.

## Consequences

- The source and its license can be cited and the small 2022 snapshot can be committed.
- GDP per capita is current US dollars; no purchasing-power or inflation adjustment is implied.
- Report conclusions remain descriptive and limited to the retrieved WDI data.
