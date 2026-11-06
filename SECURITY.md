# Security notes

StatsDesk processes a bounded local CSV/JSON snapshot. Analysis is offline; only the explicit
`statsdesk fetch` command contacts the World Bank API.

## Input boundaries

- API responses, snapshot files, record counts, page counts, and field sizes have explicit bounds.
- CSV columns, year, codes, numeric values, duplicate identifiers, and provenance digest are
  validated.
- API/network and malformed-input errors are shown to the caller; no sample or stale data is
  silently substituted.
- Report files are written with temporary files and atomic replacement.

## Limitations

This is not a privacy-preserving analytics service or a statistical inference package. It does not
perform causal identification, hypothesis testing, or policy evaluation. The source data is
country/economy-level public data; no personal records are included.

Report suspected vulnerabilities through the repository's GitHub security reporting process.
