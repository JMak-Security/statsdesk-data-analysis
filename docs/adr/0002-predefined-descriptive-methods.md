# ADR 0002: Commit the analysis plan before data inspection

- Status: Accepted
- Date: 2026-11-06

## Context

Exploratory analysis can be biased by changing filters or metrics after viewing the observations.
The project also needs to avoid overstating country-level correlations.

## Decision

Commit `ANALYSIS_PLAN.md` before retrieving or inspecting observation values. Use its fixed year,
indicators, country-aggregate exclusions, complete-case rule, descriptive statistics, Spearman
method, and population sensitivity check.

## Consequences

- Analysis choices are auditable and less susceptible to post-hoc selection.
- Missing values are reported rather than imputed.
- Results do not support causal, inferential, or individual-level conclusions.
