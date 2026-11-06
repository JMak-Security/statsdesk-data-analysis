from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from statsdesk.fetch import (
    MAX_RECORDS,
    MAX_RESPONSE_BYTES,
    _indicator_values,
    _read_api_pages,
    build_snapshot_rows,
    fetch_snapshot,
)


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int) -> bytes:
        return self.payload[:size]


def test_builds_joined_rows_and_retains_aggregates_and_missing_values() -> None:
    gdp: list[dict[str, object]] = [
        {
            "countryiso3code": "AAA",
            "date": "2022",
            "value": Decimal("12.5"),
        },
        {"countryiso3code": "AGG", "date": "2022", "value": None},
    ]
    population: list[dict[str, object]] = [
        {"countryiso3code": "AAA", "date": "2022", "value": 100},
        {"countryiso3code": "AGG", "date": "2022", "value": 500},
    ]
    countries: list[dict[str, object]] = [
        {"id": "AAA", "name": "Alpha", "region": {"value": "Region"}},
        {"id": "AGG", "name": "All group", "region": {"value": "Aggregates"}},
    ]
    rows = build_snapshot_rows(gdp, population, countries)
    assert rows == [
        {
            "code": "AAA",
            "country": "Alpha",
            "region": "Region",
            "year": "2022",
            "gdp_per_capita_usd": "12.5",
            "population": "100",
        },
        {
            "code": "AGG",
            "country": "All group",
            "region": "Aggregates",
            "year": "2022",
            "gdp_per_capita_usd": "",
            "population": "500",
        },
    ]


def test_uses_country_metadata_iso2_alias_for_aggregate() -> None:
    gdp: list[dict[str, object]] = [
        {
            "countryiso3code": "",
            "country": {"id": "XD", "value": "High income"},
            "date": "2022",
            "value": Decimal("12.5"),
        }
    ]
    population: list[dict[str, object]] = [
        {
            "countryiso3code": "",
            "country": {"id": "XD", "value": "High income"},
            "date": "2022",
            "value": 100,
        }
    ]
    countries: list[dict[str, object]] = [
        {
            "id": "HIC",
            "iso2Code": "XD",
            "name": "High income",
            "region": {"value": "Aggregates"},
        }
    ]
    rows = build_snapshot_rows(gdp, population, countries)
    assert rows[0]["code"] == "HIC"
    assert rows[0]["region"] == "Aggregates"


def test_rejects_duplicate_observation_codes() -> None:
    duplicate = [
        {"countryiso3code": "AAA", "date": "2022", "value": 1},
        {"countryiso3code": "AAA", "date": "2022", "value": 2},
    ]
    with pytest.raises(ValueError, match="duplicate code AAA"):
        _indicator_values(duplicate, "TEST")


def test_reads_one_valid_api_page() -> None:
    payload = json.dumps(
        [
            {"page": 1, "pages": 1, "total": 1},
            [{"date": "2022", "value": 3, "countryiso3code": "AAA"}],
        ]
    ).encode()

    with patch("statsdesk.fetch.urlopen", return_value=_Response(payload)):
        records, pages = _read_api_pages("country/all/indicator/TEST", year=2022)
    assert len(records) == 1
    assert pages[0]["total"] == 1


def test_reads_country_api_value_wrapper() -> None:
    payload = json.dumps(
        [
            {"page": 1, "pages": 1, "total": 1},
            {
                "value": [
                    {
                        "id": "HIC",
                        "iso2Code": "XD",
                        "name": "High income",
                        "region": {"value": "Aggregates"},
                    }
                ],
                "Count": 1,
            },
        ]
    ).encode()
    with patch("statsdesk.fetch.urlopen", return_value=_Response(payload)):
        records, _ = _read_api_pages("country/XD")
    assert records[0]["id"] == "HIC"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"{", "invalid JSON"),
        (b"{}", "metadata and records"),
        (b"[{},[]]", "metadata is incomplete"),
        (b'[{"page":2,"pages":1,"total":0},[]]', "pagination metadata"),
        (b'[{"page":1,"pages":4,"total":4},[]]', "exceeds limits"),
        (b'[{"page":1,"pages":1,"total":1},["bad"]]', "non-object record"),
        (
            b'[{"page":1,"pages":1,"total":2},[{"date":"2022","value":3,"countryiso3code":"AAA"}]]',
            "record count does not match",
        ),
        (
            json.dumps([{"page": 1, "pages": 1, "total": MAX_RECORDS + 1}, []]).encode(),
            "record limit",
        ),
    ],
)
def test_rejects_bad_api_responses(payload: bytes, message: str) -> None:
    with (
        patch("statsdesk.fetch.urlopen", return_value=_Response(payload)),
        pytest.raises(ValueError, match=message),
    ):
        _read_api_pages("country/all/indicator/TEST", year=2022)


def test_rejects_oversized_api_response() -> None:
    payload = b"x" * (MAX_RESPONSE_BYTES + 1)
    with (
        patch("statsdesk.fetch.urlopen", return_value=_Response(payload)),
        pytest.raises(ValueError, match="exceeds"),
    ):
        _read_api_pages("country/all/indicator/TEST", year=2022)


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ([{"countryiso3code": "AAA", "date": "2021", "value": 1}], "year other than 2022"),
        ([{"date": "2022", "value": 1}], "missing its country code"),
        ([{"countryiso3code": "AAA", "date": "2022", "value": "bad"}], "non-numeric"),
        ([{"countryiso3code": "../", "date": "2022", "value": 1}], "unsupported country code"),
    ],
)
def test_rejects_invalid_indicator_records(records: list[dict[str, object]], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _indicator_values(records, "TEST")


def test_rejects_missing_country_metadata() -> None:
    with pytest.raises(ValueError, match="missing observation code"):
        build_snapshot_rows(
            [{"countryiso3code": "AAA", "date": "2022", "value": 1}],
            [{"countryiso3code": "AAA", "date": "2022", "value": 2}],
            [],
        )


def test_rejects_country_metadata_without_region() -> None:
    with pytest.raises(ValueError, match="missing code, name, or region"):
        build_snapshot_rows(
            [{"countryiso3code": "AAA", "date": "2022", "value": 1}],
            [{"countryiso3code": "AAA", "date": "2022", "value": 2}],
            [{"id": "AAA", "name": "Alpha"}],
        )


def test_fetch_snapshot_writes_hash_and_provenance(tmp_path: Path) -> None:
    gdp_records = [{"countryiso3code": "AAA", "date": "2022", "value": Decimal("10")}]
    population_records = [{"countryiso3code": "AAA", "date": "2022", "value": 100}]
    country_records = [{"id": "AAA", "name": "Alpha", "region": {"value": "Region"}}]
    with patch(
        "statsdesk.fetch._read_api_pages",
        side_effect=[
            (gdp_records, [{"lastupdated": "2026-10-08"}]),
            (population_records, [{"lastupdated": "2026-10-08"}]),
            (country_records, [{"lastupdated": "2026-10-08"}]),
        ],
    ):
        csv_path, metadata_path, count = fetch_snapshot(tmp_path)
    assert count == 1
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["snapshot_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert metadata["api_last_updated"]["gdp_per_capita_usd"] == "2026-10-08"
