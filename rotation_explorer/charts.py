"""Plotly figures for NASA POWER climate patterns."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CHART_FONT = dict(family="DM Sans, Inter, sans-serif", size=13, color="#626263")
PLOT_BG = "#ffffff"
GRID = "#e9e9e9"
PAPER = "rgba(0,0,0,0)"


def _base_layout(**kwargs) -> dict:
    layout = dict(
        margin=dict(l=40, r=20, t=48, b=28),
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER,
        font=CHART_FONT,
        hoverlabel=dict(bgcolor="#1e1e1f", font_size=12, font_family="DM Sans"),
    )
    layout.update(kwargs)
    return layout


def climate_trend_figure(
    monthly: pd.DataFrame,
    variables: tuple[str, ...] = ("Maximum temperature", "Rainfall"),
) -> go.Figure:
    series = {
        "Rainfall": ("PRECTOTCORR", "Rainfall", "mm", "#8ec7e2", "bar"),
        "Maximum temperature": ("T2M_MAX", "Maximum temperature", "°C", "#1e1e1f", "line"),
        "Mean temperature": ("T2M", "Mean temperature", "°C", "#886816", "line"),
        "Minimum temperature": ("T2M_MIN", "Minimum temperature", "°C", "#397f9e", "line"),
    }
    selected = [name for name in variables if name in series]
    if not selected:
        selected = ["Maximum temperature", "Rainfall"]
    fig = make_subplots(
        rows=len(selected),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=min(0.12, 0.28 / max(len(selected), 1)),
        subplot_titles=selected,
    )
    for row, name in enumerate(selected, start=1):
        column, label, unit, color, kind = series[name]
        hover = f"%{{x|%b %Y}}<br>%{{y:.{'0f' if unit == 'mm' else '1f'}}} {unit}<extra></extra>"
        if kind == "bar":
            trace = go.Bar(
                x=monthly.index,
                y=monthly[column],
                name=label,
                marker_color=color,
                marker_line_width=0,
                hovertemplate=hover,
            )
        else:
            trace = go.Scatter(
                x=monthly.index,
                y=monthly[column],
                name=label,
                line=dict(color=color, width=2.2, shape="spline"),
                hovertemplate=hover,
            )
        fig.add_trace(trace, row=row, col=1)
        fig.update_yaxes(title_text=unit, row=row, col=1, gridcolor=GRID, zeroline=False)
    fig.update_layout(
        height=max(300, 250 * len(selected)),
        showlegend=False,
        **_base_layout(margin=dict(l=48, r=24, t=54, b=36)),
    )
    fig.update_annotations(
        font=dict(family="DM Sans, Inter, sans-serif", size=14, color="#1e1e1f"),
        yshift=8,
    )
    fig.update_xaxes(gridcolor=GRID, showgrid=False)
    return fig


def annual_bars_figure(df: pd.DataFrame) -> go.Figure:
    annual = (
        df.assign(year=df.index.year, precip=df["PRECTOTCORR"].clip(lower=0))
        .groupby("year")
        .agg(precip=("precip", "sum"), tmax=("T2M_MAX", "mean"))
        .reset_index()
    )
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=annual["year"],
            y=annual["precip"],
            name="Rain",
            marker_color="#8ec7e2",
            marker_line_width=0,
            yaxis="y",
            hovertemplate="%{x}<br>%{y:.0f} mm<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=annual["year"],
            y=annual["tmax"],
            name="Max temp",
            mode="lines+markers",
            line=dict(color="#1e1e1f", width=2.5),
            marker=dict(size=7, color="#f7ca50", line=dict(width=1.5, color="#1e1e1f")),
            yaxis="y2",
            hovertemplate="%{x}<br>%{y:.1f} °C<extra></extra>",
        )
    )
    fig.update_layout(
        height=540,
        **_base_layout(
            margin=dict(l=52, r=64, t=16, b=48),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.99,
                x=0.01,
                xanchor="left",
                bgcolor="rgba(255,255,255,0.9)",
                borderwidth=0,
                font=dict(size=12, color="#1e1e1f"),
            ),
            yaxis=dict(title="Rain (mm)", gridcolor=GRID, zeroline=False, rangemode="tozero"),
            yaxis2=dict(
                title="Max temp (°C)",
                overlaying="y",
                side="right",
                showgrid=False,
                range=[0, 40],
                dtick=10,
                tickformat=".0f",
            ),
            title=None,
        ),
    )
    return fig


def water_balance_figure(monthly: pd.DataFrame) -> go.Figure:
    """Monthly net moisture balance (Rainfall − ET₀) showing surplus vs. deficit months."""
    if "WATER_BALANCE_MM" not in monthly.columns:
        return go.Figure()
    wb = monthly["WATER_BALANCE_MM"].fillna(0.0)
    colors = ["#2f855a" if v >= 0 else "#d97706" for v in wb]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=monthly.index,
            y=wb,
            name="Rain − ET₀",
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="%{x|%b %Y}<br>Balance: %{y:+.0f} mm<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_width=1.2, line_color="#626263")
    fig.update_layout(
        height=320,
        showlegend=False,
        **_base_layout(
            margin=dict(l=48, r=20, t=24, b=36),
            yaxis=dict(title="Rain − ET₀ (mm/mo)", gridcolor=GRID, zeroline=False),
            xaxis=dict(gridcolor=GRID, showgrid=False),
        ),
    )
    return fig
