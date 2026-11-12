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
    soil_type: str = "Loam"


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
    avg_et0_mm_day: float = 0.0   # Hargreaves-Samani ET₀ proxy (mm/day)
    avg_rh_pct: float = 0.0       # Mean relative humidity at 2 m (%)
    annual_water_balance_mm: float = 0.0  # Annual Rain − ET₀ (mm/yr)
    dry_months_per_year: float = 0.0      # Months/yr where ET₀ > Rain


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
