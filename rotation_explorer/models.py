"""Typed domain objects shared across data, scoring, and UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Farm:
    name: str
    lat: float
    lon: float
    region: str
    soil_note: str
    typical_crop: str
    local_tip: str = ""
    agrozone: str = ""


@dataclass(frozen=True)
class FarmSetup:
    farm: Farm
    crop: str
    priorities: tuple[str, ...]
    farmer_name: str = ""
    local_tip: str = ""
    language: str = "en"
    observed_yield_t_ha: float | None = None


@dataclass(frozen=True)
class ClimateSummary:
    avg_t2m: float
    avg_tmax: float
    avg_tmin: float
    annual_precip_mm: float
    precip_trend_pct: float
    heat_days_per_year: float
    frost_days_per_year: float
    n_years: int
    start_year: int
    end_year: int


@dataclass(frozen=True)
class RotationResult:
    name: str
    tagline: str
    score: float
    water: int
    soil: int
    priority: int
    why: str
    benefits: tuple[str, ...]
    risks: tuple[str, ...]
    sequence: str
