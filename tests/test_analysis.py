from __future__ import annotations

from decimal import Decimal

import pytest

from statsdesk.analysis import _average_ranks, analyze
from statsdesk.models import Observation


def observation(
    code: str,
    gdp: str | None,
    population: str | None,
    *,
    region: str = "Americas",
) -> Observation:
    return Observation(
        code=code,
        country=f"Economy {code}",
        region=region,
        year=2022,
        gdp_per_capita_usd=None if gdp is None else Decimal(gdp),
        population=None if population is None else Decimal(population),
    )


def test_average_ranks_assigns_mean_rank_to_ties() -> None:
    assert _average_ranks([3.0, 1.0, 1.0, 5.0]) == [3.0, 1.5, 1.5, 4.0]


def test_analysis_reports_statistics_correlation_and_aggregate_exclusions() -> None:
    rows = [
        observation("AAA", "10", "100"),
        observation("BBB", "20", "400"),
        observation("CCC", "20", "200"),
        observation("DDD", "40", "800"),
        observation("EEE", None, "20"),
        observation("FFF", "0", "50"),
        observation("GGG", None, "0"),
        observation("AGG", "999", "9999", region="Aggregates"),
    ]
    report = analyze(rows, {"dataset": "test", "year": 2022})
    counts = report["counts"]
    assert isinstance(counts, dict)
    assert counts == {
        "input_records": 8,
        "aggregate_records_excluded": 1,
        "country_economy_records": 7,
        "missing_indicator_values": 2,
        "incomplete_records": 2,
        "invalid_numeric_values": 2,
        "invalid_records": 2,
        "paired_observations": 4,
    }
    statistics = report["descriptive_statistics"]
    assert isinstance(statistics, dict)
    gdp = statistics["gdp_per_capita_usd_current"]
    assert isinstance(gdp, dict)
    assert gdp["median"] == 20.0
    assert gdp["p25_linear"] == 17.5
    correlation = report["spearman_rank_correlation"]
    assert isinstance(correlation, dict)
    assert correlation["n"] == 4
    assert correlation["rho"] == pytest.approx(0.948683, abs=1e-6)
    assert correlation["p_value"] is None


def test_sensitivity_removes_ceil_one_percent_of_largest_population() -> None:
    rows = [
        observation("AAA", "10", "10"),
        observation("BBB", "20", "20"),
        observation("CCC", "30", "30"),
        observation("DDD", "40", "40"),
        observation("EEE", "50", "1000"),
    ]
    report = analyze(rows, {})
    sensitivity = report["largest_population_sensitivity"]
    assert isinstance(sensitivity, dict)
    assert sensitivity["removed_largest_population_records"] == 1
    assert sensitivity["remaining_n"] == 4


def test_constant_indicator_has_undefined_spearman() -> None:
    rows = [
        observation("AAA", "10", "10"),
        observation("BBB", "10", "20"),
    ]
    report = analyze(rows, {})
    correlation = report["spearman_rank_correlation"]
    assert isinstance(correlation, dict)
    assert correlation["rho"] is None


def test_requires_two_valid_paired_observations() -> None:
    with pytest.raises(ValueError, match="fewer than two"):
        analyze([observation("AAA", "10", "10")], {})
