"""Bounded access to the World Bank Indicators API and deterministic snapshot creation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from statsdesk.reporting import render_json, write_text_atomic

YEAR = 2022
PER_PAGE = 400
MAX_RECORDS = 500
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_PAGES = 3
INDICATORS = {
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "population": "SP.POP.TOTL",
}
BASE_URL = "https://api.worldbank.org/v2"
CATALOG_URL = (
    "https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators"
)
LICENSE_URL = "https://datacatalog.worldbank.org/public-licenses?fragment=cc"
API_DOCS_URL = "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392"
CSV_COLUMNS = (
    "code",
    "country",
    "region",
    "year",
    "gdp_per_capita_usd",
    "population",
)
_WORLD_BANK_CODE_PATTERN = re.compile(r"[A-Z]{2,3}\Z")


def _read_api_pages(
    path: str, *, year: int | None = None
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    page_metadata: list[dict[str, object]] = []
    page = 1
    total_pages = 1
    expected_pages: int | None = None
    expected_records: int | None = None
    while page <= total_pages:
        params = {"format": "json", "per_page": str(PER_PAGE), "page": str(page)}
        if year is not None:
            params["date"] = str(year)
        url = f"{BASE_URL}/{path}?{urlencode(params)}"
        # URL uses the fixed HTTPS World Bank host and fixed indicator paths above.
        request = Request(  # noqa: S310
            url, headers={"User-Agent": "StatsDesk/1.0 (WDI public-data analysis)"}
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError(f"World Bank API response exceeds {MAX_RESPONSE_BYTES} bytes")
        try:
            document = json.loads(payload, parse_float=Decimal)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("World Bank API returned invalid JSON") from exc
        if not isinstance(document, list) or len(document) != 2:
            raise ValueError("World Bank API response must contain metadata and records")
        metadata, raw_records = document
        if isinstance(raw_records, dict):
            country_values = raw_records.get("value")
            if isinstance(country_values, list):
                raw_records = country_values
        if not isinstance(metadata, dict) or not isinstance(raw_records, list):
            raise ValueError("World Bank API response has an invalid shape")

        try:
            returned_page = int(metadata["page"])
            total_pages = int(metadata["pages"])
            total_records = int(metadata["total"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("World Bank API response metadata is incomplete") from exc
        if returned_page != page or total_pages < 1 or total_pages > MAX_PAGES or total_records < 0:
            raise ValueError("World Bank API pagination metadata is invalid or exceeds limits")
        if expected_pages is None:
            expected_pages = total_pages
            expected_records = total_records
        elif total_pages != expected_pages or total_records != expected_records:
            raise ValueError("World Bank API pagination metadata changed between pages")
        if total_records > MAX_RECORDS or len(raw_records) > MAX_RECORDS:
            raise ValueError(f"World Bank API result exceeds the {MAX_RECORDS}-record limit")
        for item in raw_records:
            if not isinstance(item, dict):
                raise ValueError("World Bank API returned a non-object record")
            records.append(cast(dict[str, object], item))
        page_metadata.append(cast(dict[str, object], metadata))
        page += 1

    if len(records) > MAX_RECORDS:
        raise ValueError(f"World Bank API result exceeds the {MAX_RECORDS}-record limit")
    if expected_records is not None and len(records) != expected_records:
        raise ValueError("World Bank API record count does not match response metadata")
    return records, page_metadata


def _code(record: dict[str, object]) -> str:
    value = record.get("countryiso3code")
    if isinstance(value, str) and value:
        code = value
    else:
        country = record.get("country")
        country_code = country.get("id") if isinstance(country, dict) else None
        if not isinstance(country_code, str) or not country_code:
            raise ValueError("World Bank observation is missing its country code")
        code = country_code
    if _WORLD_BANK_CODE_PATTERN.fullmatch(code) is None:
        raise ValueError(f"World Bank observation has unsupported country code {code!r}")
    return code


def _indicator_values(
    records: list[dict[str, object]], indicator_code: str
) -> dict[str, Decimal | None]:
    values: dict[str, Decimal | None] = {}
    for record in records:
        if str(record.get("date")) != str(YEAR):
            raise ValueError(f"{indicator_code} response included a year other than {YEAR}")
        code = _code(record)
        if code in values:
            raise ValueError(f"{indicator_code} response contains duplicate code {code}")
        raw_value = record.get("value")
        if raw_value is None:
            values[code] = None
        elif isinstance(raw_value, (int, Decimal)) and not isinstance(raw_value, bool):
            values[code] = Decimal(str(raw_value))
        else:
            raise ValueError(f"{indicator_code} response has a non-numeric value for {code}")
    return values


def _country_metadata(records: list[dict[str, object]]) -> dict[str, tuple[str, str, str]]:
    result: dict[str, tuple[str, str, str]] = {}
    for record in records:
        code = record.get("id")
        name = record.get("name")
        iso2_code = record.get("iso2Code")
        region = record.get("region")
        region_name = region.get("value") if isinstance(region, dict) else None
        if (
            not isinstance(code, str)
            or _WORLD_BANK_CODE_PATTERN.fullmatch(code) is None
            or len(code) != 3
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(region_name, str)
            or not region_name.strip()
        ):
            raise ValueError("World Bank country metadata is missing code, name, or region")
        if code in result:
            raise ValueError(f"World Bank country metadata contains duplicate code {code}")
        country = (code, name, region_name.strip())
        result[code] = country
        if (
            isinstance(iso2_code, str)
            and len(iso2_code) == 2
            and iso2_code.isalpha()
            and iso2_code.upper() != "NA"
        ):
            alias = iso2_code.upper()
            if alias in result and result[alias] != country:
                raise ValueError(f"World Bank country metadata contains duplicate alias {alias}")
            result[alias] = country
    return result


def build_snapshot_rows(
    gdp_records: list[dict[str, object]],
    population_records: list[dict[str, object]],
    country_records: list[dict[str, object]],
) -> list[dict[str, str]]:
    gdp_values = _indicator_values(gdp_records, INDICATORS["gdp_per_capita_usd"])
    population_values = _indicator_values(population_records, INDICATORS["population"])
    countries = _country_metadata(country_records)
    codes = sorted(set(gdp_values) | set(population_values))
    rows: list[dict[str, str]] = []
    canonical_codes: set[str] = set()
    for code in codes:
        if code not in countries:
            raise ValueError(f"World Bank country metadata is missing observation code {code}")
        canonical_code, country, region = countries[code]
        if canonical_code in canonical_codes:
            raise ValueError(
                f"World Bank code aliases resolve to duplicate country {canonical_code}"
            )
        canonical_codes.add(canonical_code)
        gdp = gdp_values.get(code)
        population = population_values.get(code)
        rows.append(
            {
                "code": canonical_code,
                "country": country,
                "region": region,
                "year": str(YEAR),
                "gdp_per_capita_usd": "" if gdp is None else str(gdp),
                "population": "" if population is None else str(population),
            }
        )
    if not rows:
        raise ValueError("World Bank API returned no observations for the selected year")
    return rows


def _csv_text(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def fetch_snapshot(output_dir: Path) -> tuple[Path, Path, int]:
    gdp_records, gdp_metadata = _read_api_pages(
        f"country/all/indicator/{INDICATORS['gdp_per_capita_usd']}", year=YEAR
    )
    population_records, population_metadata = _read_api_pages(
        f"country/all/indicator/{INDICATORS['population']}", year=YEAR
    )
    country_records, country_page_metadata = _read_api_pages("country")
    all_indicator_records = [*gdp_records, *population_records]
    known_codes = set(_country_metadata(country_records))
    missing_country_codes = sorted(
        {_code(record) for record in all_indicator_records} - known_codes
    )
    extra_country_urls: list[str] = []
    for code in missing_country_codes:
        extra_records, extra_metadata = _read_api_pages(f"country/{code}")
        country_records.extend(extra_records)
        country_page_metadata.extend(extra_metadata)
        extra_country_urls.append(f"{BASE_URL}/country/{code}?format=json&per_page={PER_PAGE}")

    rows = build_snapshot_rows(gdp_records, population_records, country_records)
    csv_contents = _csv_text(rows)
    csv_path = output_dir / "wdi_2022.csv"
    metadata_path = output_dir / "dataset_metadata.json"
    digest = hashlib.sha256(csv_contents.encode("utf-8")).hexdigest()

    def last_updated(pages: list[dict[str, object]]) -> str | None:
        value = pages[0].get("lastupdated") if pages else None
        return value if isinstance(value, str) else None

    metadata: dict[str, object] = {
        "dataset": "World Development Indicators",
        "dataset_id": "0037712",
        "catalog_url": CATALOG_URL,
        "license": "Creative Commons Attribution 4.0",
        "license_url": LICENSE_URL,
        "attribution": "World Bank, World Development Indicators (CC BY 4.0)",
        "api_documentation_url": API_DOCS_URL,
        "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "year": YEAR,
        "indicators": INDICATORS,
        "api_last_updated": {
            "gdp_per_capita_usd": last_updated(gdp_metadata),
            "population": last_updated(population_metadata),
            "country_metadata": last_updated(country_page_metadata),
        },
        "snapshot_sha256": digest,
        "analysis_plan": "ANALYSIS_PLAN.md, version 1.0",
        "source_urls": [
            f"{BASE_URL}/country/all/indicator/{INDICATORS['gdp_per_capita_usd']}?date={YEAR}&format=json&per_page={PER_PAGE}",
            f"{BASE_URL}/country/all/indicator/{INDICATORS['population']}?date={YEAR}&format=json&per_page={PER_PAGE}",
            f"{BASE_URL}/country?format=json&per_page={PER_PAGE}",
            *extra_country_urls,
        ],
        "record_count": len(rows),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(csv_path, csv_contents)
    write_text_atomic(metadata_path, render_json(metadata))
    return csv_path, metadata_path, len(rows)
