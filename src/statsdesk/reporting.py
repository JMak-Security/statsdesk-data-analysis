"""Stable rendering and atomic local output."""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast

from statsdesk.models import Observation


def render_json(document: object) -> str:
    return (
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def render_markdown(report: dict[str, object]) -> str:
    source = cast(dict[str, object], report["source"])
    counts = cast(dict[str, object], report["counts"])
    statistics = cast(dict[str, object], report["descriptive_statistics"])
    gdp = cast(dict[str, object], statistics["gdp_per_capita_usd_current"])
    population = cast(dict[str, object], statistics["population_total"])
    correlation = cast(dict[str, object], report["spearman_rank_correlation"])
    sensitivity = cast(dict[str, object], report["largest_population_sensitivity"])
    highest = cast(list[dict[str, object]], report["highest_gdp_per_capita"])
    lowest = cast(list[dict[str, object]], report["lowest_gdp_per_capita"])
    lines = [
        "# StatsDesk WDI descriptive analysis",
        "",
        f"- Dataset: {source.get('dataset', 'unknown')}",
        f"- Year: {source.get('year', 'unknown')}",
        f"- Snapshot SHA-256: `{source.get('snapshot_sha256', 'unknown')}`",
        f"- Valid paired country/economy observations: {counts['paired_observations']}",
        "",
        "## Data accounting",
        "",
        "| Measure | Count |",
        "| --- | ---: |",
        f"| Input records | {counts['input_records']} |",
        f"| Aggregate records excluded | {counts['aggregate_records_excluded']} |",
        f"| Incomplete records | {counts['incomplete_records']} |",
        f"| Invalid records | {counts['invalid_records']} |",
        "",
        "## Descriptive statistics",
        "",
        "| Indicator | n | Mean | Median | Sample SD | Min | P25 | P75 | Max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        _stat_row("GDP per capita (current US$)", gdp),
        _stat_row("Population total", population),
        "",
        "## Rank association",
        "",
        f"Spearman rho: **{correlation['rho']}** (n={correlation['n']}).",
        "No p-value is reported; this is descriptive and does not establish causation.",
        "",
        "Sensitivity after removing the largest-population observations: "
        f"rho={sensitivity['spearman_rho']} (n={sensitivity['remaining_n']}, "
        f"removed={sensitivity['removed_largest_population_records']}).",
        "",
        "## Highest GDP per capita",
        "",
        "| Code | Economy | Current US$ per capita | Population |",
        "| --- | --- | ---: | ---: |",
        *(_economy_row(item) for item in highest),
        "",
        "## Lowest GDP per capita",
        "",
        "| Code | Economy | Current US$ per capita | Population |",
        "| --- | --- | ---: | ---: |",
        *(_economy_row(item) for item in lowest),
        "",
        "## Interpretation limits",
        "",
        "- Country/economy-level descriptive association is not causal evidence.",
        "- GDP per capita is current US dollars, not purchasing-power-adjusted or "
        "inflation-adjusted.",
        "- Missing values are not imputed; only valid paired observations are analyzed.",
        "",
    ]
    return "\n".join(lines)


def _stat_row(label: str, values: dict[str, object]) -> str:
    fields = (
        "n",
        "mean",
        "median",
        "sample_standard_deviation",
        "minimum",
        "p25_linear",
        "p75_linear",
        "maximum",
    )
    cells = [str(values[field]) for field in fields]
    return f"| {label} | " + " | ".join(cells) + " |"


def _economy_row(item: dict[str, object]) -> str:
    country = str(item["country"]).replace("|", "\\|").replace("\n", " ")
    return f"| {item['code']} | {country} | {item['gdp_per_capita_usd']} | {item['population']} |"


def render_analysis_csv(observations: list[Observation]) -> str:
    buffer = io.StringIO(newline="")
    columns = ("code", "country", "year", "gdp_per_capita_usd", "population")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for item in sorted(observations, key=lambda row: row.code):
        if (
            item.region.strip().casefold() == "aggregates"
            or item.gdp_per_capita_usd is None
            or item.population is None
            or not item.gdp_per_capita_usd.is_finite()
            or not item.population.is_finite()
            or item.gdp_per_capita_usd <= 0
            or item.population <= 0
            or item.population != item.population.to_integral_value()
        ):
            continue
        writer.writerow(
            {
                "code": item.code,
                "country": item.country,
                "year": item.year,
                "gdp_per_capita_usd": item.gdp_per_capita_usd,
                "population": item.population,
            }
        )
    return buffer.getvalue()


def write_analysis_csv(
    path: Path, report: dict[str, object], observations: list[Observation]
) -> None:
    counts = cast(dict[str, object], report["counts"])
    content = render_analysis_csv(observations)
    actual_rows = max(0, content.count("\n") - 1)
    if actual_rows != counts["paired_observations"]:
        raise ValueError("analysis CSV row count does not match the report")
    write_text_atomic(path, content)


def write_text_atomic(path: Path, text: str) -> None:
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            temporary_path = temporary
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
