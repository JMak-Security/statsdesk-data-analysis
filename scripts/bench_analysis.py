"""Reproducible in-memory benchmark for the predefined analysis pipeline."""

from __future__ import annotations

import argparse
import statistics
import time
from decimal import Decimal

from statsdesk.analysis import analyze
from statsdesk.models import Observation


def build_synthetic(count: int) -> list[Observation]:
    return [
        Observation(
            code=f"SYN{index:06d}",
            country=f"Synthetic economy {index}",
            region="Synthetic region",
            year=2022,
            gdp_per_capita_usd=Decimal(500 + (index * 7919) % 100_000),
            population=Decimal(100_000 + (index * 104729) % 1_000_000_000),
        )
        for index in range(count)
    ]


def run_benchmark(count: int, runs: int) -> list[float]:
    observations = build_synthetic(count)
    metadata: dict[str, object] = {"dataset": "Synthetic benchmark data", "year": 2022}
    durations: list[float] = []
    for _ in range(runs):
        started = time.perf_counter()
        report = analyze(observations, metadata)
        durations.append(time.perf_counter() - started)
        report_counts = report["counts"]
        if not isinstance(report_counts, dict) or report_counts["paired_observations"] != count:
            raise RuntimeError("benchmark analysis unexpectedly excluded synthetic observations")
    return durations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.rows < 2 or args.runs < 1:
        parser.error("--rows must be at least 2 and --runs must be positive")

    durations = run_benchmark(args.rows, args.runs)
    median_seconds = statistics.median(durations)
    print(f"Rows: {args.rows:,}")
    print(f"Runs: {args.runs}")
    print(f"Median: {median_seconds:.6f} seconds")
    print(f"Median throughput: {args.rows / median_seconds:,.2f} rows/second")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
