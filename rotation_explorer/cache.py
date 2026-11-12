"""Disk cache so demo (and visited) points work after the first NASA POWER fetch."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from rotation_explorer.config import CACHE_DIR

# Re-fetch cached files older than this many days (stale data guard)
CACHE_TTL_DAYS = 30
# Minimum rows to consider a cached file valid (integrity check)
_MIN_ROWS = 100


def _path(lat: float, lon: float) -> Path:
    return CACHE_DIR / f"{lat:.2f}_{lon:.2f}.csv"


def _age_days(path: Path) -> float:
    """Return age of a file in days based on its last-modified time."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime).total_seconds() / 86_400


def is_cached(lat: float, lon: float) -> bool:
    """Return True only if a valid, non-stale cache file exists."""
    p = _path(lat, lon)
    if not p.exists():
        return False
    return _age_days(p) < CACHE_TTL_DAYS


def load_cached(lat: float, lon: float) -> pd.DataFrame | None:
    """Load cached daily DataFrame, or None if missing, stale, or corrupt."""
    path = _path(lat, lon)
    if not path.exists():
        return None
    if _age_days(path) >= CACHE_TTL_DAYS:
        return None  # Let caller re-fetch fresh data
    try:
        df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    except Exception:
        return None  # Corrupt file — treat as cache miss
    if len(df) < _MIN_ROWS:
        return None  # Truncated / empty file
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
