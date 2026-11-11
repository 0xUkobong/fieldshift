"""NASA POWER daily point client. No Streamlit dependency."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from rotation_explorer.config import (
    POWER_COMMUNITY,
    POWER_END,
    POWER_FILL_VALUE,
    POWER_PARAMETERS,
    POWER_START,
    POWER_TIMEOUT_S,
    POWER_URL,
)


class PowerAPIError(Exception):
    """Raised when NASA POWER cannot be fetched or parsed."""


def fetch_power_payload(lat: float, lon: float) -> dict[str, Any]:
    """Fetch daily NASA POWER agroclimatology JSON for a point."""
    params = {
        "parameters": POWER_PARAMETERS,
        "community": POWER_COMMUNITY,
        "longitude": lon,
        "latitude": lat,
        "start": POWER_START,
        "end": POWER_END,
        "format": "JSON",
    }
    try:
        response = requests.get(POWER_URL, params=params, timeout=POWER_TIMEOUT_S)
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise PowerAPIError("NASA POWER timed out.") from exc
    except requests.RequestException as exc:
        raise PowerAPIError(f"Could not reach NASA POWER: {exc}") from exc
    except ValueError as exc:
        raise PowerAPIError("NASA POWER returned invalid JSON.") from exc

    if "properties" not in payload or "parameter" not in payload.get("properties", {}):
        raise PowerAPIError("Unexpected NASA POWER response shape.")
    return payload


def power_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Parse POWER JSON into a daily DataFrame, dropping fill values."""
    try:
        parameters = payload["properties"]["parameter"]
    except (KeyError, TypeError) as exc:
        raise PowerAPIError("Could not parse NASA POWER data.") from exc

    series = {
        name: pd.Series(values, dtype="float64") for name, values in parameters.items()
    }
    df = pd.DataFrame(series)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"
    df = df.replace(POWER_FILL_VALUE, pd.NA).dropna(how="all")
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_index()
