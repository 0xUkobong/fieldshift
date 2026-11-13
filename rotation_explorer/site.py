"""About, disclaimer, privacy, and data-attribution pages."""

from __future__ import annotations

import streamlit as st

from rotation_explorer.config import DISCLAIMER
from rotation_explorer.seo import (
    ABOUT,
    DATA,
    DISCLAIMER as DISCLAIMER_SEO,
    PRIVACY,
    PageSEO,
    app_route,
    header_mark_src,
    inject_seo,
    page_icon,
)

UPDATED = "12 November 2026"


def render_legal_nav(current: str = "") -> None:
    explorer_url = app_route("/")
    about_url = app_route("/About")
    disclaimer_url = app_route("/Disclaimer")
    privacy_url = app_route("/Privacy")
    st.markdown(
        f"""
        <nav class="topbar" aria-label="Main navigation">
          <a class="brand" href="{explorer_url}" target="_self"><img class="brand-mark" src="{header_mark_src()}" width="36" height="36" alt="">FIELD SHIFT <small>Rotation Explorer</small></a>
          <div class="toplinks">
            <a href="{explorer_url}" target="_self">EXPLORER</a>
            <a href="{about_url}" target="_self">ABOUT</a>
            <a href="{disclaimer_url}" target="_self">DISCLAIMER</a>
            <a href="{privacy_url}" target="_self">PRIVACY</a>
            <a class="pill-link" href="{explorer_url}" target="_self">Open explorer <span>↗</span></a>
          </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
    _ = current


def render_footer() -> None:
    about, disclaimer, privacy, data, copy = st.columns([0.9, 1.15, 0.9, 1.4, 3.4])
    with about:
        st.page_link("pages/1_About.py", label="About")
    with disclaimer:
        st.page_link("pages/2_Disclaimer.py", label="Disclaimer")
    with privacy:
        st.page_link("pages/3_Privacy.py", label="Privacy")
    with data:
        st.page_link("pages/4_Data_sources.py", label="Data & licenses")
    with copy:
        st.caption(
            "Rotation Explorer · NASA Space Apps Challenge 2026 · "
            "Data courtesy of NASA Langley Research Center POWER Project."
        )


def start_legal_page(title: str, current: str, page: PageSEO | None = None) -> None:
    st.set_page_config(
        page_title=f"{title} · Field Shift",
        page_icon=page_icon(),
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    seo_pages = {
        "about": ABOUT,
        "disclaimer": DISCLAIMER_SEO,
        "privacy": PRIVACY,
        "data": DATA,
    }
    inject_seo(page or seo_pages.get(current, ABOUT))
    from rotation_explorer.ui import inject_css

    inject_css()
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none!important;}</style>",
        unsafe_allow_html=True,
    )
    render_legal_nav(current)


def render_about() -> None:
    st.markdown(
        """
        <div class="hero">
          <div>
            <div class="kicker">NASA Space Apps Challenge 2026</div>
            <h1 id="overview">A field tool, not a sample farm.</h1>
            <p class="lede">Field Shift · Rotation Explorer helps farmers and extension workers compare crop rotations using NASA weather for the place they actually farm.</p>
          </div>
          <div class="hero-aside">
            <div class="live-pill"><span class="live-dot"></span> Challenge: Field Shift</div>
            <p class="quiet">Built for Adapting Farms with NASA Data. Scores are rule-based and explained in plain language.</p>
          </div>
        </div>
        <div class="legal">
          <h2>Who it is for</h2>
          <p>Smallholders, farm families, and extension workers who want a starting point for a rotation conversation. You name the field, the current crop, and what matters on that land. The app does not assume you are in Iowa, California, or any other demo site.</p>
          <h2>What it does</h2>
          <p>It locates a real field (continent, country, state or province, local government or county, and area), loads NASA POWER daily weather for that pin, and compares rotation options: keep the current sequence, add drought-tolerant cover, bring in a nitrogen-fixing legume, integrate trees, or intercrop. Historical rainfall timing and dry-spell patterns help you shortlist a season window for the selected crop.</p>
          <p>Each option gets a transparent 1–5 score for water resilience, soil-health potential, and how well it matches the goals you typed. You can download an SMS-length note or a printable farmer card to share offline.</p>
          <h2>What it does not do</h2>
          <p>It does not replace an agronomist, a soil test, market prices, or what you see in the field. It does not send SMS by itself and does not create user accounts. Saved fields are stored by the app service; on fieldshift.cloud, that means the server hosting the service.</p>
          <h2>How to use it</h2>
          <p>1. Pin the field. 2. Set crop, soil texture, and goals. 3. Apply and compare. Then check the recommendation with local advice before you change seed, labour, or land use.</p>
          <h2>Questions people ask</h2>
          <p><strong>Does this replace an agronomist?</strong> No. It is a starting point for a conversation with local advice.</p>
          <p><strong>Which NASA data is used?</strong> NASA POWER daily agroclimatology for the pin you set — temperature, rainfall, humidity, and solar.</p>
          <p><strong>Where is my farm record stored?</strong> In the local database on the machine hosting the Field Shift service. On fieldshift.cloud, the server operator can access these files.</p>
          <p><strong>Does NASA endorse the rotation it ranks first?</strong> No. POWER supplies weather. The scores are this project’s rules.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()


def render_disclaimer() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div>
            <div class="kicker">Legal · Updated {UPDATED}</div>
            <h1 id="overview">Disclaimer and terms of use</h1>
            <p class="lede">{DISCLAIMER}</p>
          </div>
        </div>
        <div class="legal">
          <h2>Decision support, not a prescription</h2>
          <p>Rotation Explorer is an exploratory tool. Scores, flags, timing notes, and share cards are conversation aids. They are not agronomic, legal, financial, or safety advice. You (and your local advisers) remain responsible for what you plant, when you plant, and how you manage the field.</p>
          <h2>Limits of the data</h2>
          <p>Climate values come from NASA POWER, a gridded satellite-and-model product, not a weather station in your plot. A pin on the map is still coarser than a ridge, a swamp, or an irrigated bed. Place names come from OpenStreetMap and may be incomplete or misspelled. Soil texture in this build is what you enter, not a lab test or a soil map.</p>
          <h2>No NASA endorsement of recommendations</h2>
          <p>This project uses publicly documented NASA POWER data. NASA, the Space Apps Challenge, and the POWER project do not endorse the rotation scores, sequences, or any farm decision you make with this app.</p>
          <h2>No warranty</h2>
          <p>The software is provided as-is for education, hackathon demonstration, and field discussion. We do not warrant that results are accurate, complete, or fit for a particular farm. To the extent allowed by law, the Field Shift project team is not liable for crop loss, income loss, or other damages arising from use of the tool.</p>
          <h2>Acceptable use</h2>
          <p>Use the app to explore rotations for fields you farm or advise. Do not scrape the NASA or OpenStreetMap services through this app in a way that violates their terms. Do not present the scores as a government order or a certified recommendation.</p>
          <h2>If something is wrong</h2>
          <p>Treat red flags as a prompt to look again, not as a forecast. Confirm unusual weather, pests, and soil issues on the ground.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()


def render_privacy() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div>
            <div class="kicker">Legal · Updated {UPDATED}</div>
            <h1 id="overview">Privacy notice</h1>
            <p class="lede">Field records are stored by the machine hosting the app. The hosted service has no user accounts, so do not enter confidential personal information.</p>
          </div>
        </div>
        <div class="legal">
          <h2>What you type</h2>
          <p>You may enter a field name, coordinates or place names, crop, soil notes, yield, farmer name (in extension mode), priorities, and local tips. Those values are used to score rotations and to fill share cards.</p>
          <h2>Where records are stored</h2>
          <p>Applied fields and extension rosters are stored in SQLite (<code>data/fieldshift.db</code>) on the machine running the app. NASA POWER climate series and place lookup results are cached under <code>data/power_cache/</code> and <code>data/geo_cache/</code>. The service operator and anyone with access to that machine can read these files. There is no self-service deletion control; an operator must remove records from the database and related caches.</p>
          <h2>What is sent to other services</h2>
          <ul>
            <li><strong>NASA POWER</strong> — selected field latitude, longitude, and climate date range. Farmer names and local notes are not part of the climate request.</li>
            <li><strong>OpenStreetMap Nominatim</strong> — place search text, or coordinates when a map pin is named. Use is subject to the OpenStreetMap Foundation’s terms and usage policy.</li>
            <li><strong>Map tiles</strong> — the browser requests map tiles from the configured tile provider to draw the map.</li>
          </ul>
          <p>The project does not add a product analytics service. The app framework may store a session cookie in your browser while you work. The web host may also retain ordinary server access logs according to its configuration.</p>
          <h2>We do not sell data</h2>
          <p>Field Shift does not sell farmer records. The hosting operator controls access and retention for records on the server. Deletion currently requires the operator to remove the saved record and related cache files.</p>
          <h2>Children</h2>
          <p>The app is meant for farmers and extension workers, not for children under 13.</p>
          <h2>Changes</h2>
          <p>This notice describes the hosted-server setup. Update it if the hosting provider, storage location, logging, or data retention changes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()


def render_data_sources() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div>
            <div class="kicker">Attribution · Updated {UPDATED}</div>
            <h1 id="overview">Data sources and licenses</h1>
            <p class="lede">Climate, places, and the map come from public services. The rotation scores are ours, not NASA’s.</p>
          </div>
        </div>
        <div class="legal">
          <h2>NASA POWER</h2>
          <p>Daily agroclimatology for the selected point is requested from the NASA Langley Research Center POWER Project (Prediction Of Worldwide Energy Resources), agriculture community, parameters T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, and RH2M. Please credit POWER when you reuse charts or numbers.</p>
          <p>POWER documentation and the public API: <a href="https://power.larc.nasa.gov/" target="_blank" rel="noopener">power.larc.nasa.gov</a>.</p>
          <h2>OpenStreetMap</h2>
          <p>Place search and reverse geocoding use the Nominatim service. Map tiles are from OpenStreetMap. © OpenStreetMap contributors. License: ODbL. Policy: <a href="https://operations.osmfoundation.org/policies/nominatim/" target="_blank" rel="noopener">Nominatim usage policy</a>.</p>
          <h2>Country and state names</h2>
          <p>Country and subdivision lists use ISO 3166 data via the pycountry library. Local government and village names come from OpenStreetMap, not from ISO.</p>
          <h2>This application</h2>
          <p>Rotation Explorer is a NASA Space Apps Challenge 2026 prototype. Rule-based scores, copy, and layout are part of the Field Shift project. Third-party libraries (Streamlit, pandas, Plotly, Folium, and others) keep their own licenses.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()
