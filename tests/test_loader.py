from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from statsdesk.loader import MAX_FILE_BYTES, load_observations, load_verified_metadata

HEADER = "code,country,region,year,gdp_per_capita_usd,population\n"


def _csv(*rows: str) -> str:
    return HEADER + "".join(f"{row}\n" for row in rows)


def test_loads_decimal_values_and_missing_values(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    path.write_text(
        _csv("AAA,Alpha,Region,2022,123.45,1000", "BBB,Beta,Region,2022,,2000"), encoding="utf-8"
    )
    observations = load_observations(path)
    assert observations[0].gdp_per_capita_usd is not None
    assert str(observations[0].gdp_per_capita_usd) == "123.45"
    assert observations[1].gdp_per_capita_usd is None


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("bad,header\n", "headers"),
        (_csv("AA,Alpha,Region,2022,1,2"), "three uppercase"),
        (_csv("AAA,Alpha,Region,2021,1,2"), "year must be 2022"),
        (_csv("AAA,Alpha,Region,2022,x,2"), "must be a decimal"),
        (_csv("AAA,Alpha,Region,2022,1,2", "AAA,Duplicate,Region,2022,3,4"), "duplicate"),
        (_csv("AAA,Alpha,Region,2022,1"), "missing or extra"),
    ],
)
def test_rejects_bad_csv_schema_or_records(tmp_path: Path, text: str, message: str) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_observations(path)


def test_rejects_oversized_csv(tmp_path: Path) -> None:
    path = tmp_path / "large.csv"
    path.write_bytes(b" " * (MAX_FILE_BYTES + 1))
    with pytest.raises(ValueError, match="size limit"):
        load_observations(path)


def test_verifies_snapshot_digest(tmp_path: Path) -> None:
    csv_path = tmp_path / "source.csv"
    csv_path.write_text(_csv("AAA,Alpha,Region,2022,1,2"), encoding="utf-8")
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"snapshot_sha256": digest}), encoding="utf-8")
    assert load_verified_metadata(csv_path, metadata)["snapshot_sha256"] == digest


def test_rejects_snapshot_digest_mismatch(tmp_path: Path) -> None:
    csv_path = tmp_path / "source.csv"
    csv_path.write_text(_csv("AAA,Alpha,Region,2022,1,2"), encoding="utf-8")
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"snapshot_sha256": "0" * 64}), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        load_verified_metadata(csv_path, metadata)
