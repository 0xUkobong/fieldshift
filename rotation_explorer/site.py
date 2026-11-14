"""About, disclaimer, privacy, and data-attribution pages."""

from __future__ import annotations

import streamlit as st

from rotation_explorer.config import DISCLAIMER
from rotation_explorer.seo import (
    ABOUT,
    DATA,
    DISCLAIMER as DISCLAIMER_SEO,
    DOCS,
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
    docs_url = app_route("/Documentation")
    disclaimer_url = app_route("/Disclaimer")
    privacy_url = app_route("/Privacy")
    st.markdown(
        f"""
        <nav class="topbar" aria-label="Main navigation">
          <a class="brand" href="{explorer_url}" target="_self"><img class="brand-mark" src="{header_mark_src()}" width="36" height="36" alt="">FIELD SHIFT <small>Rotation Explorer</small></a>
          <div class="toplinks">
            <a href="{explorer_url}" target="_self">EXPLORER</a>
            <a href="{docs_url}" target="_self">DOCS</a>
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
    docs, about, disclaimer, privacy, data, copy = st.columns([0.85, 0.85, 1.05, 0.85, 1.3, 3.6])
    with docs:
        st.page_link("pages/5_Documentation.py", label="Docs")
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
            "Rotation Explorer · Built by Team Asterverse · NASA Space Apps Challenge 2026 · "
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
        "docs": DOCS,
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
          <p>You may enter a field name, coordinates or place names, crop, soil notes, yield, farmer name (in extension mode), priorities, and local tips. You may also choose to share your device location for the current field. Those values are used to score rotations and to fill share cards.</p>
          <h2>Where records are stored</h2>
          <p>Applied fields and extension rosters are stored in SQLite (<code>data/fieldshift.db</code>) on the machine running the app. NASA POWER climate series and place lookup results are cached under <code>data/power_cache/</code> and <code>data/geo_cache/</code>. The service operator and anyone with access to that machine can read these files. There is no self-service deletion control; an operator must remove records from the database and related caches.</p>
          <h2>What is sent to other services</h2>
          <ul>
            <li><strong>NASA POWER</strong> — selected field latitude, longitude, and climate date range when you apply a comparison. Farmer names and local notes are not part of the climate request.</li>
            <li><strong>OpenStreetMap Nominatim</strong> — place search text, or coordinates only when you choose “Name the pin from coordinates.” Use is subject to the OpenStreetMap Foundation’s terms and usage policy.</li>
            <li><strong>Map tiles</strong> — the browser requests map tiles from the configured tile provider to draw the map.</li>
          </ul>
          <p>Device location is requested only after you tap “Use my device location” and grant permission in your browser. Field Shift does not track location in the background. The coordinates are used for this field and are stored with it only if you apply and save the comparison. You can deny or revoke browser permission and use search, the map, or coordinates instead.</p>
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


def render_documentation() -> None:
    explorer_url = app_route("/")
    st.markdown(
        f"""
        <div class="hero">
          <div>
            <div class="kicker">User Guide & Reference · Updated {UPDATED}</div>
            <h1 id="overview">How to Use Field Shift</h1>
            <p class="lede">A complete guide to making sense of local NASA climate records, rotation scoring, planting calendars, and offline sharing for your field.</p>
          </div>
        </div>
        <div class="legal">
          <h2>1. Quickstart: 3 Simple Steps</h2>
          <ol>
            <li><strong>Locate your field:</strong> Select Continent, Country, State, LGA, and Area, search any place name, click directly on the interactive map, or tap <em>"Capture Current Coordinates"</em> from your mobile device or browser.</li>
            <li><strong>Set crop & priorities:</strong> Choose your current primary crop (e.g. Maize, Sorghum, Millet, Rice, Cassava) and what matters most to your farm (water conservation, soil organic matter, nitrogen fixation, erosion control, or animal forage).</li>
            <li><strong>Apply and compare:</strong> Click <strong>"Apply and compare"</strong>. Field Shift immediately contacts NASA POWER, analyzes the 7-year agroclimate daily record for that exact GPS pin, scores 5 alternative crop rotations, and visualizes seasonal rainfall windows.</li>
          </ol>

          <h2>2. Making Sense of the Climate Data</h2>
          <p>Unlike generic weather apps that show forecasts, Field Shift pulls an official <strong>7-year daily agroclimate record</strong> from NASA’s Prediction Of Worldwide Energy Resources (POWER) satellite and assimilation models:</p>
          <ul>
            <li><strong>Typical Daily High (T2M_MAX):</strong> Year-round mean daily maximum temperature. Helps assess if crops are at baseline heat stress.</li>
            <li><strong>Rain in a Typical Year (PRECTOTCORR):</strong> Long-term average annual rainfall (mm/year).</li>
            <li><strong>Rainfall Trend (%):</strong> Compares recent years against earlier years in the record. A negative percentage (e.g. -12%) indicates a drying trend, prompting drought-hardy varieties.</li>
            <li><strong>Heat Stress Days:</strong> Count of days where temperatures exceeded 32 °C. Frequent heat spikes during flowering or grain-fill severely impact cereal yields.</li>
            <li><strong>Reference Evapotranspiration (ET₀):</strong> Calculated using solar radiation and temperature range via the Hargreaves-Samani method. Shows how much moisture the atmosphere is demanding from soil and foliage.</li>
            <li><strong>Moisture Balance (Rain − ET₀):</strong> Indicates whether rainfall satisfies evaporative demand or if the field experiences chronic seasonal water deficits.</li>
          </ul>

          <h2>3. Understanding the Rotation Scores (1 to 5)</h2>
          <p>Field Shift evaluates 5 tailored rotations against three transparent weighted pillars:</p>
          <ul>
            <li><strong>Water Resilience (40%):</strong> How well the sequence handles drought, heat waves, and evaporative water deficit. Rotations featuring deep roots, mulch cover, and drought-hardy pulses receive higher marks.</li>
            <li><strong>Soil Health (30%):</strong> Ability to build organic matter, fix natural nitrogen from atmospheric air, prevent erosion, and alleviate soil compaction.</li>
            <li><strong>Farmer Priorities (30%):</strong> Direct alignment with the specific goals you selected in the sidebar (e.g., animal forage, low fertilizer cost, moisture saving).</li>
          </ul>
          <p>The 5 evaluated rotation models are:</p>
          <ol>
            <li><strong>Current Rotation (Baseline):</strong> Your existing mono-crop or traditional rotation practice.</li>
            <li><strong>Drought-Tolerant + Cover Crop:</strong> Adds resilient sorghum/millet and mulch/cover crops to armor dry soils.</li>
            <li><strong>Nitrogen-Fixing Legume Mix:</strong> Intersperses pulses (cowpea, groundnut, soybean) to cut synthetic nitrogen costs and restore organic matter.</li>
            <li><strong>Agroforestry / Tree-Integrated:</strong> Incorporates multipurpose trees (e.g. <em>Faidherbia albida</em>, fruit/fuelwood trees) with legume understory for shade, wind protection, and long-term carbon.</li>
            <li><strong>Intensive Intercropping:</strong> Dual-canopy simultaneous cropping (e.g. cereal + legume in the same bed) to maximize yield per hectare and lower pest pressure.</li>
          </ol>

          <h2>4. What to Do with This Information</h2>
          <p>Field Shift is an agronomic decision-support tool designed to turn climate data into actionable field practices:</p>
          <ul>
            <li><strong>Start with a Test Plot:</strong> Never switch 100% of your acreage overnight. Dedicate a small 0.1 to 0.5 hectare demonstration strip to test the top-recommended rotation.</li>
            <li><strong>Check Planting Windows:</strong> Review the <em>Planting Window & Moisture Screen</em> to identify the months with the highest rainfall reliability and lowest dry-spell frequency before buying seeds.</li>
            <li><strong>Use the Plain-English Summary:</strong> Click the floating <em>"Plain-English Summary"</em> button at the bottom-right corner for a jargon-free brief you can print or read aloud.</li>
            <li><strong>Take It Offline:</strong> Copy the SMS text or download the printable one-page Farmer Card HTML to take to the field with no internet connection.</li>
            <li><strong>Verify Locally:</strong> Take your FieldShift summary to your local agricultural extension agent, cooperative head, or agro-dealer to confirm seed availability and local disease resistance before planting.</li>
          </ul>
          <div style="margin-top:2rem;">
            <a class="pill-link" href="{explorer_url}" target="_self">Return to Explorer <span>↗</span></a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()
