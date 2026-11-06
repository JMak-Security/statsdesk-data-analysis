# Benchmark

## Descriptive analysis pipeline

- Command: `python scripts/bench_analysis.py --rows 100000 --runs 3`
- Dataset: 100,000 deterministic synthetic in-memory observations.
- Timed section: the full predefined `analyze` pipeline; synthetic data construction is outside the
  timed interval.
- Method: three runs; report median elapsed time and derived throughput.
- Result: median 1.775805 seconds; median throughput 56,312.50 rows/second.
- Environment: Windows 11 x64 (build 10.0.26300), Python 3.12.10, AMD Ryzen 7 5825U.

This is one local measurement of the current implementation, not a before/after optimization claim
or a service-level guarantee. Results vary with hardware and runtime.
