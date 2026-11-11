"""Climate indicators derived from daily NASA POWER series."""

from __future__ import annotations

import pandas as pd

from rotation_explorer.config import HEAT_STRESS_C
from rotation_explorer.models import ClimateSummary


def summarize_climate(df: pd.DataFrame) -> ClimateSummary:
    """Turn daily POWER series into farmer-facing climate indicators."""
    work = df.copy()
    work["year"] = work.index.year
    work["precip"] = work["PRECTOTCORR"].clip(lower=0)

    annual = work.groupby("year").agg(
        precip=("precip", "sum"),
        tmax=("T2M_MAX", "mean"),
        t2m=("T2M", "mean"),
        tmin=("T2M_MIN", "mean"),
        heat_days=("T2M_MAX", lambda s: (s > HEAT_STRESS_C).sum()),
        frost_days=("T2M_MIN", lambda s: (s < 0).sum()),
    )
    annual = annual.dropna()
    years = annual.index.astype(int)
    n_years = max(len(annual), 1)

    k = max(n_years // 3, 1)
    early = float(annual["precip"].iloc[:k].mean())
    late = float(annual["precip"].iloc[-k:].mean())
    precip_trend_pct = ((late - early) / early * 100.0) if early > 1 else 0.0

    return ClimateSummary(
        avg_t2m=float(annual["t2m"].mean()),
        avg_tmax=float(annual["tmax"].mean()),
        avg_tmin=float(annual["tmin"].mean()),
        annual_precip_mm=float(annual["precip"].mean()),
        precip_trend_pct=precip_trend_pct,
        heat_days_per_year=float(annual["heat_days"].mean()),
        frost_days_per_year=float(annual["frost_days"].mean()),
        n_years=n_years,
        start_year=int(years.min()),
        end_year=int(years.max()),
    )


def describe_heat(heat_days_per_year: float) -> str:
    if heat_days_per_year >= 80:
        return "very hot days are common"
    if heat_days_per_year >= 30:
        return "hot days show up most years"
    if heat_days_per_year >= 10:
        return "very hot days are occasional"
    return "very hot days are uncommon"


def describe_rain_trend(precip_trend_pct: float) -> str:
    if precip_trend_pct <= -10:
        return "later years have been clearly drier"
    if precip_trend_pct <= -5:
        return "rainfall has trended a little drier"
    if precip_trend_pct >= 10:
        return "later years have been clearly wetter"
    if precip_trend_pct >= 5:
        return "rainfall has trended a little wetter"
    return "rainfall has stayed fairly steady"


def describe_frost(frost_days_per_year: float) -> str:
    if frost_days_per_year >= 60:
        return "frost is a regular winter risk"
    if frost_days_per_year >= 15:
        return "frost occurs in a typical year"
    if frost_days_per_year >= 1:
        return "frost is possible but not frequent"
    return "frost is rare"


def climate_story(climate: ClimateSummary) -> str:
    """One farmer-facing paragraph from the POWER summary."""
    heat = describe_heat(climate.heat_days_per_year)
    rain = describe_rain_trend(climate.precip_trend_pct)
    frost = describe_frost(climate.frost_days_per_year)
    return (
        f"In a typical year this field sees about {climate.annual_precip_mm:.0f} mm of rain "
        f"and a mean daily high of {climate.avg_tmax:.1f} °C. "
        f"The record says {heat}, {rain}, and {frost}."
    )


def monthly_climate(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly temperature means and rainfall totals for charts."""
    monthly = df.resample("ME").agg(
        T2M_MAX=("T2M_MAX", "mean"),
        T2M=("T2M", "mean"),
        PRECTOTCORR=("PRECTOTCORR", "sum"),
    )
    return monthly.dropna(how="all")
