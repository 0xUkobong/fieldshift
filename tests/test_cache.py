from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import pandas as pd

from rotation_explorer import cache


def test_cache_ttl_and_integrity_guard():
    orig_dir = cache.CACHE_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cache.CACHE_DIR = Path(tmp)
            lat, lon = 12.34, 56.78

            # 1. Fewer than 100 rows should be rejected by integrity guard
            short_idx = pd.date_range("2023-01-01", periods=10, freq="D")
            short_df = pd.DataFrame({"T2M": 20.0}, index=short_idx)
            cache.save_cached(lat, lon, short_df)
            assert cache.load_cached(lat, lon) is None

            # 2. >= 100 rows and fresh should load cleanly
            valid_idx = pd.date_range("2023-01-01", periods=120, freq="D")
            valid_df = pd.DataFrame({"T2M": 20.0}, index=valid_idx)
            saved_path = cache.save_cached(lat, lon, valid_df)
            assert cache.is_cached(lat, lon) is True
            loaded = cache.load_cached(lat, lon)
            assert loaded is not None
            assert len(loaded) == 120

            # 3. Stale file (> CACHE_TTL_DAYS) should be treated as cache miss
            stale_ts = time.time() - (cache.CACHE_TTL_DAYS + 2) * 86_400
            os.utime(saved_path, (stale_ts, stale_ts))
            assert cache.is_cached(lat, lon) is False
            assert cache.load_cached(lat, lon) is None
    finally:
        cache.CACHE_DIR = orig_dir
