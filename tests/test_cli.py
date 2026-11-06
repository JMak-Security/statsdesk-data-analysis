from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from statsdesk.cli import main


def _write_data(directory: Path) -> tuple[Path, Path]:
    data = directory / "wdi.csv"
    data.write_text(
        "code,country,region,year,gdp_per_capita_usd,population\n"
        "AAA,Alpha,Region,2022,10,100\n"
        "BBB,Beta,Region,2022,20,400\n",
        encoding="utf-8",
    )
    metadata = directory / "metadata.json"
    metadata.write_text(
        json.dumps({"snapshot_sha256": hashlib.sha256(data.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    return data, metadata


def test_analyze_cli_writes_all_outputs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data, metadata = _write_data(tmp_path)
    output = tmp_path / "output"
    assert (
        main(
            [
                "analyze",
                "--input",
                str(data),
                "--metadata",
                str(metadata),
                "--output-dir",
                str(output),
            ]
        )
        == 0
    )
    assert (output / "report.json").is_file()
    assert (output / "report.md").is_file()
    assert (output / "analysis.csv").is_file()
    assert "Analyzed 2 paired" in capsys.readouterr().out


def test_analyze_cli_rejects_digest_mismatch(tmp_path: Path) -> None:
    data, metadata = _write_data(tmp_path)
    data.write_text(data.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert (
        main(
            [
                "analyze",
                "--input",
                str(data),
                "--metadata",
                str(metadata),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        == 2
    )


def test_analyze_cli_rejects_output_collision(tmp_path: Path) -> None:
    data, metadata = _write_data(tmp_path)
    collision = tmp_path / "analysis.csv"
    data.replace(collision)
    metadata.write_text(
        json.dumps({"snapshot_sha256": hashlib.sha256(collision.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    assert (
        main(
            [
                "analyze",
                "--input",
                str(collision),
                "--metadata",
                str(metadata),
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 2
    )


def test_fetch_cli_reports_saved_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "wdi_2022.csv"
    metadata_path = tmp_path / "dataset_metadata.json"
    with patch(
        "statsdesk.cli.fetch_snapshot",
        return_value=(csv_path, metadata_path, 266),
    ):
        assert main(["fetch", "--output-dir", str(tmp_path)]) == 0
    assert "Fetched 266" in capsys.readouterr().out
