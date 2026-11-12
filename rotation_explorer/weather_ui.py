"""Regional weather map and saved-field comparison presentation."""

from __future__ import annotations

from html import escape

import folium
import pandas as pd
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium

from rotation_explorer.models import FarmSetup
from rotation_explorer.regional_weather import (
    RegionalWeatherError,
    fetch_regional_rainfall,
    rainfall_change_cells,
)
from rotation_explorer.store import list_fields

WEATHER_BLUE = "#397f9e"
WEATHER_NEUTRAL = "#f5f5f5"
WEATHER_DRY = "#ad5d4e"


def _cell_size(cells: pd.DataFrame) -> tuple[float, float]:
    latitudes = sorted(cells["CELL_LAT"].dropna().unique())
    longitudes = sorted(cells["CELL_LON"].dropna().unique())
    lat_steps = [b - a for a, b in zip(latitudes, latitudes[1:]) if b > a]
    lon_steps = [b - a for a, b in zip(longitudes, longitudes[1:]) if b > a]
    return (
        float(pd.Series(lat_steps).median()) if lat_steps else 0.5,
        float(pd.Series(lon_steps).median()) if lon_steps else 0.625,
    )


def _cell_color_map(values: pd.Series, metric: str) -> LinearColormap:
    if metric == "change_mm":
        limit = max(float(values.abs().max()), 1.0)
        return LinearColormap(
            [WEATHER_DRY, WEATHER_NEUTRAL, WEATHER_BLUE],
            index=[-limit, 0, limit],
            vmin=-limit,
            vmax=limit,
        )
    low = max(float(values.min()), 0.0)
    high = max(float(values.max()), low + 1.0)
    return LinearColormap([WEATHER_NEUTRAL, "#8ec7e2", WEATHER_BLUE], vmin=low, vmax=high)


def _rain_label(row: pd.Series) -> str:
    change = f"{row['change_mm']:+.0f} mm/year"
    if pd.notna(row["change_pct"]):
        change += f" ({row['change_pct']:+.0f}%)"
    return change


def _build_map(
    cells: pd.DataFrame,
    selected: FarmSetup,
    radius: float,
    metric: str,
    early_years: tuple[int, int],
    recent_years: tuple[int, int],
) -> tuple[folium.Map, tuple[float, float]]:
    lat_step, lon_step = _cell_size(cells)
    value_column = "change_mm" if metric == "change_mm" else "recent_rain_mm"
    color_map = _cell_color_map(cells[value_column], value_column)
    color_map.caption = (
        "Change in average annual rainfall (mm/year)"
        if metric == "change_mm"
        else f"Average annual rainfall, {recent_years[0]}–{recent_years[1]} (mm/year)"
    )

    fmap = folium.Map(
        location=[selected.farm.lat, selected.farm.lon],
        zoom_start=7 if radius <= 1 else 6,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    for row in cells.itertuples(index=False):
        value = float(getattr(row, value_column))
        earlier = float(row.earlier_rain_mm)
        recent = float(row.recent_rain_mm)
        pct = getattr(row, "change_pct")
        pct_label = f" · {float(pct):+.0f}%" if pd.notna(pct) else ""
        tooltip = (
            f"Annual rain: {recent:.0f} mm · change: {float(row.change_mm):+.0f} mm/year{pct_label}"
        )
        popup = (
            "<strong>Regional rainfall estimate</strong><br>"
            f"Recent ({recent_years[0]}–{recent_years[1]}): {recent:.0f} mm/year<br>"
            f"Earlier ({early_years[0]}–{early_years[1]}): {earlier:.0f} mm/year<br>"
            f"Change: {float(row.change_mm):+.0f} mm/year{pct_label}"
        )
        bounds = [
            [float(row.CELL_LAT) - lat_step / 2, float(row.CELL_LON) - lon_step / 2],
            [float(row.CELL_LAT) + lat_step / 2, float(row.CELL_LON) + lon_step / 2],
        ]
        folium.Rectangle(
            bounds=bounds,
            color="#ffffff",
            weight=1,
            fill=True,
            fill_color=color_map(value),
            fill_opacity=0.78,
            tooltip=tooltip,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(fmap)

    folium.CircleMarker(
        location=[selected.farm.lat, selected.farm.lon],
        radius=8,
        color="#1e1e1f",
        weight=2,
        fill=True,
        fill_color="#f7ca50",
        fill_opacity=1,
        tooltip=f"Selected field · {escape(selected.farm.name)}",
        popup=escape(selected.farm.name),
    ).add_to(fmap)

    min_lat, max_lat = cells["CELL_LAT"].min() - lat_step / 2, cells["CELL_LAT"].max() + lat_step / 2
    min_lon, max_lon = cells["CELL_LON"].min() - lon_step / 2, cells["CELL_LON"].max() + lon_step / 2
    fmap.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(10, 10))
    color_map.add_to(fmap)
    return fmap, (lat_step, lon_step)


def _field_cell_values(
    cells: pd.DataFrame,
    setup: FarmSetup,
    lat_step: float,
    lon_step: float,
) -> pd.DataFrame:
    saved_rows = list_fields()
    candidates: list[dict] = []
    seen: set[tuple[float, float]] = set()

    def add_field(name: str, crop: str, lat: float, lon: float, observed_yield: float | None) -> None:
        key = (round(float(lat), 3), round(float(lon), 3))
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            {"Field": name, "Crop": crop or "—", "lat": float(lat), "lon": float(lon), "Last harvest (t/ha)": observed_yield}
        )

    add_field(
        setup.farm.name,
        setup.crop,
        setup.farm.lat,
        setup.farm.lon,
        setup.observed_yield_t_ha,
    )
    for row in saved_rows:
        add_field(
            str(row["name"]),
            str(row["crop"] or row["typical_crop"] or ""),
            float(row["lat"]),
            float(row["lon"]),
            row["observed_yield"],
        )

    comparisons: list[dict] = []
    for field in candidates:
        lat_delta = (cells["CELL_LAT"] - field["lat"]).abs()
        lon_delta = (cells["CELL_LON"] - field["lon"]).abs()
        index = (lat_delta / max(lat_step, 0.01) + lon_delta / max(lon_step, 0.01)).idxmin()
        match = cells.loc[index]
        if lat_delta.loc[index] > lat_step * 0.55 or lon_delta.loc[index] > lon_step * 0.55:
            continue
        comparisons.append(
            {
                "Field": field["Field"],
                "Crop": field["Crop"],
                "Last harvest (t/ha)": field["Last harvest (t/ha)"],
                "Cell rain (mm/year)": round(float(match["recent_rain_mm"])),
                "Change (mm/year)": round(float(match["change_mm"])),
            }
        )
    return pd.DataFrame(comparisons)


