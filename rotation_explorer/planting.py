"""Historical rainfall timing signals for planning a crop season."""

from __future__ import annotations

import calendar

import pandas as pd

from rotation_explorer.config import HEAT_STRESS_C


class PlantingDataError(Exception):
    """Raised when the selected climate period is too incomplete to summarize."""


MONTHS = {month: calendar.month_abbr[month] for month in range(1, 13)}


def _longest_dry_spell(rain: pd.Series) -> int:
    """Longest observed run below 1 mm/day; missing days break a run."""
    longest = current = 0
    for value in rain:
        if pd.isna(value):
            current = 0
        elif value < 1.0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _clean_daily(daily: pd.DataFrame) -> pd.DataFrame:
    if "PRECTOTCORR" not in daily.columns or not isinstance(daily.index, pd.DatetimeIndex):
        raise PlantingDataError("Daily rainfall is not available for this climate period.")
    frame = daily.sort_index().asfreq("D").copy()
    frame["rain"] = pd.to_numeric(frame["PRECTOTCORR"], errors="coerce")
    frame.loc[frame["rain"] < 0, "rain"] = pd.NA
    if "T2M_MAX" in frame.columns:
        frame["hot_days"] = pd.to_numeric(frame["T2M_MAX"], errors="coerce") > HEAT_STRESS_C
    else:
        frame["hot_days"] = False
    return frame


def monthly_rain_signals(daily: pd.DataFrame) -> pd.DataFrame:
    """Median monthly totals, wet-day frequency, and within-month dry spells."""
    frame = _clean_daily(daily)
    work = frame.assign(year=frame.index.year, month=frame.index.month, day=frame.index.day)
    records: list[dict] = []
    for (year, month), group in work.groupby(["year", "month"]):
        expected_days = calendar.monthrange(int(year), int(month))[1]
        valid = group["rain"].notna().sum()
        if valid < expected_days * 0.85:
            continue
        records.append(
            {
                "year": int(year),
                "month": int(month),
                "rain_mm": float(group["rain"].sum() * expected_days / valid),
                "wet_days": int((group["rain"] >= 1.0).sum()),
                "longest_dry_spell": _longest_dry_spell(group["rain"]),
                "hot_days": int(group["hot_days"].sum()),
            }
        )
    if not records:
        raise PlantingDataError("There are not enough complete daily records to show monthly rainfall patterns.")
    monthly = pd.DataFrame(records)
    summary = (
        monthly.groupby("month")
        .agg(
            rain_mm=("rain_mm", "median"),
            wet_days=("wet_days", "median"),
            dry_spell_days=("longest_dry_spell", "median"),
            hot_days=("hot_days", "median"),
            years=("year", "nunique"),
        )
        .reindex(range(1, 13))
    )
    summary.index.name = "month"
    summary["month_name"] = [MONTHS[month] for month in summary.index]
    return summary.reset_index()


def season_window_signals(daily: pd.DataFrame, duration_months: int) -> tuple[pd.DataFrame, int]:
    """Rank calendar windows by their lower-quartile historical rainfall."""
    if not 2 <= duration_months <= 6:
        raise ValueError("Season duration must be between two and six months.")
    frame = _clean_daily(daily)
    if frame.empty:
        raise PlantingDataError("There are no daily records in this climate period.")
    first_date = frame.index.min().normalize()
    last_date = frame.index.max().normalize()
    windows: list[dict] = []

    # Use complete year-to-year windows only, including seasons that cross New Year.
    for start_month in range(1, 13):
        samples: list[dict] = []
        for start_year in range(first_date.year, last_date.year + 1):
            start = pd.Timestamp(start_year, start_month, 1)
            end = start + pd.DateOffset(months=duration_months)
            last_day = end - pd.Timedelta(days=1)
            if start < first_date or last_day > last_date:
                continue
            segment = frame.loc[(frame.index >= start) & (frame.index < end)]
            expected_days = (end - start).days
            valid_rain = segment["rain"].notna().sum()
            if valid_rain < expected_days * 0.85:
                continue
            samples.append(
                {
                    "rain_mm": float(segment["rain"].sum() * expected_days / valid_rain),
                    "wet_days": int((segment["rain"] >= 1.0).sum()),
                    "longest_dry_spell": _longest_dry_spell(segment["rain"]),
                    "hot_days": int(segment["hot_days"].sum()),
                }
            )
        if len(samples) >= 3:
            sample_frame = pd.DataFrame(samples)
            windows.append(
                {
                    "start_month": start_month,
                    "end_month": ((start_month + duration_months - 2) % 12) + 1,
                    "rain_p25_mm": float(sample_frame["rain_mm"].quantile(0.25)),
                    "rain_median_mm": float(sample_frame["rain_mm"].median()),
                    "wet_days_median": float(sample_frame["wet_days"].median()),
                    "dry_spell_median_days": float(sample_frame["longest_dry_spell"].median()),
                    "dry_spell_p75_days": float(sample_frame["longest_dry_spell"].quantile(0.75)),
                    "hot_days_median": float(sample_frame["hot_days"].median()),
                    "years": len(samples),
                }
            )
    if not windows:
        raise PlantingDataError("At least three sufficiently complete season windows are needed for this duration.")
    ranked = pd.DataFrame(windows).sort_values(
        ["rain_p25_mm", "wet_days_median", "start_month"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return ranked, int(ranked["years"].max())
