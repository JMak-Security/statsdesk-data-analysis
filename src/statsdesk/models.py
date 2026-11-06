"""Shared data models for the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Observation:
    code: str
    country: str
    region: str
    year: int
    gdp_per_capita_usd: Decimal | None
    population: Decimal | None