def render_regional_weather_map(
    setup: FarmSetup,
    start_year: int,
    end_year: int,
    *,
    prefer_cache: bool = False,
) -> None:
    st.markdown(
        """
        <div class="section-head stacked">
          <h2>Rainfall across the area</h2>
          <p>Compare gridded rainfall around this field, then see which saved fields fall in the same weather cells.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "NASA POWER regional daily rainfall. Each square is a source grid cell; colors show the change between earlier and recent complete years. This is regional context, not a field measurement or forecast."
    )
    radius = st.select_slider(
        "Map extent",
        options=(1.0, 2.0),
        value=1.0,
        format_func=lambda value: "Nearby area (±1°)" if value == 1.0 else "Wider area (±2°)",
        key="regional_weather_radius",
    )
    request_key = (
        round(setup.farm.lat, 3),
        round(setup.farm.lon, 3),
        int(start_year),
        int(end_year),
        float(radius),
    )
    if st.button("Load rainfall map", key="load_regional_weather"):
        st.session_state["regional_weather_request"] = request_key

    if st.session_state.get("regional_weather_request") != request_key:
        st.caption("The regional layer loads only when you ask for it.")
        return
    if prefer_cache:
        st.info("Saved-climate mode is on. The map will use a saved regional scan if available.")

    try:
        with st.spinner("Loading nearby rainfall cells…"):
            daily = fetch_regional_rainfall(
                setup.farm.lat,
                setup.farm.lon,
                int(start_year),
                int(end_year),
                float(radius),
                prefer_cache=prefer_cache,
            )
        cells, early_years, recent_years = rainfall_change_cells(
            daily,
            int(start_year),
            int(end_year),
        )
    except RegionalWeatherError as exc:
        st.warning(str(exc))
        return

    metric = st.radio(
        "Map layer",
        ("Rainfall change", "Recent annual rainfall"),
        horizontal=True,
        key="regional_weather_layer",
        help="Rainfall change compares average annual totals for the earlier and recent parts of this selected climate period.",
    )
    metric_key = "change_mm" if metric == "Rainfall change" else "recent_rain_mm"
    fmap, (lat_step, lon_step) = _build_map(
        cells,
        setup,
        float(radius),
        metric_key,
        early_years,
        recent_years,
    )
    st_folium(
        fmap,
        height=460,
        use_container_width=True,
        returned_objects=[],
        key=f"regional-weather-{hash(request_key)}-{metric_key}",
    )
    st.caption(
        f"Earlier average: {early_years[0]}–{early_years[1]} · Recent average: {recent_years[0]}–{recent_years[1]} · Complete years only"
    )

    comparisons = _field_cell_values(cells, setup, lat_step, lon_step)
    if comparisons.empty:
        st.caption("No saved fields fall inside this map extent yet. Save another field nearby to compare its grid-cell context here.")
    else:
        st.markdown("**Fields in this map**")
        st.dataframe(comparisons, hide_index=True, width="stretch")
        st.caption("Rain values are estimates for the nearest NASA grid cell, not measurements taken on the field.")
