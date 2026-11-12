"""Streamlit presentation layer. Keep widgets here, domain logic elsewhere."""

from __future__ import annotations

from html import escape
import math

import pandas as pd
import streamlit as st

from rotation_explorer.charts import (
    annual_bars_figure,
    climate_trend_figure,
    water_balance_figure,
)
from rotation_explorer.cache import cached_points, is_cached
from rotation_explorer.config import (
    CROPS,
    HEAT_STRESS_C,
    LANGUAGES,
    POWER_YEAR_MAX,
    POWER_YEAR_MIN,
    PRIORITIES,
    PRIORITY_WEIGHT,
    ROTATION_AGROFORESTRY,
    ROTATION_CURRENT,
    ROTATION_DROUGHT,
    ROTATION_INTERCROP,
    ROTATION_LEGUME,
    SOIL_TYPES,
    SOIL_WEIGHT,
    WATER_WEIGHT,
    infer_soil_type,
)
from rotation_explorer.geo import farm_from_place
from rotation_explorer.seo import app_route, asset_src
from rotation_explorer.location_ui import hydrate_location, session_place
from rotation_explorer.climate import climate_story
from rotation_explorer.insights import (
    RiskFlag,
    action_line,
    farmer_card_html,
    rotation_visuals,
    sms_summary,
)
from rotation_explorer.models import ClimateSummary, Farm, FarmSetup, RotationResult
from rotation_explorer.report import comparison_report, rotation_csv_report
from rotation_explorer.store import (
    list_fields,
    load_field,
    load_last_setup,
    load_roster,
    save_field,
    save_roster_entry,
)

NEXT_STEPS = {
    ROTATION_CURRENT: (
        "Ask whether heat and rainfall trends already show up on this field "
        "before you change crops."
    ),
    ROTATION_DROUGHT: (
        "Ask about cover-crop seed, termination timing, and whether a "
        "drought-tolerant variety fits your market and equipment."
    ),
    ROTATION_LEGUME: (
        "Ask about inoculant, harvest timing, and how much cereal area you "
        "can rotate this season."
    ),
    ROTATION_AGROFORESTRY: (
        "Ask about suitable tree species, spacing, land tenure, and "
        "how long until you see the first soil benefit."
    ),
    ROTATION_INTERCROP: (
        "Ask about which companion crop fits your market, peak labour "
        "timing, and whether your planting equipment can handle mixed beds."
    ),
}

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

