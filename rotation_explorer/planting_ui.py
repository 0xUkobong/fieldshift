"""Crop-season rainfall screening and dry-spell context."""

from __future__ import annotations

import calendar

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rotation_explorer.models import FarmSetup
from rotation_explorer.planting import (
    MONTHS,
    PlantingDataError,
    monthly_rain_signals,
    season_window_signals,
)


def _month_span(start_month: int, duration: int) -> str:
    end_month = ((start_month + duration - 2) % 12) + 1
    return f"{calendar.month_name[start_month]}–{calendar.month_name[end_month]}"


def _rain_chart(monthly: pd.DataFrame, start_month: int, duration: int) -> go.Figure:
    highlighted = {
        ((start_month + offset - 1) % 12) + 1
        for offset in range(duration)
    }
    colors = ["#397f9e" if int(month) in highlighted else "#c9dce3" for month in monthly["month"]]
    fig = go.Figure(
        go.Bar(
            x=monthly["month_name"],
            y=monthly["rain_mm"],
            marker_color=colors,
            marker_line_width=0,
            customdata=monthly[["wet_days", "dry_spell_days", "years"]],
            hovertemplate=(
                "%{x}<br>Median rainfall: %{y:.0f} mm"
                "<br>Wet days: %{customdata[0]:.0f}"
                "<br>Longest dry spell: %{customdata[1]:.0f} days"
                "<br>Years represented: %{customdata[2]:.0f}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=40, r=18, t=18, b=32),
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Inter, sans-serif", size=12, color="#626263"),
        showlegend=False,
        yaxis=dict(title="Median rainfall (mm)", rangemode="tozero", gridcolor="#e9e9e9"),
        xaxis=dict(title=None, categoryorder="array", categoryarray=list(MONTHS.values())),
        hoverlabel=dict(bgcolor="#1e1e1f", font_size=12, font_family="DM Sans"),
    )
    return fig


def render_planting_window(
    daily: pd.DataFrame,
    setup: FarmSetup,
    start_year: int,
    end_year: int,
) -> None:
    st.markdown(
        """
        <div class="section-head stacked">
          <h2>When do the rains usually support a season?</h2>
          <p>Use the field’s rainfall history to shortlist a season window and spot the dry gaps that can interrupt it.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Historical rainfall screen for {setup.crop} at {setup.farm.name} · {start_year}–{end_year}. "
        "It is not a planting-date forecast or a crop-stage model."
    )

    duration = st.select_slider(
        "Growing period to explore",
        options=(2, 3, 4, 5, 6),
        value=4,
        format_func=lambda months: f"{months} months",
        key="planting_window_duration",
        help="Choose a length that matches your crop and local variety. Actual crop duration depends on the variety and conditions.",
    )
    try:
        monthly = monthly_rain_signals(daily)
        windows, _ = season_window_signals(daily, int(duration))
    except PlantingDataError as exc:
        st.info(str(exc))
        return

    strongest = windows.iloc[0]
    season_label = _month_span(int(strongest["start_month"]), int(duration))
    st.markdown(f"**Rainiest historical {duration}-month window: {season_label}**")
    first, second, third = st.columns(3)
    first.metric("Rain in a typical window", f"{strongest['rain_median_mm']:.0f} mm")
    second.metric("Lower-quartile window", f"{strongest['rain_p25_mm']:.0f} mm", help="Rainfall was at or below this amount in one quarter of the complete historical windows")
    third.metric("Longest dry gap", f"{strongest['dry_spell_p75_days']:.0f} days", help="75th percentile of the longest observed dry spell within that window")

    st.plotly_chart(
        _rain_chart(monthly, int(strongest["start_month"]), int(duration)),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="planting_rain_chart",
    )
    table = monthly.rename(
        columns={
            "month_name": "Month",
            "rain_mm": "Median rain (mm)",
            "wet_days": "Wet days (≥1 mm)",
            "dry_spell_days": "Longest dry spell (days)",
            "hot_days": "Hot days (>32°C)",
            "years": "Years",
        }
    )
    st.dataframe(
        table[["Month", "Median rain (mm)", "Wet days (≥1 mm)", "Longest dry spell (days)", "Hot days (>32°C)", "Years"]],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"Blue bars mark the rainiest historical window for the selected season length, based on {int(strongest['years'])} complete seasons. "
        "A wet day is at least 1 mm; a dry spell counts consecutive days below 1 mm. "
        "Compare with soil moisture, local planting calendars, and the variety you plan to grow."
    )
