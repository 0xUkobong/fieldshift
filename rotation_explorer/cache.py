"""Disk cache so demo (and visited) points work after the first NASA POWER fetch."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rotation_explorer.config import CACHE_DIR


def _path(lat: float, lon: float) -> Path:
    return CACHE_DIR / f"{lat:.2f}_{lon:.2f}.csv"


def is_cached(lat: float, lon: float) -> bool:
    return _path(lat, lon).exists()


def load_cached(lat: float, lon: float) -> pd.DataFrame | None:
    path = _path(lat, lon)
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return df.sort_index()


def save_cached(lat: float, lon: float, df: pd.DataFrame) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _path(lat, lon)
    out = df.copy()
    out.index.name = "date"
    out.to_csv(path)
    return path


def cached_points() -> list[str]:
    if not CACHE_DIR.exists():
        return []
    return sorted(path.stem for path in CACHE_DIR.glob("*.csv"))
