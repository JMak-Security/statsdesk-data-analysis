"""Command-line entry point for fetching and analyzing the WDI snapshot."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from statsdesk import __version__
from statsdesk.analysis import analyze
from statsdesk.fetch import fetch_snapshot
from statsdesk.loader import load_observations, load_verified_metadata
from statsdesk.reporting import render_json, render_markdown, write_analysis_csv, write_text_atomic


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="statsdesk",
        description="Fetch a cited WDI snapshot or analyze it reproducibly offline.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser("fetch", help="download the fixed 2022 WDI indicators")
    fetch.add_argument("--output-dir", type=Path, default=Path("data"))

    analysis = commands.add_parser("analyze", help="analyze a local, digest-verified WDI snapshot")
    analysis.add_argument("--input", type=Path, default=Path("data/wdi_2022.csv"))
    analysis.add_argument("--metadata", type=Path, default=Path("data/dataset_metadata.json"))
    analysis.add_argument("--output-dir", type=Path, default=Path("output"))
    return parser


def _ensure_distinct(paths: Sequence[Path]) -> None:
    resolved: set[Path] = set()
    for path in paths:
        canonical = path.resolve(strict=False)
        if canonical in resolved:
            raise ValueError("input and output paths must be different")
        resolved.add(canonical)


def _run_fetch(args: argparse.Namespace) -> int:
    csv_path, metadata_path, count = fetch_snapshot(args.output_dir)
    print(f"Fetched {count} WDI country/economy records.")
    print(f"Snapshot: {csv_path}")
    print(f"Provenance: {metadata_path}")
    return 0


def _run_analysis(args: argparse.Namespace) -> int:
    output_dir: Path = args.output_dir
    output_paths = [
        output_dir / "report.json",
        output_dir / "report.md",
        output_dir / "analysis.csv",
    ]
    _ensure_distinct([args.input, args.metadata, *output_paths])

    observations = load_observations(args.input)
    metadata = load_verified_metadata(args.input, args.metadata)
    report = analyze(observations, metadata)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output_paths[0], render_json(report))
    write_text_atomic(output_paths[1], render_markdown(report))
    write_analysis_csv(output_paths[2], report, observations)
    counts = report["counts"]
    correlation = report["spearman_rank_correlation"]
    if not isinstance(counts, dict) or not isinstance(correlation, dict):
        raise ValueError("internal error: generated report has an invalid shape")
    print(
        f"Analyzed {counts['paired_observations']} paired country/economy observations; "
        f"Spearman rho={correlation['rho']}."
    )
    print(f"Reports: {output_paths[0]}, {output_paths[1]}, {output_paths[2]}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            return _run_fetch(args)
        if args.command == "analyze":
            return _run_analysis(args)
        parser.error(f"unknown command: {args.command}")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"statsdesk: error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
