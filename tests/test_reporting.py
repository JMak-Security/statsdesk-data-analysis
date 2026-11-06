from __future__ import annotations

from decimal import Decimal

from statsdesk.models import Observation
from statsdesk.reporting import render_analysis_csv, render_json, render_markdown


def test_json_rendering_is_stable_and_unicode_safe() -> None:
    assert render_json({"z": "世界", "a": 1}) == '{\n  "a": 1,\n  "z": "世界"\n}\n'


def test_analysis_csv_sorts_and_excludes_aggregate_rows() -> None:
    rows = [
        Observation("BBB", "Beta", "Region", 2022, Decimal("2.50"), Decimal("20")),
        Observation("AAA", "Alpha", "Region", 2022, Decimal("1"), Decimal("10")),
        Observation("AGG", "Aggregate", "Aggregates", 2022, Decimal("9"), Decimal("90")),
    ]
    text = render_analysis_csv(rows)
    assert text.splitlines() == [
        "code,country,year,gdp_per_capita_usd,population",
        "AAA,Alpha,2022,1,10",
        "BBB,Beta,2022,2.50,20",
    ]


def test_markdown_report_mentions_descriptive_limits() -> None:
    report: dict[str, object] = {
        "source": {"dataset": "WDI", "year": 2022, "snapshot_sha256": "abc"},
        "counts": {
            "paired_observations": 2,
            "input_records": 2,
            "aggregate_records_excluded": 0,
            "incomplete_records": 0,
            "invalid_records": 0,
        },
        "descriptive_statistics": {
            "gdp_per_capita_usd_current": {
                "n": 2,
                "mean": 2,
                "median": 2,
                "sample_standard_deviation": 1,
                "minimum": 1,
                "p25_linear": 1,
                "p75_linear": 2,
                "maximum": 3,
            },
            "population_total": {
                "n": 2,
                "mean": 20,
                "median": 20,
                "sample_standard_deviation": 10,
                "minimum": 10,
                "p25_linear": 10,
                "p75_linear": 20,
                "maximum": 30,
            },
        },
        "spearman_rank_correlation": {"rho": 1, "n": 2},
        "largest_population_sensitivity": {
            "spearman_rho": None,
            "remaining_n": 1,
            "removed_largest_population_records": 1,
        },
        "highest_gdp_per_capita": [],
        "lowest_gdp_per_capita": [],
    }
    text = render_markdown(report)
    assert "does not establish causation" in text
    assert "Snapshot SHA-256" in text