ROTATION_META = {
    ROTATION_CURRENT: ("Baseline", "Keep what already works"),
    ROTATION_DROUGHT: ("Water", "Cover soil, ease demand"),
    ROTATION_LEGUME: ("Soil", "Fix nitrogen, build matter"),
    ROTATION_AGROFORESTRY: ("Trees", "Long-term soil & shade"),
    ROTATION_INTERCROP: ("Mixed", "Two crops, one season"),
}

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;500;600&display=swap');
:root { --canvas:#f5f5f5; --cream:#f8f4e6; --paper:#fff; --mist:#e9e9e9; --ink:#1e1e1f; --carbon:#000; --blue:#8ec7e2; --yellow:#f7ca50; --muted:#626263; --line:#d8d8d8; --body:'DM Sans',Inter,ui-sans-serif,system-ui,sans-serif; --mono:'DM Mono',ui-monospace,monospace; }
html,body,[class*="css"] { font-family:var(--body); color:var(--ink); }
.stApp { background:var(--canvas); color:var(--ink); }
.block-container { max-width:100%; padding:1.2rem clamp(1.2rem,3.2vw,3.5rem) 4rem; }
html { scroll-behavior:smooth; scroll-padding-top:1rem; }
*,*::before,*::after { box-sizing:border-box; }
button,a,[role="button"] { touch-action:manipulation; -webkit-tap-highlight-color:rgba(30,30,31,.12); }
#MainMenu,footer,.stDeployButton,.stAppDeployButton { visibility:hidden; }
[data-testid="stSidebarNav"] { display:none !important; }
.legal { max-width:44rem; }
.legal h2 { margin:2.2rem 0 .6rem; color:var(--carbon); font-size:1.45rem; font-weight:400; letter-spacing:-.05em; }
.legal p,.legal li { color:#454546; font-size:.95rem; line-height:1.55; }
.legal ul { padding-left:1.15rem; }
.legal a { color:var(--ink); }
.site-foot { display:flex; flex-wrap:wrap; gap:.85rem 1.4rem; align-items:center; margin-top:2.4rem; padding-top:1rem; border-top:1px solid var(--line); }
.site-foot a { color:var(--ink)!important; text-decoration:none!important; font-family:var(--mono); font-size:.68rem; letter-spacing:.03em; text-transform:uppercase; }
.site-foot a:hover { text-decoration:underline!important; text-underline-offset:3px; }
div[data-testid="stPageLink"] a { color:var(--ink)!important; text-decoration:none!important; font-family:var(--mono); font-size:.7rem; letter-spacing:.03em; text-transform:uppercase; }
.site-foot .copy { margin-left:auto; color:var(--muted); font-family:var(--mono); font-size:.65rem; line-height:1.4; }
.legal-page section[data-testid="stSidebar"] { display:none !important; }
header[data-testid="stHeader"] { background:transparent; }
header button[data-testid="stSidebarCollapsedControl"] { visibility:visible!important; opacity:1!important; width:44px!important; height:44px!important; min-width:44px!important; background:var(--blue)!important; border:0!important; border-radius:22px!important; color:var(--carbon)!important; }
header button[data-testid="stSidebarCollapsedControl"]:hover { background:#a6d5e9!important; }
section[data-testid="stSidebar"] { background:var(--cream); border-right:1px solid var(--line); }
section[data-testid="stSidebar"]>div { padding:1.25rem 1rem 2rem; }
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3 { color:var(--carbon); letter-spacing:-.045em; }
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] [data-testid="stCaption"] { color:var(--muted); }
section[data-testid="stSidebar"] hr { border-color:var(--line); }
section[data-testid="stSidebar"] [data-baseweb="tag"],section[data-testid="stSidebar"] [data-baseweb="tag"] *,section[data-testid="stSidebar"] [data-slot="tag"],section[data-testid="stSidebar"] [data-slot="tag"] *,section[data-testid="stSidebar"] [class*="tag"] { background:var(--blue)!important; color:var(--carbon)!important; border-radius:22px!important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:var(--ink)!important; font-size:.9rem; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height:1.45; }
.topbar { display:flex; align-items:center; justify-content:space-between; gap:1.5rem; padding:.65rem .85rem; margin-bottom:1.7rem; background:var(--mist); border-radius:3px; }
.brand { display:flex; align-items:center; gap:.65rem; color:var(--carbon); font-size:1rem; font-weight:600; letter-spacing:-.05em; text-decoration:none; }
.brand-mark { width:36px; height:36px; display:block; object-fit:contain; }
.brand small { font-family:var(--mono); font-size:.65rem; font-weight:400; letter-spacing:.015em; text-transform:uppercase; color:var(--muted); }
.toplinks { display:flex; align-items:center; gap:clamp(.75rem,2vw,2rem); }
.toplinks a { color:var(--ink)!important; text-decoration:none!important; font-family:var(--mono); font-size:.7rem; letter-spacing:.025em; }
.toplinks a:hover { text-decoration:underline; text-underline-offset:4px; }
.mobile-nav { display:none; }
.topbar .brand,.topbar .brand:visited { color:var(--carbon)!important; text-decoration:none!important; }
.pill-link { display:inline-flex; align-items:center; gap:.75rem; padding:.55rem .65rem .55rem .9rem; border-radius:22px; background:var(--blue); color:var(--carbon)!important; text-decoration:none!important; font-size:.83rem; transition:background .15s ease; }
.pill-link:hover { background:#a6d5e9; }
.pill-link span { display:inline-grid; place-items:center; width:1.45rem; height:1.45rem; background:rgba(255,255,255,.65); border-radius:50%; font-size:1rem; line-height:1; }
.hero { display:grid; grid-template-columns:minmax(0,1fr) minmax(15rem,.52fr); gap:2rem; align-items:end; padding:0 0 1.3rem; border-bottom:1px solid var(--line); }
.kicker,.eyebrow { display:block; color:var(--muted); font-family:var(--mono); font-size:.7rem; line-height:1.4; letter-spacing:.045em; text-transform:uppercase; }
.kicker { margin:0 0 .85rem; }
.hero h1 { max-width:19ch; margin:0; color:var(--carbon); font-size:clamp(2.5rem,4.5vw,3.8rem); font-weight:400; line-height:1; letter-spacing:-.065em; text-wrap:balance; }
.lede { max-width:38rem; margin:.75rem 0 0; color:#454546; font-size:1rem; line-height:1.45; letter-spacing:-.025em; }
.hero-aside { padding:1rem 0 0 1.2rem; border-left:1px solid var(--line); }
.live-pill { display:inline-flex; align-items:center; gap:.5rem; padding:.42rem .72rem; border-radius:22px; background:var(--yellow); color:var(--carbon); font-family:var(--mono); font-size:.68rem; letter-spacing:.01em; }
.live-dot { width:7px; height:7px; border-radius:50%; background:var(--carbon); }
.quiet { margin:.8rem 0 0; color:var(--muted); font-size:.85rem; line-height:1.45; }
.hero-nav { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1.2rem; }
.hero-nav a { display:inline-flex; align-items:center; gap:.45rem; padding:.58rem .7rem .58rem .9rem; background:var(--blue); color:var(--carbon); border-radius:22px; font-size:.8rem; text-decoration:none; }
.hero-nav a span { font-size:1.1rem; }
.facts { display:grid; grid-template-columns:1fr 1fr 1fr 1.35fr; gap:0; margin:0 0 4rem; padding:.95rem 0 1.1rem; border-bottom:1px solid var(--line); }
.fact { padding:.15rem 1.1rem .15rem 0; }
.fact+.fact { padding-left:1.1rem; border-left:1px solid var(--line); }
.fact span { display:block; margin-bottom:.38rem; color:var(--muted); font-family:var(--mono); font-size:.67rem; letter-spacing:.04em; text-transform:uppercase; }
.fact strong { display:block; color:var(--ink); font-size:1rem; font-weight:500; letter-spacing:-.03em; line-height:1.4; }
.fact small { display:block; margin-top:.25rem; color:var(--muted); font-size:.78rem; font-weight:400; line-height:1.35; text-transform:none; letter-spacing:-.01em; }
.fact.note strong { font-size:.88rem; font-weight:400; }
.section-head { display:flex; align-items:end; justify-content:space-between; gap:1.25rem; margin:3.8rem 0 1.1rem; scroll-margin-top:1rem; }
.section-head h2 { margin:0; color:var(--carbon); font-size:clamp(1.7rem,2.6vw,2.7rem); font-weight:400; line-height:1.08; letter-spacing:-.06em; text-wrap:balance; }
.section-head p { max-width:46rem; margin:.4rem 0 0; color:var(--muted); font-size:.9rem; line-height:1.5; letter-spacing:-.015em; }
.section-head.stacked { display:block; }
.stat-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:0; margin:0 0 1.25rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.stat { min-height:7.2rem; padding:1rem .8rem 1rem 0; }
.stat+.stat { padding-left:.85rem; border-left:1px solid var(--line); }
.stat .k { display:block; color:var(--muted); font-family:var(--mono); font-size:.64rem; line-height:1.35; letter-spacing:.035em; text-transform:uppercase; }
.stat .v { display:block; margin:.48rem 0 .1rem; color:var(--carbon); font-size:clamp(1.45rem,2vw,2rem); font-weight:400; line-height:1; letter-spacing:-.06em; }
.stat .u { color:var(--muted); font-size:.75rem; line-height:1.3; }
.stat.heat .v { color:var(--ink); }.stat.rain .v { color:#397f9e; }.stat.gold .v { color:#886816; }
.rot-card { position:relative; height:100%; min-height:20rem; padding:1.1rem 1.1rem 1rem; background:var(--paper); border:1px solid var(--line); border-radius:22px; box-sizing:border-box; overflow:hidden; transition:transform .18s ease, box-shadow .18s ease; }
.rot-card:hover { transform:translateY(-3px); box-shadow:0 8px 28px rgba(0,0,0,.09); }
.rot-card::before { content:''; position:absolute; top:0; left:0; right:0; height:4px; background:var(--mist); border-radius:22px 22px 0 0; }
.rot-card.leader { border-color:var(--carbon); border-width:2px; }
.rot-card.leader::before { background:linear-gradient(90deg,#f7ca50,#8ec7e2); }
.rot-card.accent-water::before { background:linear-gradient(90deg,#8ec7e2,#397f9e); }
.rot-card.accent-soil::before { background:linear-gradient(90deg,#4caf78,#1e1e1f); }
.rot-card.accent-base::before { background:linear-gradient(90deg,var(--mist),var(--line)); }
.rot-card.accent-agro::before { background:linear-gradient(90deg,#6dbf7e,#2d6a4f); }
.rot-card.accent-intercrop::before { background:linear-gradient(90deg,#c9a84c,#7b5e1a); }
.badge { display:inline-flex; align-items:center; gap:.35rem; padding:.32rem .65rem; border-radius:22px; background:var(--mist); color:var(--ink); font-family:var(--mono); font-size:.62rem; line-height:1.3; letter-spacing:.02em; text-transform:uppercase; }
.badge.gold { background:var(--yellow); color:var(--carbon); font-weight:600; }
.rot-card h3 { max-width:18ch; margin:.9rem 0 .2rem; color:var(--carbon); font-size:1.38rem; font-weight:400; line-height:1.12; letter-spacing:-.06em; text-wrap:balance; }
.tagline { min-height:2rem; margin:0 0 .95rem; color:var(--muted); font-size:.82rem; line-height:1.4; }
.score-row { display:flex; align-items:baseline; gap:.5rem; margin-bottom:1.1rem; }
.score-row .num { background:linear-gradient(135deg,var(--carbon) 40%,#555); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; font-size:3rem; font-weight:500; line-height:1; letter-spacing:-.07em; }
.score-row .den { color:var(--muted); font-size:.76rem; letter-spacing:-.01em; }
.bars { display:grid; gap:.6rem; margin-bottom:1rem; }
.bar-lab { display:flex; justify-content:space-between; margin-bottom:.28rem; color:var(--muted); font-size:.71rem; letter-spacing:.01em; }
.bar-lab .bar-val { font-family:var(--mono); font-size:.7rem; color:var(--ink); font-weight:500; }
.track { height:7px; overflow:hidden; border-radius:10px; background:var(--mist); }
.fill { height:100%; border-radius:10px; transition:width .6s cubic-bezier(.4,0,.2,1); }
.seq { padding:.6rem .75rem; border-radius:14px; background:linear-gradient(135deg,var(--cream) 0%,#f0ead6 100%); color:var(--ink); font-size:.77rem; line-height:1.45; border:1px solid rgba(0,0,0,.06); }
.result-note,.rec-banner { margin:.2rem 0 1.1rem; padding:1.1rem 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); color:var(--ink); }
.rec-banner { margin:0 0 1.6rem; }
.result-note strong,.rec-banner strong { font-size:1.02rem; font-weight:500; letter-spacing:-.03em; }
.result-note p,.rec-banner p { margin:.35rem 0 0; color:var(--muted); font-size:.88rem; line-height:1.5; }
.steps { display:flex; flex-wrap:wrap; gap:.45rem; margin:.8rem 0 0; }
.step { display:inline-flex; align-items:center; gap:.45rem; padding:.4rem .7rem; border-radius:22px; background:var(--mist); color:var(--ink); font-size:.8rem; }
.step b { font-family:var(--mono); font-size:.72rem; font-weight:500; color:var(--muted); }
.story { margin:0 0 1.6rem; padding:1rem 1.1rem; background:var(--cream); border-radius:18px; color:var(--ink); font-size:.95rem; line-height:1.5; }
.map-panel { min-height:15rem; padding:1.2rem 1.25rem; background:var(--cream); border-radius:18px; }
.map-panel h3 { margin:.8rem 0 .2rem; color:var(--carbon); font-size:1.4rem; font-weight:400; line-height:1.15; letter-spacing:-.05em; }
.map-panel p { margin:.4rem 0; color:var(--muted); font-size:.85rem; line-height:1.45; }
.map-panel strong { color:var(--ink); font-size:.9rem; font-weight:500; }
.map-panel hr { margin:1rem 0; border:0; border-top:1px solid var(--line); }
.pills { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.45rem; }
.pill { display:inline-block; padding:.28rem .6rem; border-radius:22px; background:var(--blue); color:var(--carbon); font-size:.75rem; }
.compare-scroll { width:100%; margin:0 0 1.4rem; overflow-x:auto; overscroll-behavior-x:contain; -webkit-overflow-scrolling:touch; border:1px solid var(--line); border-radius:16px; }
.compare { width:100%; min-width:40rem; border-collapse:collapse; margin:0; font-size:.88rem; table-layout:fixed; }
.compare-hint { display:none; margin:-.75rem 0 1rem; color:var(--muted); font-size:.75rem; }
.compare thead { position:sticky; top:0; z-index:1; }
.compare th { text-align:left; font-family:var(--mono); font-size:.62rem; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); font-weight:600; padding:.55rem .6rem .55rem .75rem; border-bottom:2px solid var(--carbon); background:var(--canvas); }
.compare th:first-child { padding-left:.75rem; }
.compare th:not(:first-child) { width:6rem; text-align:center; padding-left:.6rem; }
.compare td { padding:.8rem .6rem .8rem .75rem; border-bottom:1px solid var(--line); vertical-align:middle; transition:background .12s ease; }
.compare td:first-child { padding-left:.75rem; }
.compare td:not(:first-child) { text-align:center; padding-left:.6rem; }
.compare tbody tr:hover td { background:rgba(142,199,226,.08); }
.compare tr.top td { background:linear-gradient(90deg, rgba(247,202,80,.18) 0%, transparent 60%); }
.compare tbody tr.top:hover td { background:linear-gradient(90deg, rgba(247,202,80,.28) 0%, rgba(142,199,226,.08) 60%); }
.compare .name { font-weight:600; color:var(--carbon); max-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; letter-spacing:-.02em; font-size:.9rem; }
.score-chip { display:inline-flex; align-items:center; justify-content:center; width:2rem; height:2rem; border-radius:50%; font-family:var(--mono); font-size:.82rem; font-weight:700; }
.score-chip.hi { background:#d4f0d4; color:#1a4d1a; }
.score-chip.mid { background:#fff3cc; color:#5c4200; }
.score-chip.lo { background:#fde8e8; color:#5a1c1c; }
.score-chip.overall { background:var(--carbon); color:var(--paper); font-size:.88rem; width:2.2rem; height:2.2rem; }
.actions { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; margin:.35rem 0 1.4rem; }
.dirty { margin:.7rem 0 .4rem; padding:.65rem .75rem; border-radius:14px; background:#fff6d8; color:#5c4a12; font-size:.82rem; line-height:1.4; }
.lvl { display:inline-flex; align-items:center; gap:.35rem; margin:0 .4rem .4rem 0; padding:.28rem .65rem; border-radius:22px; font-size:.75rem; font-weight:500; }
.lvl.green { background:#d8f0d8; color:#1c3d1c; }
.lvl.yellow { background:#f7ca50; color:#1e1e1f; }
.lvl.red { background:#f4c2c2; color:#5a1c1c; }
.cue-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.55rem; margin:0 0 1.1rem; }
.cue { padding:.7rem .75rem; background:var(--paper); border:1px solid var(--line); border-radius:16px; }
.cue b { display:block; font-size:.68rem; font-family:var(--mono); letter-spacing:.04em; text-transform:uppercase; color:var(--muted); font-weight:500; margin-bottom:.3rem; }
.cue span { font-size:.95rem; }
.sms-box { font-family:var(--mono); font-size:.78rem; line-height:1.5; background:var(--cream); border-radius:14px; padding:.85rem 1rem; white-space:pre-wrap; }
.tip-box { margin:0 0 1.2rem; padding:.9rem 1rem; background:var(--cream); border-radius:16px; }
@media(max-width:720px) { .cue-grid { grid-template-columns:1fr 1fr; } }
div[data-testid="stExpander"] { margin-top:.6rem; border:1px solid var(--line); border-radius:18px; background:var(--paper); }
div[data-testid="stExpander"] summary { background:var(--paper)!important; border-radius:18px; }
div[data-testid="stExpander"] summary:hover { background:var(--mist)!important; }
div[data-testid="stExpander"] summary p,div[data-testid="stExpander"] summary span,div[data-testid="stExpander"] summary svg { color:var(--ink)!important; fill:var(--ink)!important; font-size:.88rem; }
div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] { color:var(--muted); line-height:1.5; }
.method-grid { display:grid; grid-template-columns:1fr 1fr; gap:2rem; padding:1rem 0 1.3rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.method h4 { margin:0 0 .55rem; color:var(--ink); font-size:1.02rem; font-weight:500; letter-spacing:-.035em; }
.method ul { margin:0; padding-left:1.1rem; color:var(--muted); font-size:.87rem; line-height:1.5; }.method li { margin:.35rem 0; }.method strong { color:var(--ink); font-weight:500; }
.foot { margin-top:1.7rem; padding-top:1rem; border-top:1px solid var(--line); color:var(--muted); font-family:var(--mono); font-size:.68rem; line-height:1.5; }
div[data-testid="stPlotlyChart"] { padding:.25rem; border-radius:22px; background:var(--paper); }
div[data-testid="stPlotlyChart"] iframe { border-radius:18px; }
div[data-testid="stDeckGlJsonChart"] { overflow:hidden; border:1px solid var(--line); border-radius:22px; background:var(--mist); }
div[data-testid="stCustomComponentV1"] { min-width:0; max-width:100%; overflow:hidden; }
div[data-testid="stDataFrame"] { max-width:100%; overflow-x:auto; }
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div { border-color:#bdbdbd; border-radius:14px; }
button[kind="secondary"],.stButton button { border:0; border-radius:22px; background:var(--blue); color:var(--carbon); }
button[kind="secondary"]:hover,.stButton button:hover { border:0; background:#a6d5e9; color:var(--carbon); }
:focus-visible { outline:2px solid var(--carbon); outline-offset:3px; }
@media(max-width:1000px) { .hero { grid-template-columns:1fr; gap:1rem; }.hero-aside { max-width:40rem; padding:.8rem 0 0; border-left:0; }.stat-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }.stat:nth-child(4) { border-left:0; padding-left:0; } }
@media(max-width:1000px) {
  .block-container { padding-left:clamp(1rem,3vw,1.8rem); padding-right:clamp(1rem,3vw,1.8rem); }
  .stHorizontalBlock { flex-wrap:wrap; }
}
@media(max-width:720px) {
  html { scroll-padding-top:.5rem; }
  .block-container { padding:.7rem .85rem calc(2rem + env(safe-area-inset-bottom)); }
  .topbar { position:relative; z-index:5; display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:.35rem; margin-bottom:1.25rem; padding:.55rem .65rem; }
  .brand { min-height:44px; gap:.55rem; font-size:.95rem; }
  .brand-mark { width:36px; height:36px; }
  .toplinks { display:none; }
  .mobile-nav { display:block; position:relative; justify-self:end; }
  .mobile-nav summary { display:inline-flex; align-items:center; justify-content:center; gap:.6rem; min-width:84px; min-height:44px; padding:.45rem .75rem; border-radius:22px; background:var(--blue); color:var(--carbon); cursor:pointer; font-family:var(--mono); font-size:.72rem; letter-spacing:.02em; list-style:none; -webkit-tap-highlight-color:rgba(30,30,31,.12); }
  .mobile-nav summary::-webkit-details-marker { display:none; }
  .mobile-nav summary::marker { content:""; }
  .mobile-menu-icon::before { content:"☰"; font-family:system-ui,sans-serif; font-size:1rem; line-height:1; }
  .mobile-nav[open] summary { background:#a6d5e9; }
  .mobile-nav[open] .mobile-menu-icon::before { content:"×"; font-size:1.35rem; }
  .mobile-nav-menu { position:absolute; top:calc(100% + .55rem); right:0; z-index:20; display:grid; gap:.15rem; width:min(18rem,calc(100vw - 1.7rem)); max-height:min(75vh,30rem); overflow-y:auto; padding:.45rem; border:1px solid var(--line); border-radius:16px; background:var(--cream); }
  .mobile-nav-menu>a { display:flex; align-items:center; min-height:44px; padding:.55rem .75rem; border-radius:12px; color:var(--ink)!important; text-decoration:none!important; font-family:var(--mono); font-size:.72rem; letter-spacing:.025em; }
  .mobile-nav-menu>a:hover,.mobile-nav-menu>a:focus-visible { background:var(--mist); text-decoration:none!important; }
  .mobile-nav-menu>.pill-link { justify-content:space-between; margin-top:.2rem; padding:.3rem .5rem .3rem .8rem; background:var(--blue); color:var(--carbon)!important; font-family:var(--body); font-size:.84rem; }
  .mobile-nav-menu>.pill-link span { display:inline-grid; flex:0 0 auto; place-items:center; width:1.45rem; height:1.45rem; border-radius:50%; background:rgba(255,255,255,.65); font-size:1rem; line-height:1; }
  .hero { grid-template-columns:minmax(0,1fr); gap:.7rem; padding-bottom:1rem; }
  .hero h1 { max-width:16ch; font-size:clamp(2.25rem,10.5vw,3.5rem); line-height:1.02; }
  .lede { font-size:.98rem; line-height:1.5; }
  .steps { gap:.4rem; }
  .step { min-height:40px; padding:.38rem .58rem; font-size:.75rem; }
  .hero-aside { padding:.4rem 0 0; }
  .facts { grid-template-columns:repeat(2,minmax(0,1fr)); gap:0; margin-bottom:1.5rem; }
  .fact,.fact+.fact { min-width:0; padding:.7rem .55rem .7rem 0; border-left:0; border-top:1px solid var(--line); }
  .fact:nth-child(-n+2) { border-top:0; }
  .fact:nth-child(even) { padding-left:.7rem; border-left:1px solid var(--line); }
  .fact strong { overflow-wrap:anywhere; font-size:.94rem; }
  .fact small { overflow-wrap:anywhere; }
  .stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stat,.stat+.stat { min-width:0; min-height:6.5rem; padding:.8rem .55rem .8rem 0; border-left:0; }
  .stat:nth-child(even) { padding-left:.65rem; border-left:1px solid var(--line); }
  .stat .k { font-size:.6rem; }
  .stat .v { font-size:clamp(1.35rem,7vw,1.8rem); }
  .section-head { display:block; margin:2.4rem 0 .9rem; }
  .section-head h2 { font-size:clamp(1.65rem,8vw,2.25rem); }
  .section-head p { font-size:.86rem; }
  .rot-card { min-height:0; padding:1rem; }
  .rot-card h3 { font-size:1.3rem; }
  .compare-hint { display:block; }
  .map-panel { min-height:0; padding:1rem; }
  .map-panel h3 { overflow-wrap:anywhere; }
  .method-grid { grid-template-columns:minmax(0,1fr); gap:1.2rem; }
  .cue-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stHorizontalBlock { flex-direction:column!important; gap:.85rem!important; }
  .stHorizontalBlock > div[data-testid="column"] { flex:1 1 100%!important; width:100%!important; min-width:0!important; max-width:100%!important; }
  section[data-testid="stSidebar"]>div { padding:1rem .85rem calc(1.5rem + env(safe-area-inset-bottom)); }
  section[data-testid="stSidebar"] [data-baseweb="select"]>div,
  section[data-testid="stSidebar"] [data-baseweb="input"]>div,
  section[data-testid="stSidebar"] input { min-height:44px; font-size:16px!important; }
  section[data-testid="stSidebar"] button,
  section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button { min-height:46px; width:100%; }
  header button[data-testid="stSidebarCollapsedControl"] { width:46px!important; height:46px!important; min-width:46px!important; }
  div[data-testid="stCustomComponentV1"] iframe { max-width:100%!important; }
  div[data-testid="stPlotlyChart"] { padding:.1rem; border-radius:16px; }
  div[data-testid="stPlotlyChart"] iframe { max-width:100%; }
  div[data-testid="stDownloadButton"] button { width:100%; min-height:46px; white-space:normal; }
  .actions { align-items:stretch; }
  .foot,.site-foot { gap:.65rem; }
  .site-foot .copy { width:100%; margin-left:0; }
}
@media(max-width:390px) {
  .block-container { padding-left:.7rem; padding-right:.7rem; }
  .brand small { display:none; }
  .facts { grid-template-columns:minmax(0,1fr); }
  .fact,.fact+.fact,.fact:nth-child(even) { padding:.65rem 0; border-left:0; border-top:1px solid var(--line); }
  .fact:first-child { border-top:0; }
  .cue-grid { grid-template-columns:minmax(0,1fr); }
  .stat .k { font-size:.57rem; letter-spacing:.01em; }
}
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { scroll-behavior:auto!important; transition:none!important; } }
"""


def inject_css() -> None:
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


def render_header() -> None:
    explorer_url = app_route("/")
    about_url = app_route("/About")
    st.markdown(
        f"""
        <nav class="topbar" aria-label="Main navigation">
          <a class="brand" href="{explorer_url}" target="_self"><img class="brand-mark" src="{asset_src('header-mark.png')}" width="36" height="36" alt="">FIELD SHIFT <small>Rotation Explorer</small></a>
          <div class="toplinks">
            <a href="#field">FIELD</a>
            <a href="#climate">CLIMATE</a>
            <a href="#rotations">ROTATIONS</a>
            <a href="{about_url}">ABOUT</a>
            <a class="pill-link" href="#rotations">Explore rotations <span>↗</span></a>
          </div>
          <details class="mobile-nav">
            <summary><span>Menu</span><span class="mobile-menu-icon" aria-hidden="true"></span></summary>
            <nav class="mobile-nav-menu" aria-label="Mobile navigation">
              <a href="#field">Field</a>
              <a href="#climate">Climate</a>
              <a href="#rotations">Rotations</a>
              <a href="{about_url}" target="_self">About</a>
              <a class="pill-link" href="#rotations">Explore rotations <span>↗</span></a>
            </nav>
          </details>
        </nav>
        <div class="hero">
          <div>
            <div class="kicker">Crop rotation, with local climate in context</div>
            <h1 id="overview">Compare rotations for the field you farm.</h1>
            <p class="lede">Name the real place — continent, country, state, local government, area — then set crop and goals. NASA weather loads for that pin, not a sample farm.</p>
            <div class="steps" aria-label="How to use Rotation Explorer">
              <span class="step"><b>1</b> Locate the field</span>
              <span class="step"><b>2</b> Set crop and goals</span>
              <span class="step"><b>3</b> Apply and compare</span>
            </div>
          </div>
          <div class="hero-aside">
            <div class="live-pill"><span class="live-dot"></span> NASA POWER · 2018–2025</div>
            <p class="quiet">A starting point for local decisions. Check field conditions with your own observations and local agronomic advice.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.html(
        """
        <script>
          if (!window.__fieldShiftMobileMenuBound) {
            window.__fieldShiftMobileMenuBound = true;
            document.addEventListener("click", (event) => {
              const link = event.target.closest(".mobile-nav-menu a");
              const menu = link?.closest(".mobile-nav");
              if (menu) menu.open = false;
            });
          }
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def render_sidebar() -> tuple[FarmSetup | None, bool]:
    if "applied_setup" not in st.session_state:
        last = load_last_setup()
        st.session_state["applied_setup"] = last
        if last:
            hydrate_location(last.farm)
            st.session_state["field_crop"] = last.crop
            st.session_state["farm_priorities"] = list(last.priorities)
            st.session_state["farmer_name"] = last.farmer_name
            st.session_state["extra_local_tip"] = last.local_tip
            st.session_state["field_soil_type"] = last.soil_type
            saved_yield = last.observed_yield_t_ha
            st.session_state["observed_yield"] = "" if saved_yield is None else str(saved_yield)

    st.session_state.setdefault("field_crop", "Maize")
    st.session_state.setdefault("farm_priorities", [])
    st.session_state.setdefault("climate_period", (POWER_YEAR_MIN, POWER_YEAR_MAX))
    st.session_state.setdefault("applied_climate_period", (POWER_YEAR_MIN, POWER_YEAR_MAX))
    st.session_state.setdefault("observed_yield", "")
    st.session_state.setdefault("custom_soil_note", "")
    st.session_state.setdefault("work_mode", "Farmer")
    st.session_state.setdefault("share_language", "en")
    st.session_state.setdefault("low_bandwidth", False)
    st.session_state.setdefault("farmer_name", "")
    st.session_state.setdefault("extra_local_tip", "")
    st.session_state.setdefault("field_soil_type", "Auto (from site)")

    with st.sidebar:
        st.markdown("### Field context")
        saved = list_fields()
        if saved:
            labels = {
                row["id"]: f"{row['name']} · {row['country'] or row['region']}"
                for row in saved
            }
            chosen_id = st.selectbox(
                "Saved field profiles",
                [0] + list(labels),
                format_func=lambda value: "Current session" if value == 0 else labels[value],
                key="saved_field_id",
            )
            if chosen_id and st.button("Open saved field"):
                loaded = load_field(int(chosen_id))
                if loaded:
                    st.session_state["applied_setup"] = loaded
                    hydrate_location(loaded.farm)
                    st.session_state["field_crop"] = loaded.crop
                    st.session_state["farm_priorities"] = list(loaded.priorities)
                    st.session_state["farmer_name"] = loaded.farmer_name
                    st.session_state["extra_local_tip"] = loaded.local_tip
                    st.session_state["field_soil_type"] = loaded.soil_type
                    saved_yield = loaded.observed_yield_t_ha
                    st.session_state["observed_yield"] = (
                        "" if saved_yield is None else str(saved_yield)
                    )
                    st.session_state["climate_request_attempted"] = False
                    st.rerun()
        else:
            st.caption("No saved fields yet. Apply a comparison to keep this field on the device.")

        place = session_place()
        if place.has_point():
            st.caption(place.region_label())
        else:
            st.caption("Set the field location on the map first.")

        submitted = False
        with st.form("field_setup", border=False):
            crop = st.selectbox("Current main crop", list(CROPS), key="field_crop")
            soil_choice = st.selectbox(
                "Soil texture",
                list(SOIL_TYPES),
                key="field_soil_type",
                help="Auto infers texture from the site description; override if you know your field's soil.",
            )
            soil_note = st.text_input(
                "Soil notes (optional)",
                placeholder="e.g. sandy loam, low organic matter",
                key="custom_soil_note",
                max_chars=120,
            )
            climate_period = st.slider(
                "Climate period",
                min_value=POWER_YEAR_MIN,
                max_value=POWER_YEAR_MAX,
                step=1,
                key="climate_period",
                help="Choose the years used for climate summaries, charts, and rotation scores.",
            )
            st.text_input(
                "Last harvest yield (t/ha, optional)",
                key="observed_yield",
                placeholder="e.g. 4.2",
                help="Your field record for context. NASA POWER does not provide crop-yield data, so this does not change the climate score.",
            )
            priorities = st.multiselect(
                "What matters for this field?",
                list(PRIORITIES),
                key="farm_priorities",
                help="Choose at least one priority. Scores use these goals.",
            )
            if st.session_state["work_mode"] == "Extension worker":
                st.text_input("Farmer name", key="farmer_name", max_chars=60)
            st.text_input(
                "Local tip (optional)",
                placeholder="e.g. Farmers here intercrop with pigeon pea",
                key="extra_local_tip",
                max_chars=160,
            )
            st.caption("Results stay on the last applied field until you press Apply.")
            submitted = st.form_submit_button(
                "Apply and compare",
                type="primary",
                use_container_width=True,
            )

        observed_yield = None
        if submitted:
            selected_yield = st.session_state.get("observed_yield", "").strip()
            try:
                observed_yield = float(selected_yield) if selected_yield else None
                if observed_yield is not None and (
                    observed_yield < 0 or not math.isfinite(observed_yield)
                ):
                    raise ValueError
            except ValueError:
                st.error("Enter a valid yield of 0 or more, or leave the field blank.")
                return st.session_state.get("applied_setup"), False

        if submitted and not priorities:
            st.error("Choose at least one priority to update the comparison.")
            return st.session_state.get("applied_setup"), False

        if submitted:
            place = session_place()
            if not place.has_point():
                st.error("Pin a field location before comparing rotations.")
                return st.session_state.get("applied_setup"), False
            farm = farm_from_place(
                place,
                name=st.session_state.get("field_name") or place.suggested_name(),
                crop=crop,
                soil_note=soil_note,
                local_tip=st.session_state.get("extra_local_tip", ""),
            )
            resolved_soil = (
                infer_soil_type(farm.soil_note)
                if soil_choice == "Auto (from site)"
                else soil_choice
            )
            setup = FarmSetup(
                farm=farm,
                crop=crop,
                priorities=tuple(priorities),
                farmer_name=st.session_state.get("farmer_name", ""),
                local_tip=st.session_state.get("extra_local_tip", ""),
                language=st.session_state.get("share_language", "en"),
                observed_yield_t_ha=observed_yield,
                soil_type=resolved_soil,
            )
            st.session_state["applied_setup"] = setup
            st.session_state["applied_climate_period"] = tuple(climate_period)
            save_field(setup)

        applied = st.session_state.get("applied_setup")
        if applied:
            place = session_place()
            moved = place.has_point() and (
                abs(place.lat - applied.farm.lat) > 0.0001
                or abs(place.lon - applied.farm.lon) > 0.0001
            )
            if (
                moved
                or st.session_state.get("field_crop", applied.crop) != applied.crop
                or tuple(st.session_state.get("farm_priorities", applied.priorities))
                != tuple(applied.priorities)
                or tuple(
                    st.session_state.get("climate_period", (POWER_YEAR_MIN, POWER_YEAR_MAX))
                )
                != tuple(st.session_state["applied_climate_period"])
            ):
                st.markdown(
                    '<p class="dirty">Field settings changed. Apply to refresh the comparison.</p>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("**Climate data**")
        packs = ", ".join(cached_points()) or "none yet"
        st.caption(
            f"NASA POWER daily agroclimatology, {POWER_YEAR_MIN}–{POWER_YEAR_MAX}. "
            "T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, RH2M · Community AG."
        )
        st.caption(f"Offline packs on this device: {packs}")
        if applied and is_cached(applied.farm.lat, applied.farm.lon):
            st.caption("Current field: saved for offline use.")
        elif applied:
            st.caption("Current field: will save a pack after the next successful live fetch.")

        with st.expander("Sharing and data options"):
            st.radio(
                "Who is using this?",
                ("Farmer", "Extension worker"),
                key="work_mode",
                horizontal=True,
            )
            st.selectbox(
                "Language for SMS / farmer card",
                list(LANGUAGES.keys()),
                format_func=lambda code: LANGUAGES[code],
                key="share_language",
            )
            st.toggle(
                "Use saved climate first",
                key="low_bandwidth",
                help="Loads a saved point quickly and works offline. Turn off to request a fresh NASA POWER series when you apply.",
            )

        profiles = load_roster()
        if st.session_state["work_mode"] == "Extension worker" and profiles:
            names = [item["farmer_name"] for item in profiles]
            chosen = st.selectbox("Load a saved farmer", ["—"] + names)
            if chosen != "—" and st.button("Open saved farmer"):
                record = next(item for item in profiles if item["farmer_name"] == chosen)
                farm = Farm(
                    name=record["farm_name"],
                    lat=record["lat"],
                    lon=record["lon"],
                    region=record.get("region", ""),
                    soil_note=record.get("soil_note", ""),
                    typical_crop=record["crop"],
                    local_tip=record.get("local_tip", ""),
                    agrozone=record.get("agrozone", ""),
                    continent=record.get("continent", ""),
                    country=record.get("country", ""),
                    country_code=record.get("country_code", ""),
                    state=record.get("state", ""),
                    lga=record.get("lga", ""),
                    area=record.get("area", ""),
                )
                st.session_state["applied_setup"] = FarmSetup(
                    farm=farm,
                    crop=record["crop"],
                    priorities=tuple(record["priorities"]),
                    farmer_name=record["farmer_name"],
                    local_tip=record.get("local_tip", ""),
                    language=st.session_state.get("share_language", "en"),
                    observed_yield_t_ha=record.get("observed_yield_t_ha"),
                )
                hydrate_location(farm)
                saved_yield = record.get("observed_yield_t_ha")
                st.session_state["observed_yield"] = "" if saved_yield is None else str(saved_yield)
                st.session_state["climate_request_attempted"] = False
                st.rerun()

    return st.session_state.get("applied_setup"), submitted


def render_farm_chip(setup: FarmSetup) -> None:
    farm = setup.farm
    pills = "".join(
        f'<span class="pill">{escape(item)}</span>' for item in setup.priorities
    )
    tip = setup.local_tip or farm.local_tip
    tip_html = (
        f'<div class="tip-box"><span class="eyebrow">Local knowledge</span>'
        f"<p>{escape(tip)}</p></div>"
        if tip
        else ""
    )
    who = setup.farmer_name.strip()
    yield_fact = (
        f"{setup.observed_yield_t_ha:g} t/ha"
        if setup.observed_yield_t_ha is not None
        else "Not provided"
    )
    st.markdown(
        f"""
        <div class="facts">
          <div class="fact"><span>Location</span><strong>{escape(farm.name)}</strong><small>{escape(farm.region)}</small></div>
          <div class="fact"><span>Current crop</span><strong>{escape(setup.crop)}</strong></div>
          <div class="fact"><span>Last harvest yield</span><strong>{escape(yield_fact)}</strong></div>
          <div class="fact note"><span>Soils / zone</span><strong>{escape(setup.soil_type)} · {escape(farm.agrozone or farm.soil_note)}</strong></div>
        </div>
        <div class="fact" style="padding:0 0 .8rem;border:0;">
          <span>Priorities{" · " + escape(who) if who else ""}</span>
          <div class="pills">{pills}</div>
        </div>
        {tip_html}
        """,
        unsafe_allow_html=True,
    )


def render_climate_snapshot(climate: ClimateSummary) -> None:
    st.markdown(
        f"""
        <div class="section-head stacked" id="climate">
          <h2>Climate snapshot</h2>
          <p>NASA POWER daily record for {climate.start_year}–{climate.end_year}
          ({climate.n_years} years). Rain change compares later years with earlier years.</p>
        </div>
        <p class="story">{escape(climate_story(climate))}</p>
        <div class="stat-grid">
          <div class="stat heat"><span class="k">Typical daily high</span>
            <span class="v">{climate.avg_tmax:.1f}°</span><span class="u">Celsius, year-round mean</span></div>
          <div class="stat rain"><span class="k">Rain in a typical year</span>
            <span class="v">{climate.annual_precip_mm:.0f}</span><span class="u">millimetres</span></div>
          <div class="stat gold"><span class="k">Is rain changing?</span>
            <span class="v">{climate.precip_trend_pct:+.0f}%</span><span class="u">later years vs earlier years</span></div>
          <div class="stat heat"><span class="k">Very hot days</span>
            <span class="v">{climate.heat_days_per_year:.0f}</span>
            <span class="u">above {HEAT_STRESS_C:.0f} °C each year</span></div>
          <div class="stat"><span class="k">Frost days</span>
            <span class="v">{climate.frost_days_per_year:.0f}</span>
            <span class="u">nights below 0 °C each year</span></div>
          {f'<div class="stat"><span class="k">Reference ET₀</span><span class="v">{climate.avg_et0_mm_day:.1f}</span><span class="u">mm/day, solar-based estimate</span></div>' if climate.avg_et0_mm_day > 0 else ''}
          {f'<div class="stat"><span class="k">Relative humidity</span><span class="v">{climate.avg_rh_pct:.0f}%</span><span class="u">daily mean at 2 m</span></div>' if climate.avg_rh_pct > 0 else ''}
          {f'<div class="stat rain"><span class="k">Moisture balance</span><span class="v">{climate.annual_water_balance_mm:+.0f}</span><span class="u">mm/yr (Rain − ET₀), {climate.dry_months_per_year:.1f} dry mo/yr</span></div>' if climate.avg_et0_mm_day > 0 else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_bar(label: str, value: int, color: str) -> str:
    width = max(8, int(value / 5 * 100))
    # Build a gradient fill for a richer look
    return (
        f'<div><div class="bar-lab"><span>{escape(label)}</span>'
        f'<span class="bar-val">{value}/5</span></div>'
        f'<div class="track"><div class="fill" style="width:{width}%;background:{color};"></div></div></div>'
    )


def render_rotation_card(col, result: RotationResult, is_top_match: bool) -> None:
    badge, fallback_tag = ROTATION_META.get(result.name, ("Option", result.tagline))
    badge_class = "badge gold" if is_top_match else "badge"
    # Determine accent class based on card type
    from rotation_explorer.config import ROTATION_CURRENT  # noqa: PLC0415
    if is_top_match:
        accent = "leader"
    elif result.name == ROTATION_CURRENT:
        accent = "accent-base"
    elif result.name == ROTATION_AGROFORESTRY:
        accent = "accent-agro"
    elif result.name == ROTATION_INTERCROP:
        accent = "accent-intercrop"
    elif result.water >= result.soil:
        accent = "accent-water"
    else:
        accent = "accent-soil"
    leader_label = "&nbsp;· Top match" if is_top_match else ""
    html = f"""
    <div class="rot-card {accent}">
      <span class="{badge_class}">{escape(badge)}{leader_label}</span>
      <h3>{escape(result.name)}</h3>
      <p class="tagline">{escape(result.tagline or fallback_tag)}</p>
      <div class="score-row">
        <span class="num">{result.score}</span>
        <span class="den">/ 5 overall score</span>
      </div>
      <div class="bars">
        {_score_bar("Water", result.water, "linear-gradient(90deg,#8ec7e2,#397f9e)")}
        {_score_bar("Soil", result.soil, "linear-gradient(90deg,#555,#1e1e1f)")}
        {_score_bar("Priorities", result.priority, "linear-gradient(90deg,#f7ca50,#e0a800)")}
      </div>
      <div class="seq">{escape(result.sequence)}</div>
      <div class="pills" style="margin-top:.7rem;">
        {"".join(f'<span class="lvl {cue.level}">{escape(cue.label)}: {escape(cue.value)}</span>' for cue in rotation_visuals(result))}
      </div>
    </div>
    """
    with col:
        st.markdown(html, unsafe_allow_html=True)
        with st.expander("Why, benefits, and risks", expanded=is_top_match):
            st.markdown("**Why this is suggested**")
            st.write(result.why)
            st.markdown("**Benefits**")
            for item in result.benefits:
                st.markdown(f"- {item}")
            st.markdown("**Risks / limitations**")
            for item in result.risks:
                st.markdown(f"- {item}")


def render_recommendation(
    rotations: list[RotationResult],
    setup: FarmSetup,
    timing: list[str],
) -> RotationResult:
    top_score = max(result.score for result in rotations)
    top_matches = [result for result in rotations if result.score == top_score]
    lead = top_matches[0]
    title = "Top match" if len(top_matches) == 1 else "Top matches"
    names = " and ".join(escape(result.name) for result in top_matches)
    st.markdown(
        f"""
        <div class="rec-banner" id="rotations">
          <strong>{title}: {names} · {top_score:.1f} / 5</strong>
          <p>{escape(action_line(setup.crop, lead, setup.farm.region))}</p>
          <p>{escape(timing[0] if timing else NEXT_STEPS[ROTATION_CURRENT])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return lead


def render_rotation_dashboard(rotations: list[RotationResult]) -> None:
    water_pct = int(WATER_WEIGHT * 100)
    soil_pct = int(SOIL_WEIGHT * 100)
    pri_pct = int(PRIORITY_WEIGHT * 100)
    sort_label = st.selectbox(
        "Sort rotations by",
        ("Overall fit", "Water resilience", "Soil health", "Priority match"),
        key="rotation_sort",
        help="Choose which score leads the comparison. The recommendation remains based on overall fit.",
    )
    sort_key = {
        "Overall fit": lambda item: item.score,
        "Water resilience": lambda item: item.water,
        "Soil health": lambda item: item.soil,
        "Priority match": lambda item: item.priority,
    }[sort_label]
    rotations = sorted(rotations, key=sort_key, reverse=True)
    top_score = max(result.score for result in rotations)
    def _chip(val: int | float, is_overall: bool = False) -> str:
        cls = "overall" if is_overall else ("hi" if val >= 4 else ("mid" if val >= 3 else "lo"))
        display = f"{val:.1f}" if is_overall else str(val)
        return f'<span class="score-chip {cls}">{display}</span>'

    rows = []
    for result in rotations:
        klass = "top" if result.score == top_score else ""
        rows.append(
            "<tr class='"
            f"{klass}'><td class='name'>{escape(result.name)}</td>"
            f"<td>{_chip(result.score, is_overall=True)}</td>"
            f"<td>{_chip(result.water)}</td>"
            f"<td>{_chip(result.soil)}</td>"
            f"<td>{_chip(result.priority)}</td></tr>"
        )
    st.markdown(
        f"""
        <div class="section-head stacked">
          <h2>Compare the three options</h2>
          <p>Overall score = {water_pct}% water + {soil_pct}% soil health +
          {pri_pct}% priority match. Scores run from 1–5. They do not predict yield.</p>
        </div>
        <p class="compare-hint">Swipe the table to compare every score.</p>
        <div class="compare-scroll" role="region" aria-label="Rotation score comparison" tabindex="0">
          <table class="compare">
            <thead><tr><th>Rotation</th><th>Overall</th><th>Water</th><th>Soil</th><th>Goals</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(rotations), gap="small")
    for col, result in zip(cols, rotations):
        render_rotation_card(col, result, is_top_match=result.score == top_score)


def render_risk_and_timing(
    flags: list[RiskFlag],
    timing: list[str],
    setup: FarmSetup,
) -> None:
    chips = "".join(
        f'<span class="lvl {flag.level}">{escape(flag.label)} · {escape(flag.detail)}</span>'
        for flag in flags
    )
    when = "".join(f"<li>{escape(item)}</li>" for item in timing)
    st.markdown(
        f"""
        <div class="section-head stacked">
          <h2>Risk flags and timing</h2>
          <p>Simple climate-risk flags for this point, plus when to cover the soil. Green / yellow / red is a conversation aid, not a forecast.</p>
        </div>
        <div>{chips}</div>
        <ul>{when}</ul>
        """,
        unsafe_allow_html=True,
    )


def render_share_kit(
    setup: FarmSetup,
    climate: ClimateSummary,
    rotations: list[RotationResult],
    flags: list[RiskFlag],
    timing: list[str],
) -> None:
    top = max(rotations, key=lambda item: item.score)
    lang = st.session_state.get("share_language") or setup.language or "en"
    sms = sms_summary(setup, top, lang)
    card = farmer_card_html(setup, climate, top, flags, timing, lang)
    report = comparison_report(setup, climate, rotations)
    csv_data = rotation_csv_report(setup, climate, rotations)
    slug = setup.farm.name.lower().replace(" ", "-")
    st.markdown(
        """
        <div class="section-head stacked">
          <h2>Share offline</h2>
          <p>Copy an SMS for a basic phone, or download a one-page farmer card you can print or send without the app.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="sms-box">{escape(sms)}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("SMS / USSD text", sms, file_name=f"{slug}-sms.txt", mime="text/plain")
    with c2:
        st.download_button(
            "Printable farmer card",
            card,
            file_name=f"{slug}-farmer-card.html",
            mime="text/html",
        )
    with c3:
        st.download_button(
            "Full comparison notes",
            report,
            file_name=f"rotation-explorer-{slug}.txt",
            mime="text/plain",
        )
    with c4:
        st.download_button(
            "Download CSV",
            csv_data,
            file_name=f"rotation-explorer-{slug}.csv",
            mime="text/csv",
        )


def render_extension_roster(setup: FarmSetup, top: RotationResult) -> None:
    if st.session_state.get("work_mode") != "Extension worker":
        return
    st.markdown(
        """
        <div class="section-head stacked">
          <h2>Extension roster</h2>
          <p>Save this comparison under a farmer name, then batch-download SMS lines for the cooperative.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Save this farmer to the roster"):
        name = setup.farmer_name.strip() or setup.farm.name
        record = {
            "farmer_name": name,
            "farm_name": setup.farm.name,
            "region": setup.farm.region,
            "lat": setup.farm.lat,
            "lon": setup.farm.lon,
            "crop": setup.crop,
            "priorities": list(setup.priorities),
            "local_tip": setup.local_tip or setup.farm.local_tip,
            "soil_note": setup.farm.soil_note,
            "agrozone": setup.farm.agrozone,
            "continent": setup.farm.continent,
            "country": setup.farm.country,
            "country_code": setup.farm.country_code,
            "state": setup.farm.state,
            "lga": setup.farm.lga,
            "area": setup.farm.area,
            "observed_yield_t_ha": setup.observed_yield_t_ha,
            "top_rotation": top.name,
            "score": top.score,
            "sms": sms_summary(setup, top, setup.language),
        }
        save_roster_entry(record)
        st.toast(f"Saved {name} to this app.")
        st.rerun()

    profiles = load_roster()
    if not profiles:
        st.caption("No farmers saved yet. Apply a comparison, then save.")
        return
    st.dataframe(
        [
            {
                "Farmer": item["farmer_name"],
                "Place": item["farm_name"],
                "Crop": item["crop"],
                "Top rotation": item["top_rotation"],
                "Score": item["score"],
            }
            for item in profiles
        ],
        hide_index=True,
        width="stretch",
    )
    batch = "\n\n".join(item["sms"] for item in profiles)
    st.download_button(
        "Download all SMS lines",
        batch,
        file_name="fieldshift-roster-sms.txt",
        mime="text/plain",
    )


def render_charts(daily: pd.DataFrame, monthly: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="section-head stacked">
          <h2>Patterns in the record</h2>
          <p>Heat and rainfall from the same NASA POWER series used in scoring.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    variables = st.multiselect(
        "Climate variables",
        ("Rainfall", "Maximum temperature", "Mean temperature", "Minimum temperature"),
        default=("Maximum temperature", "Rainfall"),
        key="climate_variables",
        help="Choose which measures to plot across the selected climate period.",
    )
    left, right = st.columns((1.3, 1), gap="large")
    with left:
        if variables:
            st.plotly_chart(
                climate_trend_figure(monthly, tuple(variables)),
                width="stretch",
                config=PLOTLY_CONFIG,
            )
        else:
            st.caption("Choose at least one climate variable to draw the monthly chart.")
    with right:
        st.caption("Year-by-year rain and heat")
        st.plotly_chart(
            annual_bars_figure(daily),
            width="stretch",
            config=PLOTLY_CONFIG,
        )
    if "WATER_BALANCE_MM" in monthly.columns:
        st.caption("Monthly moisture balance (Rainfall − ET₀): green = surplus, amber = deficit")
        st.plotly_chart(
            water_balance_figure(monthly),
            width="stretch",
            config=PLOTLY_CONFIG,
        )


def render_method_and_glossary() -> None:
    st.markdown(
        """
        <div class="section-head stacked" id="method">
          <h2>How the comparison works</h2>
        </div>
        <div class="method-grid">
          <div class="method">
            <h4>What we score</h4>
            <ul>
              <li><strong>Water resilience</strong> — cover and drought-tolerant options rise when POWER shows heat or low / declining rain.</li>
              <li><strong>Soil health</strong> — legumes and cover crops rank above a simple continuous cereal.</li>
              <li><strong>Priority match</strong> — extra weight for water savings, organic matter, nitrogen, erosion, or forage.</li>
            </ul>
          </div>
          <div class="method">
            <h4>What we do not claim</h4>
            <ul>
              <li>No SMAP soil-moisture or ECOSTRESS tiles in this build (POWER is the live NASA layer).</li>
              <li>No field-level soils, irrigation, or prices.</li>
              <li>No replacement for extension services, soil tests, or your experience.</li>
            </ul>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What do these terms mean?"):
        st.markdown(
            """
            - **NASA POWER** — NASA's Prediction Of Worldwide Energy Resources.
              Gridded weather and agroclimate fields. Field summaries use the
              agriculture daily point API; the optional area map uses the daily
              regional endpoint and preserves the source grid cells.
            - **T2M / T2M_MAX / T2M_MIN** — Average, maximum, and minimum
              2-meter air temperature (°C). High **T2M_MAX** is a simple heat-stress flag.
            - **PRECTOTCORR** — Bias-corrected total precipitation (mm/day).
              We sum it to monthly and annual rainfall.
            - **Heat-stress days** — Days with max temperature above 32 °C.
              A threshold for illustration, not a crop-specific damage model.
            - **Planting-window screen** — A comparison of historical 2–6 month
              rainfall windows and dry spells. It helps shortlist timing to discuss;
              it is not a forecast or a crop-stage model.
            - **Frost days** — Days with min temperature below 0 °C.
            - **NDVI** — Greenness index from satellites (Landsat/MODIS). Not
              fetched in this prototype.
            - **Soil moisture (SMAP) / water stress (ECOSTRESS)** — NASA products
              planned for fusion; this build uses POWER temperature and rain.
            - **Soil moisture anomaly** — How wet or dry soil is versus a
              long-term average for that week or month.
            - **Evapotranspiration** — Water leaving the field via soil
              evaporation and plant transpiration.
            """
        )

    from rotation_explorer.site import render_footer

    render_footer()
