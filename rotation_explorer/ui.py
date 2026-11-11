"""Streamlit presentation layer. Keep widgets here, domain logic elsewhere."""

from __future__ import annotations

from html import escape

import pandas as pd
import pydeck as pdk
import streamlit as st

from rotation_explorer.charts import annual_bars_figure, climate_trend_figure
from rotation_explorer.cache import cached_points, is_cached
from rotation_explorer.config import (
    CROPS,
    DEFAULT_PRIORITIES,
    FARMS_BY_NAME,
    HEAT_STRESS_C,
    LANGUAGES,
    PRIORITIES,
    PRIORITY_WEIGHT,
    ROTATION_CURRENT,
    ROTATION_DROUGHT,
    ROTATION_LEGUME,
    SOIL_WEIGHT,
    WATER_WEIGHT,
)
from rotation_explorer.climate import climate_story
from rotation_explorer.insights import (
    RiskFlag,
    action_line,
    farmer_card_html,
    rotation_visuals,
    sms_summary,
)
from rotation_explorer.models import ClimateSummary, Farm, FarmSetup, RotationResult
from rotation_explorer.report import comparison_report

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
}

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}

ROTATION_META = {
    ROTATION_CURRENT: ("Baseline", "Keep what already works"),
    ROTATION_DROUGHT: ("Water", "Cover soil, ease demand"),
    ROTATION_LEGUME: ("Soil", "Fix nitrogen, build matter"),
}
CUSTOM_LOCATION = "Enter coordinates"

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;500;600&display=swap');
:root { --canvas:#f5f5f5; --cream:#f8f4e6; --paper:#fff; --mist:#e9e9e9; --ink:#1e1e1f; --carbon:#000; --blue:#8ec7e2; --yellow:#f7ca50; --muted:#626263; --line:#d8d8d8; --body:'DM Sans',Inter,ui-sans-serif,system-ui,sans-serif; --mono:'DM Mono',ui-monospace,monospace; }
html,body,[class*="css"] { font-family:var(--body); color:var(--ink); }
.stApp { background:var(--canvas); color:var(--ink); }
.block-container { max-width:100%; padding:1.2rem clamp(1.2rem,3.2vw,3.5rem) 4rem; }
#MainMenu,footer,.stDeployButton,div[data-testid="stToolbar"],.stAppDeployButton { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
section[data-testid="stSidebar"] { background:var(--cream); border-right:1px solid var(--line); }
section[data-testid="stSidebar"]>div { padding:1.25rem 1rem 2rem; }
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3 { color:var(--carbon); letter-spacing:-.045em; }
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] [data-testid="stCaption"] { color:var(--muted); }
section[data-testid="stSidebar"] hr { border-color:var(--line); }
section[data-testid="stSidebar"] [data-baseweb="tag"],section[data-testid="stSidebar"] [data-baseweb="tag"] *,section[data-testid="stSidebar"] [data-slot="tag"],section[data-testid="stSidebar"] [data-slot="tag"] *,section[data-testid="stSidebar"] [class*="tag"] { background:var(--blue)!important; color:var(--carbon)!important; border-radius:22px!important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:var(--ink)!important; font-size:.9rem; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height:1.45; }
.topbar { display:flex; align-items:center; justify-content:space-between; gap:1.5rem; padding:.65rem .85rem; margin-bottom:2.7rem; background:var(--mist); border-radius:3px; }
.brand { display:flex; align-items:baseline; gap:.65rem; color:var(--carbon); font-size:1rem; font-weight:600; letter-spacing:-.05em; text-decoration:none; }
.brand small { font-family:var(--mono); font-size:.65rem; font-weight:400; letter-spacing:.015em; text-transform:uppercase; color:var(--muted); }
.toplinks { display:flex; align-items:center; gap:clamp(.75rem,2vw,2rem); }
.toplinks a { color:var(--ink)!important; text-decoration:none!important; font-family:var(--mono); font-size:.7rem; letter-spacing:.025em; }
.toplinks a:hover { text-decoration:underline; text-underline-offset:4px; }
.topbar .brand,.topbar .brand:visited { color:var(--carbon)!important; text-decoration:none!important; }
.pill-link { display:inline-flex; align-items:center; gap:.75rem; padding:.55rem .65rem .55rem .9rem; border-radius:22px; background:var(--blue); color:var(--carbon)!important; text-decoration:none!important; font-size:.83rem; transition:background .15s ease; }
.pill-link:hover { background:#a6d5e9; }
.pill-link span { display:inline-grid; place-items:center; width:1.45rem; height:1.45rem; background:rgba(255,255,255,.65); border-radius:50%; font-size:1rem; line-height:1; }
.hero { display:grid; grid-template-columns:minmax(0,1fr) minmax(15rem,.52fr); gap:2rem; align-items:end; padding:0 0 2rem; border-bottom:1px solid var(--line); }
.kicker,.eyebrow { display:block; color:var(--muted); font-family:var(--mono); font-size:.7rem; line-height:1.4; letter-spacing:.045em; text-transform:uppercase; }
.kicker { margin:0 0 .85rem; }
.hero h1 { max-width:13ch; margin:0; color:var(--carbon); font-size:clamp(2.6rem,5.5vw,4.7rem); font-weight:400; line-height:.98; letter-spacing:-.065em; text-wrap:balance; }
.lede { max-width:41rem; margin:1rem 0 0; color:#454546; font-size:1.05rem; line-height:1.5; letter-spacing:-.025em; }
.hero-aside { padding:1rem 0 0 1.2rem; border-left:1px solid var(--line); }
.live-pill { display:inline-flex; align-items:center; gap:.5rem; padding:.42rem .72rem; border-radius:22px; background:var(--yellow); color:var(--carbon); font-family:var(--mono); font-size:.68rem; letter-spacing:.01em; }
.live-dot { width:7px; height:7px; border-radius:50%; background:var(--carbon); }
.quiet { margin:.8rem 0 0; color:var(--muted); font-size:.85rem; line-height:1.45; }
.hero-nav { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1.2rem; }
.hero-nav a { display:inline-flex; align-items:center; gap:.45rem; padding:.58rem .7rem .58rem .9rem; background:var(--blue); color:var(--carbon); border-radius:22px; font-size:.8rem; text-decoration:none; }
.hero-nav a span { font-size:1.1rem; }
.facts { display:grid; grid-template-columns:1fr 1fr 1.35fr; gap:0; margin:0 0 4rem; padding:.95rem 0 1.1rem; border-bottom:1px solid var(--line); }
.fact { padding:.15rem 1.1rem .15rem 0; }
.fact+.fact { padding-left:1.1rem; border-left:1px solid var(--line); }
.fact span { display:block; margin-bottom:.38rem; color:var(--muted); font-family:var(--mono); font-size:.67rem; letter-spacing:.04em; text-transform:uppercase; }
.fact strong { display:block; color:var(--ink); font-size:1rem; font-weight:500; letter-spacing:-.03em; line-height:1.4; }
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
.rot-card { height:100%; min-height:18.3rem; padding:1rem 1rem .9rem; background:var(--paper); border:1px solid var(--line); border-radius:22px; }
.rot-card.leader { border-color:var(--carbon); }
.badge { display:inline-block; padding:.35rem .62rem; border-radius:22px; background:var(--mist); color:var(--ink); font-family:var(--mono); font-size:.64rem; line-height:1.3; letter-spacing:.015em; }
.badge.gold { background:var(--yellow); color:var(--carbon); }
.rot-card h3 { max-width:16ch; margin:.85rem 0 .25rem; color:var(--carbon); font-size:1.32rem; font-weight:400; line-height:1.15; letter-spacing:-.055em; text-wrap:balance; }
.tagline { min-height:2.3rem; margin:0 0 1.1rem; color:var(--muted); font-size:.84rem; line-height:1.4; }
.score-row { display:flex; align-items:baseline; gap:.4rem; margin-bottom:1rem; }
.score-row .num { color:var(--carbon); font-size:2.65rem; font-weight:400; line-height:1; letter-spacing:-.065em; }
.score-row .den { color:var(--muted); font-size:.78rem; }
.bars { display:grid; gap:.55rem; margin-bottom:1rem; }
.bar-lab { display:flex; justify-content:space-between; margin-bottom:.2rem; color:var(--muted); font-size:.73rem; }
.track { height:5px; overflow:hidden; border-radius:10px; background:var(--mist); }
.fill { height:100%; border-radius:10px; }
.seq { min-height:2.5rem; padding:.55rem .65rem; border-radius:14px; background:var(--cream); color:var(--ink); font-size:.77rem; line-height:1.4; }
.result-note,.rec-banner { margin:.2rem 0 1.1rem; padding:1.1rem 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); color:var(--ink); }
.rec-banner { margin:0 0 1.6rem; }
.result-note strong,.rec-banner strong { font-size:1.02rem; font-weight:500; letter-spacing:-.03em; }
.result-note p,.rec-banner p { margin:.35rem 0 0; color:var(--muted); font-size:.88rem; line-height:1.5; }
.steps { display:flex; flex-wrap:wrap; gap:.55rem; margin:1.1rem 0 0; }
.step { display:inline-flex; align-items:center; gap:.45rem; padding:.4rem .7rem; border-radius:22px; background:var(--mist); color:var(--ink); font-size:.8rem; }
.step b { font-family:var(--mono); font-size:.72rem; font-weight:500; color:var(--muted); }
.story { margin:0 0 1.6rem; padding:1rem 1.1rem; background:var(--cream); border-radius:18px; color:var(--ink); font-size:.95rem; line-height:1.5; }
.pills { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.45rem; }
.pill { display:inline-block; padding:.28rem .6rem; border-radius:22px; background:var(--blue); color:var(--carbon); font-size:.75rem; }
.compare { width:100%; border-collapse:collapse; margin:0 0 1.1rem; font-size:.88rem; }
.compare th { text-align:left; font-family:var(--mono); font-size:.64rem; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); font-weight:500; padding:.45rem .5rem .45rem 0; border-bottom:1px solid var(--line); }
.compare td { padding:.7rem .5rem .7rem 0; border-bottom:1px solid var(--line); vertical-align:middle; }
.compare tr.top td { background:linear-gradient(90deg, rgba(247,202,80,.22), transparent 70%); }
.compare .name { font-weight:500; color:var(--carbon); }
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
div[data-testid="stExpander"] { border:1px solid var(--line); border-radius:18px; background:var(--paper); }
div[data-testid="stExpander"] summary p { color:var(--ink); font-size:.88rem; }
div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] { color:var(--muted); line-height:1.5; }
.method-grid { display:grid; grid-template-columns:1fr 1fr; gap:2rem; padding:1rem 0 1.3rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.method h4 { margin:0 0 .55rem; color:var(--ink); font-size:1.02rem; font-weight:500; letter-spacing:-.035em; }
.method ul { margin:0; padding-left:1.1rem; color:var(--muted); font-size:.87rem; line-height:1.5; }.method li { margin:.35rem 0; }.method strong { color:var(--ink); font-weight:500; }
.foot { margin-top:1.7rem; padding-top:1rem; border-top:1px solid var(--line); color:var(--muted); font-family:var(--mono); font-size:.68rem; line-height:1.5; }
div[data-testid="stPlotlyChart"] { padding:.25rem; border-radius:22px; background:var(--paper); }
div[data-testid="stPlotlyChart"] iframe { border-radius:18px; }
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div { border-color:#bdbdbd; border-radius:14px; }
button[kind="secondary"],.stButton button { border:0; border-radius:22px; background:var(--blue); color:var(--carbon); }
button[kind="secondary"]:hover,.stButton button:hover { border:0; background:#a6d5e9; color:var(--carbon); }
:focus-visible { outline:2px solid var(--carbon); outline-offset:3px; }
@media(max-width:1000px) { .hero { grid-template-columns:1fr; gap:1rem; }.hero-aside { max-width:40rem; padding:.8rem 0 0; border-left:0; }.stat-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }.stat:nth-child(4) { border-left:0; padding-left:0; } }
@media(max-width:720px) { .block-container { padding-left:1rem; padding-right:1rem; }.topbar { margin-bottom:1.7rem; }.toplinks a:not(.pill-link) { display:none; }.brand small { display:none; }.facts { grid-template-columns:1fr; margin-bottom:2.3rem; }.fact,.fact+.fact { padding:.65rem 0; border-left:0; }.fact+.fact { border-top:1px solid var(--line); }.stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.stat,.stat+.stat { padding:.8rem .65rem .8rem 0; border-left:0; }.stat:nth-child(even) { padding-left:.7rem; border-left:1px solid var(--line); }.method-grid { grid-template-columns:1fr; gap:1.2rem; }.section-head { display:block; margin-top:2.8rem; }.hero h1 { font-size:clamp(2.7rem,12vw,4rem); } }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { scroll-behavior:auto!important; transition:none!important; } }
"""


def inject_css() -> None:
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        f"""
        <nav class="topbar" aria-label="Main navigation">
          <a class="brand" href="#overview">FIELD SHIFT <small>Rotation Explorer</small></a>
          <div class="toplinks">
            <a href="#field">FIELD</a>
            <a href="#climate">CLIMATE</a>
            <a href="#rotations">ROTATIONS</a>
            <a href="#method">HOW IT WORKS</a>
            <a class="pill-link" href="#rotations">Explore rotations <span>↗</span></a>
          </div>
        </nav>
        <div class="hero">
          <div>
            <div class="kicker">Crop rotation, with local climate in context</div>
            <h1 id="overview">Compare rotations for the field you farm.</h1>
            <p class="lede">Set your field, crop, and goals. Then compare three rotations against recent NASA weather — starting with a recommended conversation, not a prescription.</p>
            <div class="steps" aria-label="How to use Rotation Explorer">
              <span class="step"><b>1</b> Choose a field</span>
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


def render_sidebar() -> tuple[FarmSetup | None, bool]:
    default_farm = next(iter(FARMS_BY_NAME.values()))
    default_setup = FarmSetup(
        farm=default_farm,
        crop=default_farm.typical_crop,
        priorities=DEFAULT_PRIORITIES,
    )
    st.session_state.setdefault("applied_setup", default_setup)
    st.session_state.setdefault("location_choice", default_farm.name)
    st.session_state.setdefault("last_location_choice", default_farm.name)
    st.session_state.setdefault("field_crop", default_setup.crop)
    st.session_state.setdefault("farm_priorities", list(DEFAULT_PRIORITIES))
    st.session_state.setdefault("custom_farm_name", "")
    st.session_state.setdefault("custom_lat", 10.5)
    st.session_state.setdefault("custom_lon", -1.2)
    st.session_state.setdefault("custom_soil_note", "")
    st.session_state.setdefault("work_mode", "Farmer")
    st.session_state.setdefault("share_language", "en")
    st.session_state.setdefault("low_bandwidth", False)
    st.session_state.setdefault("farmer_name", "")
    st.session_state.setdefault("extra_local_tip", "")
    st.session_state.setdefault("profiles", [])

    with st.sidebar:
        st.markdown("### Set your field context")
        st.caption("Choose a demo site or use coordinates for your own field.")
        location_choice = st.selectbox(
            "Location",
            [*FARMS_BY_NAME, CUSTOM_LOCATION],
            key="location_choice",
        )
        if location_choice != st.session_state["last_location_choice"]:
            if location_choice in FARMS_BY_NAME:
                st.session_state["field_crop"] = FARMS_BY_NAME[location_choice].typical_crop
            else:
                st.session_state["field_crop"] = st.session_state["applied_setup"].crop
            st.session_state["last_location_choice"] = location_choice

        applied = st.session_state["applied_setup"]
        pending_location = (
            CUSTOM_LOCATION
            if applied.farm.region == "Custom coordinates"
            else applied.farm.name
        )
        dirty = location_choice != pending_location
        if dirty:
            st.markdown(
                '<p class="dirty">Location changed. Apply to refresh climate and scores for this field.</p>',
                unsafe_allow_html=True,
            )

        submitted = False
        with st.form("field_setup", border=False):
            if location_choice == CUSTOM_LOCATION:
                farm_name = st.text_input(
                    "Farm or area name",
                    placeholder="e.g. Kano North",
                    key="custom_farm_name",
                    max_chars=60,
                )
                latitude_col, longitude_col = st.columns(2)
                with latitude_col:
                    latitude = st.number_input(
                        "Latitude",
                        min_value=-90.0,
                        max_value=90.0,
                        step=0.1,
                        format="%.2f",
                        key="custom_lat",
                        help="Decimal degrees, from −90 to 90.",
                    )
                with longitude_col:
                    longitude = st.number_input(
                        "Longitude",
                        min_value=-180.0,
                        max_value=180.0,
                        step=0.1,
                        format="%.2f",
                        key="custom_lon",
                        help="Decimal degrees, from −180 to 180.",
                    )
                soil_note = st.text_input(
                    "Soil notes (optional)",
                    placeholder="e.g. sandy loam, low organic matter",
                    key="custom_soil_note",
                    max_chars=120,
                )
                farm = Farm(
                    name=farm_name.strip() or "Custom field",
                    lat=latitude,
                    lon=longitude,
                    region="Custom coordinates",
                    soil_note=soil_note.strip()
                    or "Field-specific soil information has not been provided.",
                    typical_crop=st.session_state["field_crop"],
                )
            else:
                farm = FARMS_BY_NAME[location_choice]
                st.caption(f"{farm.region} · {farm.lat:.2f}°, {farm.lon:.2f}°")

            crop = st.selectbox("Current main crop", list(CROPS), key="field_crop")
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

        if submitted and not priorities:
            st.error("Choose at least one priority to update the comparison.")
            return None, False

        if submitted:
            st.session_state["applied_setup"] = FarmSetup(
                farm=farm,
                crop=crop,
                priorities=tuple(priorities),
                farmer_name=st.session_state.get("farmer_name", ""),
                local_tip=st.session_state.get("extra_local_tip", ""),
                language=st.session_state.get("share_language", "en"),
            )

        st.markdown("---")
        st.markdown("**Climate data**")
        packs = ", ".join(cached_points()) or "none yet"
        st.caption(
            "NASA POWER daily agroclimatology, 2018–2025. "
            "T2M, T2M_MAX, T2M_MIN, PRECTOTCORR · Community AG."
        )
        st.caption(f"Offline packs on this device: {packs}")
        applied = st.session_state["applied_setup"]
        if is_cached(applied.farm.lat, applied.farm.lon):
            st.caption("Current field: saved for offline use.")
        else:
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
                "Low-bandwidth: use saved weather if available",
                key="low_bandwidth",
            )

        profiles = st.session_state.get("profiles", [])
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
                )
                st.session_state["applied_setup"] = FarmSetup(
                    farm=farm,
                    crop=record["crop"],
                    priorities=tuple(record["priorities"]),
                    farmer_name=record["farmer_name"],
                    local_tip=record.get("local_tip", ""),
                    language=st.session_state.get("share_language", "en"),
                )
                st.session_state["climate_request_attempted"] = False
                st.rerun()

    return st.session_state["applied_setup"], submitted


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
    st.markdown(
        f"""
        <div class="facts">
          <div class="fact"><span>Location</span><strong>{escape(farm.name)}</strong></div>
          <div class="fact"><span>Current crop</span><strong>{escape(setup.crop)}</strong></div>
          <div class="fact note"><span>Soils / zone</span><strong>{escape(farm.agrozone or farm.soil_note)}</strong></div>
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
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_bar(label: str, value: int, color: str) -> str:
    width = max(8, int(value / 5 * 100))
    return (
        f'<div><div class="bar-lab"><span>{escape(label)}</span>'
        f"<span>{value}/5</span></div>"
        f'<div class="track"><div class="fill" style="width:{width}%;background:{color};"></div></div></div>'
    )


def render_rotation_card(col, result: RotationResult, is_top_match: bool) -> None:
    badge, fallback_tag = ROTATION_META.get(result.name, ("Option", result.tagline))
    badge_class = "badge gold" if is_top_match else "badge"
    leader_class = "rot-card leader" if is_top_match else "rot-card"
    leader_label = " · Top match" if is_top_match else ""
    html = f"""
    <div class="{leader_class}">
      <span class="{badge_class}">{escape(badge)}{leader_label}</span>
      <h3>{escape(result.name)}</h3>
      <p class="tagline">{escape(result.tagline or fallback_tag)}</p>
      <div class="score-row"><span class="num">{result.score}</span>
        <span class="den">/ 5 overall score</span></div>
      <div class="bars">
        {_score_bar("Water", result.water, "#8ec7e2")}
        {_score_bar("Soil", result.soil, "#1e1e1f")}
        {_score_bar("Priorities", result.priority, "#f7ca50")}
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
    top_score = max(result.score for result in rotations)
    rows = []
    for result in rotations:
        klass = "top" if result.score == top_score else ""
        rows.append(
            "<tr class='"
            f"{klass}'><td class='name'>{escape(result.name)}</td>"
            f"<td>{result.score:.1f}</td><td>{result.water}</td>"
            f"<td>{result.soil}</td><td>{result.priority}</td></tr>"
        )
    st.markdown(
        f"""
        <div class="section-head stacked">
          <h2>Compare the three options</h2>
          <p>Overall score = {water_pct}% water + {soil_pct}% soil health +
          {pri_pct}% priority match. Scores run from 1–5. They do not predict yield.</p>
        </div>
        <table class="compare" aria-label="Rotation score comparison">
          <thead><tr><th>Rotation</th><th>Overall</th><th>Water</th><th>Soil</th><th>Goals</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(3, gap="small")
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
    c1, c2, c3 = st.columns(3)
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
            "top_rotation": top.name,
            "score": top.score,
            "sms": sms_summary(setup, top, setup.language),
        }
        profiles = [
            item
            for item in st.session_state.get("profiles", [])
            if item["farmer_name"] != name
        ]
        profiles.append(record)
        st.session_state["profiles"] = profiles
        st.toast(f"Saved {name} on this device.")
        st.rerun()

    profiles = st.session_state.get("profiles", [])
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
    left, right = st.columns((1.3, 1), gap="large")
    with left:
        st.plotly_chart(
            climate_trend_figure(monthly),
            width="stretch",
            config=PLOTLY_CONFIG,
        )
    with right:
        st.caption("Year-by-year rain and heat")
        st.plotly_chart(
            annual_bars_figure(daily),
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
              Gridded weather and agroclimate fields. We use the agriculture
              community daily point API (no login for this public query).
            - **T2M / T2M_MAX / T2M_MIN** — Average, maximum, and minimum
              2-meter air temperature (°C). High **T2M_MAX** is a simple heat-stress flag.
            - **PRECTOTCORR** — Bias-corrected total precipitation (mm/day).
              We sum it to monthly and annual rainfall.
            - **Heat-stress days** — Days with max temperature above 32 °C.
              A threshold for illustration, not a crop-specific damage model.
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

    st.markdown(
        '<p class="foot">Rotation Explorer · NASA Space Apps Challenge 2026 · '
        "Data courtesy of NASA Langley Research Center POWER Project.</p>",
        unsafe_allow_html=True,
    )
