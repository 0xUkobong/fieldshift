"""Climate indicators derived from daily NASA POWER series."""

from __future__ import annotations

import pandas as pd

from rotation_explorer.config import HEAT_STRESS_C
from rotation_explorer.models import ClimateSummary


def compute_daily_et0(df: pd.DataFrame) -> pd.Series:
    """Compute Hargreaves-Samani ET₀ proxy (mm/day), or NaN if solar radiation is missing."""
    if "ALLSKY_SFC_SW_DWN" not in df.columns:
        return pd.Series(float("nan"), index=df.index, dtype=float)
    td = (df["T2M_MAX"] - df["T2M_MIN"]).clip(lower=0)
    rs = df["ALLSKY_SFC_SW_DWN"].clip(lower=0)
    return (0.0023 * (df["T2M"] + 17.8) * td.pow(0.5) * rs * 0.408).clip(lower=0)


def summarize_climate(df: pd.DataFrame) -> ClimateSummary:
    """Turn daily POWER series into farmer-facing climate indicators."""
    work = df.copy()
    work["year"] = work.index.year
    work["precip"] = work["PRECTOTCORR"].clip(lower=0)

    has_solar = "ALLSKY_SFC_SW_DWN" in work.columns
    has_rh = "RH2M" in work.columns
    work["et0"] = compute_daily_et0(work)

    agg_dict: dict = dict(
        precip=("precip", "sum"),
        tmax=("T2M_MAX", "mean"),
        t2m=("T2M", "mean"),
        tmin=("T2M_MIN", "mean"),
        heat_days=("T2M_MAX", lambda s: (s > HEAT_STRESS_C).sum()),
        frost_days=("T2M_MIN", lambda s: (s < 0).sum()),
        et0=("et0", "mean"),
    )
    if has_rh:
        agg_dict["rh"] = ("RH2M", "mean")

    annual = work.groupby("year").agg(**agg_dict)
    annual = annual.dropna(subset=["precip", "tmax", "t2m", "tmin"])
    years = annual.index.astype(int)
    n_years = max(len(annual), 1)

    k = max(n_years // 3, 1)
    early = float(annual["precip"].iloc[:k].mean())
    late = float(annual["precip"].iloc[-k:].mean())
    precip_trend_pct = ((late - early) / early * 100.0) if early > 1 else 0.0

    avg_et0 = float(annual["et0"].mean()) if has_solar else 0.0
    avg_rh = float(annual["rh"].mean()) if has_rh else 0.0
    annual_precip = float(annual["precip"].mean())

    annual_water_balance = 0.0
    dry_months_per_year = 0.0
    if has_solar:
        monthly_wb = work[["precip", "et0"]].resample("ME").sum()
        if not monthly_wb.empty:
            annual_water_balance = annual_precip - (avg_et0 * 365.25)
            dry_months_total = int((monthly_wb["et0"] > monthly_wb["precip"]).sum())
            dry_months_per_year = dry_months_total / n_years

    return ClimateSummary(
        avg_t2m=float(annual["t2m"].mean()),
        avg_tmax=float(annual["tmax"].mean()),
        avg_tmin=float(annual["tmin"].mean()),
        annual_precip_mm=annual_precip,
        precip_trend_pct=precip_trend_pct,
        heat_days_per_year=float(annual["heat_days"].mean()),
        frost_days_per_year=float(annual["frost_days"].mean()),
        n_years=n_years,
        start_year=int(years.min()),
        end_year=int(years.max()),
        avg_et0_mm_day=avg_et0,
        avg_rh_pct=avg_rh,
        annual_water_balance_mm=annual_water_balance,
        dry_months_per_year=dry_months_per_year,
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
    """Monthly temperature means, rainfall totals, and optional ET₀ / water balance for charts."""
    work = df.copy()
    has_solar = "ALLSKY_SFC_SW_DWN" in work.columns
    if has_solar:
        work["ET0_MM"] = compute_daily_et0(work)
        monthly = work.resample("ME").agg(
            T2M_MAX=("T2M_MAX", "mean"),
            T2M=("T2M", "mean"),
            PRECTOTCORR=("PRECTOTCORR", "sum"),
            ET0_MM=("ET0_MM", "sum"),
        )
        monthly["WATER_BALANCE_MM"] = monthly["PRECTOTCORR"] - monthly["ET0_MM"]
    else:
        monthly = work.resample("ME").agg(
            T2M_MAX=("T2M_MAX", "mean"),
            T2M=("T2M", "mean"),
            PRECTOTCORR=("PRECTOTCORR", "sum"),
        )
    return monthly.dropna(how="all")
