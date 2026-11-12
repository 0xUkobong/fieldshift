"""Regional rainfall cells from NASA POWER's daily regional API."""

from __future__ import annotations

from datetime import datetime, timedelta
import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from rotation_explorer.config import POWER_FILL_VALUE, POWER_TIMEOUT_S

REGIONAL_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/regional"
REGIONAL_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "regional_weather_cache"
REGIONAL_CACHE_TTL_DAYS = 1
REGIONAL_CELL_DEGREES = 0.5


class RegionalWeatherError(Exception):
    """Raised when regional NASA POWER data cannot be fetched or read."""


def _cache_path(lat: float, lon: float, start_year: int, end_year: int, radius: float) -> Path:
    key = f"{lat:.3f}:{lon:.3f}:{start_year}:{end_year}:{radius:.1f}"
    digest = sha256(key.encode("utf-8")).hexdigest()[:20]
    return REGIONAL_CACHE_DIR / f"{digest}.csv"


def _load_disk_cache(path: Path, allow_stale: bool = False) -> pd.DataFrame | None:
    if not path.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if not allow_stale and age > timedelta(days=REGIONAL_CACHE_TTL_DAYS):
        return None
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
        return None
    return frame if not frame.empty else None


def _parse_regional_csv(body: str) -> pd.DataFrame:
    """Read POWER CSV while safely skipping its human-readable metadata header."""
    lines = body.lstrip("\ufeff").splitlines()
    header_row = None
    for index, line in enumerate(lines):
        try:
            columns = {part.strip().strip('"').upper() for part in next(csv.reader([line]))}
        except (csv.Error, StopIteration):
            continue
        if {"YEAR", "LON", "LAT", "PRECTOTCORR"}.issubset(columns):
            header_row = index
            break
    if header_row is None:
        raise RegionalWeatherError("NASA POWER returned a regional file without grid coordinates.")

    frame = pd.read_csv(StringIO("\n".join(lines[header_row:])))
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    required = {"YEAR", "LON", "LAT", "PRECTOTCORR"}
    if not required.issubset(frame.columns):
        raise RegionalWeatherError("NASA POWER's regional data did not include rainfall and grid coordinates.")
    if "DOY" not in frame.columns and "YYYYMMDD" not in frame.columns:
        raise RegionalWeatherError("NASA POWER's regional data did not include daily dates.")

    for column in ("YEAR", "DOY", "LON", "LAT", "PRECTOTCORR"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "YYYYMMDD" in frame.columns:
        date_text = frame["YYYYMMDD"].astype("Int64").astype("string")
        frame["DATE"] = pd.to_datetime(date_text, format="%Y%m%d", errors="coerce")
    else:
        frame["DATE"] = pd.to_datetime(frame["YEAR"].astype("Int64").astype(str), format="%Y") + pd.to_timedelta(frame["DOY"] - 1, unit="D")

    frame = frame.dropna(subset=["DATE", "LAT", "LON", "PRECTOTCORR"])
    frame = frame[frame["PRECTOTCORR"] != POWER_FILL_VALUE]
    if frame.empty:
        raise RegionalWeatherError("NASA POWER returned no usable rainfall cells for this area.")
    return frame[["DATE", "YEAR", "LAT", "LON", "PRECTOTCORR"]].reset_index(drop=True)


def fetch_regional_rainfall(
    lat: float,
    lon: float,
    start_year: int,
    end_year: int,
    radius_degrees: float = 1.0,
    *,
    prefer_cache: bool = False,
) -> pd.DataFrame:
    """Fetch daily rainfall for grid cells around a selected point, with a disk cache."""
    path = _cache_path(lat, lon, start_year, end_year, radius_degrees)
    cached = _load_disk_cache(path, allow_stale=prefer_cache)
    if cached is not None:
        return cached
    if prefer_cache:
        raise RegionalWeatherError(
            "No saved regional scan is available for this area yet. Turn off saved-climate mode to load it once."
        )

    params = {
        "parameters": "PRECTOTCORR",
        "community": "AG",
        "latitude-min": max(-89.5, lat - radius_degrees),
        "latitude-max": min(89.5, lat + radius_degrees),
        "longitude-min": max(-179.5, lon - radius_degrees),
        "longitude-max": min(179.5, lon + radius_degrees),
        "start": f"{start_year}0101",
        "end": f"{end_year}1231",
        "format": "CSV",
        "header": "true",
        "time-standard": "UTC",
        "user": "FieldShift",
    }
    try:
        response = requests.get(REGIONAL_DAILY_URL, params=params, timeout=POWER_TIMEOUT_S)
        response.raise_for_status()
    except requests.RequestException as exc:
        stale = _load_disk_cache(path, allow_stale=True)
        if stale is not None:
            return stale
        raise RegionalWeatherError("NASA POWER regional rainfall is unavailable right now.") from exc

    frame = _parse_regional_csv(response.text)
    REGIONAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


def rainfall_change_cells(
    daily: pd.DataFrame,
    start_year: int,
    end_year: int,
    minimum_cell_year_coverage: float = 0.9,
) -> tuple[pd.DataFrame, tuple[int, int], tuple[int, int]]:
    """Compare early and recent complete-year rainfall means for each grid cell."""
    frame = daily.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame["YEAR"] = frame["DATE"].dt.year
    frame["PRECTOTCORR"] = pd.to_numeric(frame["PRECTOTCORR"], errors="coerce")
    frame = frame[
        frame["DATE"].notna()
        & frame["PRECTOTCORR"].notna()
        & frame["YEAR"].between(start_year, end_year)
    ]
    if frame.empty:
        raise RegionalWeatherError("There is no regional rainfall record for the selected years.")

    frame["CELL_LAT"] = frame["LAT"].round(3)
    frame["CELL_LON"] = frame["LON"].round(3)
    yearly = (
        frame.groupby(["CELL_LAT", "CELL_LON", "YEAR"], as_index=False)
        .agg(rain_mm=("PRECTOTCORR", "sum"), valid_days=("DATE", "nunique"))
    )
    yearly["days_in_year"] = yearly["YEAR"].map(
        lambda year: 366 if pd.Timestamp(year=int(year), month=12, day=31).dayofyear == 366 else 365
    )
    yearly = yearly[yearly["valid_days"] >= yearly["days_in_year"] * minimum_cell_year_coverage]
    yearly["rain_mm"] = yearly["rain_mm"] * yearly["days_in_year"] / yearly["valid_days"]

    total_cells = yearly[["CELL_LAT", "CELL_LON"]].drop_duplicates().shape[0]
    minimum_cells = max(3, int(total_cells * 0.5))
    covered_cells = yearly.groupby("YEAR").size()
    years = sorted(int(year) for year, coverage in covered_cells.items() if coverage >= minimum_cells)
    if len(years) < 4:
        raise RegionalWeatherError("Choose a period with at least four complete years to compare rainfall change.")

    window_size = max(2, len(years) // 3)
    early_years = years[:window_size]
    recent_years = years[-window_size:]
    early = (
        yearly[yearly["YEAR"].isin(early_years)]
        .groupby(["CELL_LAT", "CELL_LON"], as_index=False)["rain_mm"]
        .mean()
        .rename(columns={"rain_mm": "earlier_rain_mm"})
    )
    recent = (
        yearly[yearly["YEAR"].isin(recent_years)]
        .groupby(["CELL_LAT", "CELL_LON"], as_index=False)["rain_mm"]
        .mean()
        .rename(columns={"rain_mm": "recent_rain_mm"})
    )
    cells = early.merge(recent, on=["CELL_LAT", "CELL_LON"], how="inner")
    cells["change_mm"] = cells["recent_rain_mm"] - cells["earlier_rain_mm"]
    cells["change_pct"] = cells.apply(
        lambda row: (row["change_mm"] / row["earlier_rain_mm"] * 100)
        if row["earlier_rain_mm"] >= 50
        else pd.NA,
        axis=1,
    )
    if cells.empty:
        raise RegionalWeatherError("NASA POWER did not return enough complete rainfall years for this map.")
    return cells, (early_years[0], early_years[-1]), (recent_years[0], recent_years[-1])
