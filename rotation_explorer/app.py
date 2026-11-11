"""Streamlit orchestration: wire inputs → NASA POWER → scoring → UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from rotation_explorer.cache import is_cached, load_cached, save_cached
from rotation_explorer.climate import monthly_climate, summarize_climate
from rotation_explorer.config import POWER_CACHE_TTL_S
from rotation_explorer.insights import (
    climate_risk_flags,
    seasonal_guidance,
)
from rotation_explorer.power import PowerAPIError, fetch_power_payload, power_to_dataframe
from rotation_explorer.scoring import score_rotations
from rotation_explorer.ui import (
    inject_css,
    render_charts,
    render_climate_snapshot,
    render_extension_roster,
    render_farm_chip,
    render_header,
    render_method_and_glossary,
    render_recommendation,
    render_risk_and_timing,
    render_rotation_dashboard,
    render_share_kit,
    render_sidebar,
)


@st.cache_data(show_spinner=False, ttl=POWER_CACHE_TTL_S)
def cached_power_payload(lat: float, lon: float) -> dict[str, Any]:
    return fetch_power_payload(lat, lon)


def load_daily_climate(lat: float, lon: float, prefer_cache: bool):
    if prefer_cache:
        disk = load_cached(lat, lon)
        if disk is not None:
            st.session_state["climate_source"] = "offline pack"
            return disk
    try:
        with st.spinner("Loading weather for this field…"):
            payload = cached_power_payload(lat, lon)
        daily = power_to_dataframe(payload)
        if daily.empty:
            raise PowerAPIError("NASA POWER returned no usable values for this point.")
        save_cached(lat, lon, daily)
        st.session_state["climate_source"] = "NASA POWER (saved for offline)"
        return daily
    except PowerAPIError:
        disk = load_cached(lat, lon)
        if disk is None:
            raise
        st.session_state["climate_source"] = "offline pack (live fetch failed)"
        return disk


def main() -> None:
    st.set_page_config(
        page_title="Field Shift · Rotation Explorer",
        page_icon="F",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    render_header()
    setup, submitted = render_sidebar()
    if setup is None:
        st.stop()
    if submitted:
        st.toast(f"Comparison updated for {setup.farm.name}.")

    render_farm_chip(setup)
    prefer_cache = bool(st.session_state.get("low_bandwidth", False))

    if submitted or not st.session_state.get("climate_request_attempted", False):
        st.session_state["climate_request_attempted"] = True
        st.session_state["climate_daily"] = None
        try:
            st.session_state["climate_daily"] = load_daily_climate(
                setup.farm.lat,
                setup.farm.lon,
                prefer_cache=prefer_cache,
            )
            st.session_state["climate_data_error"] = None
        except PowerAPIError as exc:
            st.session_state["climate_data_error"] = str(exc)

    daily = st.session_state.get("climate_daily")
    if daily is None:
        st.error(
            "Weather for this field could not be loaded. Connect once to save an "
            "offline pack, or pick a demo site that is already cached."
        )
        if details := st.session_state.get("climate_data_error"):
            with st.expander("Technical details"):
                st.code(details)
        st.stop()

    source = st.session_state.get("climate_source", "NASA POWER")
    cached = is_cached(setup.farm.lat, setup.farm.lon)
    st.caption(
        f"Climate source: {source}. "
        + ("This point is saved for offline use." if cached else "Not yet saved for offline use.")
    )

    climate = summarize_climate(daily)
    monthly = monthly_climate(daily)
    rotations = score_rotations(
        climate, setup.crop, setup.priorities, region=setup.farm.region
    )
    flags = climate_risk_flags(climate)
    top = max(rotations, key=lambda item: item.score)
    timing = seasonal_guidance(monthly, setup.crop, top)

    render_recommendation(rotations, setup, timing)
    render_risk_and_timing(flags, timing, setup)
    render_climate_snapshot(climate)
    render_rotation_dashboard(rotations)
    render_share_kit(setup, climate, rotations, flags, timing)
    render_extension_roster(setup, top)
    render_charts(daily, monthly)
    render_method_and_glossary()
