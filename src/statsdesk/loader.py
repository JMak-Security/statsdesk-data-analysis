"""Strict, bounded loading and provenance verification for the WDI snapshot."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from statsdesk.fetch import CSV_COLUMNS, YEAR
from statsdesk.models import Observation

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 500
_CODE_PATTERN = re.compile(r"[A-Z]{3}\Z")
_CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f]")


def _text(value: str | None, field: str, line: int, maximum: int) -> str:
    if value is None or not value.strip() or len(value) > maximum:
        raise ValueError(f"line {line}: {field} must contain 1 to {maximum} characters")
    cleaned = value.strip()
    if _CONTROL_PATTERN.search(cleaned) is not None:
        raise ValueError(f"line {line}: {field} contains unsupported control characters")
    return cleaned


def _decimal(value: str | None, field: str, line: int) -> Decimal | None:
    if value is None or value.strip() == "":
        return None
    if len(value) > 40:
        raise ValueError(f"line {line}: {field} exceeds the supported length")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"line {line}: {field} must be a decimal or empty") from exc


def load_observations(path: Path) -> list[Observation]:
    with path.open("rb") as input_file:
        encoded = input_file.read(MAX_FILE_BYTES + 1)
    if len(encoded) > MAX_FILE_BYTES:
        raise ValueError(f"CSV exceeds the {MAX_FILE_BYTES}-byte size limit")
    try:
        text = encoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be valid UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != list(CSV_COLUMNS):
        raise ValueError(f"CSV headers must match exactly: {', '.join(CSV_COLUMNS)}")

    observations: list[Observation] = []
    seen_codes: set[str] = set()
    for line, record in enumerate(reader, start=2):
        if line - 1 > MAX_ROWS:
            raise ValueError(f"CSV exceeds the {MAX_ROWS}-row limit")
        if None in record or any(value is None for value in record.values()):
            raise ValueError(f"line {line}: missing or extra CSV fields")
        code = _text(record["code"], "code", line, 3)
        if _CODE_PATTERN.fullmatch(code) is None:
            raise ValueError(f"line {line}: code must be three uppercase letters")
        if code in seen_codes:
            raise ValueError(f"line {line}: duplicate country code {code}")
        seen_codes.add(code)
        country = _text(record["country"], "country", line, 160)
        region = _text(record["region"], "region", line, 100)
        year_text = _text(record["year"], "year", line, 4)
        if year_text != str(YEAR):
            raise ValueError(f"line {line}: year must be {YEAR}")
        observations.append(
            Observation(
                code=code,
                country=country,
                region=region,
                year=YEAR,
                gdp_per_capita_usd=_decimal(
                    record["gdp_per_capita_usd"], "gdp_per_capita_usd", line
                ),
                population=_decimal(record["population"], "population", line),
            )
        )

    if not observations:
        raise ValueError("CSV contains no country/economy observations")
    return observations


def load_verified_metadata(csv_path: Path, metadata_path: Path) -> dict[str, object]:
    with metadata_path.open("rb") as metadata_file:
        metadata_bytes = metadata_file.read(MAX_FILE_BYTES + 1)
    if len(metadata_bytes) > MAX_FILE_BYTES:
        raise ValueError(f"metadata exceeds the {MAX_FILE_BYTES}-byte size limit")
    try:
        document = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("dataset metadata must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise ValueError("dataset metadata top level must be an object")
    expected = document.get("snapshot_sha256")
    if not isinstance(expected, str) or re.fullmatch(r"[a-f0-9]{64}", expected) is None:
        raise ValueError("dataset metadata is missing a valid snapshot SHA-256")
    with csv_path.open("rb") as csv_file:
        csv_bytes = csv_file.read(MAX_FILE_BYTES + 1)
    if len(csv_bytes) > MAX_FILE_BYTES:
        raise ValueError(f"CSV exceeds the {MAX_FILE_BYTES}-byte size limit")
    digest = hashlib.sha256(csv_bytes).hexdigest()
    if digest != expected:
        raise ValueError("snapshot SHA-256 does not match dataset metadata")
    return document
