# ADR 0003: Keep reporting offline and deterministic

- Status: Accepted
- Date: 2026-11-06

## Context

An analysis should remain reproducible after the upstream API changes and should not require
network access to rerun.

## Decision

Provide an explicit bounded fetch command that stores a cited snapshot, and make validation,
analysis, and report generation operate on local files. Produce stable JSON, CSV, and Markdown
outputs with source provenance and a digest.

## Consequences

- Users can reproduce the analysis from a checked-in snapshot without API availability.
- Fetch and analysis errors remain distinct and visible.
- An updated upstream snapshot requires a new digest and an explicitly reviewed analysis rerun.
