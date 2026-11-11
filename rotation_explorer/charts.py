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


def climate_trend_figure(monthly: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            "Monthly maximum temperature",
            "Monthly rainfall",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly["T2M_MAX"],
            name="Max temperature",
            line=dict(color="#1e1e1f", width=2.2, shape="spline"),
            hovertemplate="%{x|%b %Y}<br>%{y:.1f} °C<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=monthly.index,
            y=monthly["PRECTOTCORR"],
            name="Rainfall",
            marker_color="#8ec7e2",
            marker_line_width=0,
            hovertemplate="%{x|%b %Y}<br>%{y:.0f} mm<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        height=540,
        showlegend=False,
        **_base_layout(margin=dict(l=48, r=24, t=64, b=36)),
    )
    fig.update_annotations(
        font=dict(family="DM Sans, Inter, sans-serif", size=14, color="#1e1e1f"),
        yshift=8,
    )
    fig.update_yaxes(title_text="°C", row=1, col=1, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text="mm", row=2, col=1, gridcolor=GRID, zeroline=False)
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
