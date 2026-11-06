"""Predefined descriptive statistics and Spearman rank association."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from decimal import Decimal

from statsdesk.models import Observation


def _valid_value(value: Decimal | None, *, population: bool) -> bool:
    if value is None or not value.is_finite() or value <= 0:
        return False
    return not population or value == value.to_integral_value()


def _average_ranks(values: Sequence[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        for index in range(start, end):
            ranks[ordered[index][0]] = average_rank
        start = end
    return ranks


def _spearman(observations: Sequence[Observation]) -> float | None:
    if len(observations) < 2:
        return None
    x = [float(item.gdp_per_capita_usd) for item in observations if item.gdp_per_capita_usd]
    y = [float(item.population) for item in observations if item.population]
    if len(x) != len(observations) or len(y) != len(observations):
        raise ValueError("Spearman calculation received missing values")
    rank_x = _average_ranks(x)
    rank_y = _average_ranks(y)
    mean_x = statistics.mean(rank_x)
    mean_y = statistics.mean(rank_y)
    numerator = sum(
        (left - mean_x) * (right - mean_y) for left, right in zip(rank_x, rank_y, strict=True)
    )
    sum_x = sum((value - mean_x) ** 2 for value in rank_x)
    sum_y = sum((value - mean_y) ** 2 for value in rank_y)
    denominator = math.sqrt(sum_x * sum_y)
    if denominator == 0:
        return None
    return numerator / denominator


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def _describe(values: Sequence[float]) -> dict[str, float | int | None]:
    if not values:
        raise ValueError("cannot describe an empty sample")
    return {
        "n": len(values),
        "mean": _rounded(statistics.mean(values)),
        "median": _rounded(statistics.median(values)),
        "sample_standard_deviation": (
            _rounded(statistics.stdev(values)) if len(values) > 1 else None
        ),
        "minimum": _rounded(min(values)),
        "p25_linear": _rounded(_quantile(values, 0.25)),
        "p75_linear": _rounded(_quantile(values, 0.75)),
        "maximum": _rounded(max(values)),
    }


def _record(observation: Observation) -> dict[str, object]:
    if observation.gdp_per_capita_usd is None or observation.population is None:
        raise ValueError("cannot serialize an incomplete observation")
    return {
        "code": observation.code,
        "country": observation.country,
        "year": observation.year,
        "gdp_per_capita_usd": _rounded(float(observation.gdp_per_capita_usd)),
        "population": int(observation.population),
    }


def analyze(observations: Sequence[Observation], metadata: dict[str, object]) -> dict[str, object]:
    aggregate_rows = [
        item for item in observations if item.region.strip().casefold() == "aggregates"
    ]
    country_rows = [item for item in observations if item.region.strip().casefold() != "aggregates"]
    missing_value_count = sum(item.gdp_per_capita_usd is None for item in country_rows) + sum(
        item.population is None for item in country_rows
    )
    incomplete_rows = [
        item for item in country_rows if item.gdp_per_capita_usd is None or item.population is None
    ]

    invalid_value_count = 0
    invalid_rows: list[Observation] = []
    valid_rows: list[Observation] = []
    for item in country_rows:
        gdp_valid = _valid_value(item.gdp_per_capita_usd, population=False)
        population_valid = _valid_value(item.population, population=True)
        invalid_value_count += int(item.gdp_per_capita_usd is not None and not gdp_valid)
        invalid_value_count += int(item.population is not None and not population_valid)
        if (item.gdp_per_capita_usd is not None and not gdp_valid) or (
            item.population is not None and not population_valid
        ):
            invalid_rows.append(item)
        if gdp_valid and population_valid:
            valid_rows.append(item)

    if len(valid_rows) < 2:
        raise ValueError("fewer than two valid paired country observations remain")
    gdp_values = [float(item.gdp_per_capita_usd) for item in valid_rows if item.gdp_per_capita_usd]
    population_values = [float(item.population) for item in valid_rows if item.population]
    if len(gdp_values) != len(valid_rows) or len(population_values) != len(valid_rows):
        raise ValueError("internal error: complete-case selection produced a missing value")

    largest_count = math.ceil(len(valid_rows) * 0.01)
    population_ordered = sorted(
        valid_rows, key=lambda item: (float(item.population or Decimal(0)), item.code)
    )
    sensitivity_rows = population_ordered[: len(valid_rows) - largest_count]
    highest = sorted(
        valid_rows, key=lambda item: (-float(item.gdp_per_capita_usd or Decimal(0)), item.code)
    )[:5]
    lowest = sorted(
        valid_rows, key=lambda item: (float(item.gdp_per_capita_usd or Decimal(0)), item.code)
    )[:5]

    return {
        "report_version": 1,
        "analysis_plan": "ANALYSIS_PLAN.md, version 1.0",
        "source": metadata,
        "counts": {
            "input_records": len(observations),
            "aggregate_records_excluded": len(aggregate_rows),
            "country_economy_records": len(country_rows),
            "missing_indicator_values": missing_value_count,
            "incomplete_records": len(incomplete_rows),
            "invalid_numeric_values": invalid_value_count,
            "invalid_records": len(invalid_rows),
            "paired_observations": len(valid_rows),
        },
        "descriptive_statistics": {
            "gdp_per_capita_usd_current": _describe(gdp_values),
            "population_total": _describe(population_values),
        },
        "spearman_rank_correlation": {
            "rho": _rounded(_spearman(valid_rows)),
            "n": len(valid_rows),
            "p_value": None,
        },
        "largest_population_sensitivity": {
            "removed_largest_population_records": largest_count,
            "remaining_n": len(sensitivity_rows),
            "spearman_rho": _rounded(_spearman(sensitivity_rows)),
            "interpretation": "Descriptive robustness check; not an inferential test.",
        },
        "highest_gdp_per_capita": [_record(item) for item in highest],
        "lowest_gdp_per_capita": [_record(item) for item in lowest],
        "limitations": [
            "Country/economy-level descriptive association does not establish causation.",
            "GDP per capita is in current US dollars, not purchasing-power-adjusted "
            "or inflation-adjusted.",
            "Missing values were not imputed; only valid paired observations were analyzed.",
        ],
    }
