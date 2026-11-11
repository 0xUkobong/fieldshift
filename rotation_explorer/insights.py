"""Farmer-facing flags, timing, SMS, and share-card copy. No Streamlit."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as html_escape

import pandas as pd

from rotation_explorer.config import (
    AFRICAN_CEREALS,
    DISCLAIMER,
    HEAT_STRESS_C,
    ROTATION_CURRENT,
    ROTATION_DROUGHT,
    ROTATION_LEGUME,
)
from rotation_explorer.models import ClimateSummary, FarmSetup, RotationResult


@dataclass(frozen=True)
class RiskFlag:
    label: str
    level: str  # green | yellow | red
    detail: str


@dataclass(frozen=True)
class VisualCue:
    label: str
    value: str
    level: str


def climate_risk_flags(climate: ClimateSummary) -> list[RiskFlag]:
    drought = (
        "red"
        if climate.annual_precip_mm < 500 or climate.precip_trend_pct <= -10
        else "yellow"
        if climate.annual_precip_mm < 800 or climate.precip_trend_pct <= -5
        else "green"
    )
    heat = (
        "red"
        if climate.heat_days_per_year >= 80
        else "yellow"
        if climate.heat_days_per_year >= 30
        else "green"
    )
    flood = (
        "yellow"
        if climate.annual_precip_mm >= 1200
        else "green"
    )
    return [
        RiskFlag(
            "Drought",
            drought,
            f"{climate.annual_precip_mm:.0f} mm/year, rain trend {climate.precip_trend_pct:+.0f}%",
        ),
        RiskFlag(
            "Heat",
            heat,
            f"{climate.heat_days_per_year:.0f} days above {HEAT_STRESS_C:.0f} °C",
        ),
        RiskFlag(
            "Flood / excess rain",
            flood,
            "High annual totals can mean waterlogging on heavy soils"
            if flood == "yellow"
            else "Annual rain is not in a high-flood band for this point",
        ),
    ]


def rotation_visuals(result: RotationResult) -> list[VisualCue]:
    water_use = "Low" if result.water >= 4 else "Medium" if result.water == 3 else "High"
    water_level = "green" if result.water >= 4 else "yellow" if result.water == 3 else "red"
    drought = "Strong" if result.water >= 4 else "Fair" if result.water == 3 else "Watch"
    drought_level = water_level
    soil_stars = "★" * result.soil + "☆" * (5 - result.soil)
    if result.name == ROTATION_CURRENT:
        labor, labor_level = "Same", "green"
    elif result.name == ROTATION_DROUGHT:
        labor, labor_level = "A little more", "yellow"
    else:
        labor, labor_level = "More at harvest", "yellow"
    return [
        VisualCue("Water use", water_use, water_level),
        VisualCue("Soil improvement", soil_stars, "green" if result.soil >= 4 else "yellow"),
        VisualCue("Drought resilience", drought, drought_level),
        VisualCue("Labor change", labor, labor_level),
    ]


def _wettest_months(monthly: pd.DataFrame, n: int = 3) -> str:
    if monthly.empty or "PRECTOTCORR" not in monthly:
        return "the rains"
    by_month = monthly.groupby(monthly.index.month)["PRECTOTCORR"].mean()
    top = by_month.nlargest(n).index.tolist()
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return ", ".join(names[m - 1] for m in sorted(top))


def _driest_span(monthly: pd.DataFrame) -> str:
    if monthly.empty or "PRECTOTCORR" not in monthly:
        return "the dry months"
    by_month = monthly.groupby(monthly.index.month)["PRECTOTCORR"].mean()
    dry = [m for m, val in by_month.items() if val <= by_month.median() * 0.45]
    if not dry:
        dry = by_month.nsmallest(3).index.tolist()
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return ", ".join(names[m - 1] for m in sorted(dry)[:4])


def seasonal_guidance(
    monthly: pd.DataFrame,
    crop: str,
    top: RotationResult,
) -> list[str]:
    rains = _wettest_months(monthly)
    dry = _driest_span(monthly)
    steps = [
        f"Main rains in this record cluster around {rains}. Plan the cash crop for that window.",
        f"Drier / bare-soil months tend to be {dry}. Do not leave the field uncovered then if erosion or heat is a concern.",
    ]
    if top.name == ROTATION_DROUGHT:
        steps.append(
            "Plant a cover crop or residue mulch as soon as the main crop is harvested, before the dry season sets in."
        )
    elif top.name == ROTATION_LEGUME:
        pulse = "cowpea or groundnut" if crop in AFRICAN_CEREALS or crop in {"Maize"} else "a pulse"
        steps.append(
            f"Sow {pulse} after the cereal harvest while there is still moisture, then return to the cereal next season."
        )
    else:
        steps.append(
            "If you keep the current rotation, shorten any bare period after harvest with residue or a short-season cover."
        )
    return steps


def action_line(crop: str, top: RotationResult, region: str = "") -> str:
    african = "Africa" in region or crop in AFRICAN_CEREALS or crop in {"Cowpea", "Groundnut", "Cassava"}
    if top.name == ROTATION_DROUGHT:
        if african:
            return "After harvest, plant sorghum or millet with a cowpea/cover mix. Do not leave the soil bare."
        return "Follow the cash crop with a drought-tolerant variety and a cover crop before the dry season."
    if top.name == ROTATION_LEGUME:
        if african or crop == "Maize":
            return f"Plant cowpea or groundnut after {crop.lower()} to add nitrogen, then return to the cereal."
        return f"Insert a nitrogen-fixing pulse after {crop.lower()} before repeating the cereal."
    return f"Keep {crop.lower()} for now, but shorten bare-soil time after harvest."


SMS = {
    "en": "FieldShift: {farmer} @ {place}. Crop: {crop}. Try: {action} Score {score}/5. Confirm with a local advisor. NASA POWER, not a yield forecast.",
    "fr": "FieldShift: {farmer} @ {place}. Culture: {crop}. Essayer: {action} Score {score}/5. Confirmer avec un conseiller local. NASA POWER, pas un pronostic de rendement.",
    "sw": "FieldShift: {farmer} @ {place}. Zao: {crop}. Jaribu: {action} Alama {score}/5. Thibitisha na mshauri wa eneo. NASA POWER, si utabiri wa mavuno.",
    "ha": "FieldShift: {farmer} @ {place}. Amfanin gona: {crop}. Gwada: {action} Maka {score}/5. Tattauna da mai ba da shawara. NASA POWER, ba hasashen amfanin gona ba.",
}

ACTIONS_I18N = {
    "en": {
        ROTATION_DROUGHT: "After harvest plant a drought-tolerant cereal + cover. Do not leave soil bare.",
        ROTATION_LEGUME: "Plant cowpea or groundnut after the cereal to feed the soil.",
        ROTATION_CURRENT: "Keep the current crop but cover the soil after harvest.",
    },
    "fr": {
        ROTATION_DROUGHT: "Apres recolte, semer une cereale tolerante a la secheresse + couverture. Ne pas laisser le sol nu.",
        ROTATION_LEGUME: "Semer niebe ou arachide apres la cereale pour nourrir le sol.",
        ROTATION_CURRENT: "Garder la culture actuelle mais couvrir le sol apres la recolte.",
    },
    "sw": {
        ROTATION_DROUGHT: "Baada ya mavuno panda nafaka inayostahimili ukame + funika udongo. Usiache udongo uchi.",
        ROTATION_LEGUME: "Panda kunde au njugu baada ya nafaka ili kuboresha udongo.",
        ROTATION_CURRENT: "Endelea na zao la sasa lakini funika udongo baada ya mavuno.",
    },
    "ha": {
        ROTATION_DROUGHT: "Bayan girbi, shuka hatsi mai jure fari + rufe kasa. Kada ka bar kasa tsirara.",
        ROTATION_LEGUME: "Shuka wake ko gyada bayan hatsi don kyautata kasa.",
        ROTATION_CURRENT: "Ci gaba da amfanin gona na yanzu amma rufe kasa bayan girbi.",
    },
}


def sms_summary(
    setup: FarmSetup,
    top: RotationResult,
    language: str = "en",
) -> str:
    lang = language if language in SMS else "en"
    farmer = setup.farmer_name.strip() or "Farmer"
    action = ACTIONS_I18N[lang].get(top.name, ACTIONS_I18N[lang][ROTATION_CURRENT])
    return SMS[lang].format(
        farmer=farmer,
        place=setup.farm.name,
        crop=setup.crop,
        action=action,
        score=f"{top.score:.1f}",
    )


def farmer_card_html(
    setup: FarmSetup,
    climate: ClimateSummary,
    top: RotationResult,
    flags: list[RiskFlag],
    timing: list[str],
    language: str = "en",
) -> str:
    sms = sms_summary(setup, top, language)
    flag_html = "".join(
        f'<span class="lvl {flag.level}">{html_escape(flag.label)}</span>' for flag in flags
    )
    timing_html = "".join(f"<li>{html_escape(item)}</li>" for item in timing)
    tip = setup.local_tip or setup.farm.local_tip
    tip_html = (
        f"<p class='tip'><strong>Local tip:</strong> {html_escape(tip)}</p>" if tip else ""
    )
    return f"""<!DOCTYPE html>
<html lang="{language}"><head><meta charset="utf-8"/>
<title>FieldShift · {html_escape(setup.farm.name)}</title>
<style>
body{{font-family:DM Sans,Segoe UI,sans-serif;max-width:720px;margin:24px auto;padding:24px;color:#1e1e1f}}
h1{{font-weight:500;letter-spacing:-.04em}}
.lvl{{display:inline-block;margin:0 6px 6px 0;padding:4px 10px;border-radius:20px;font-size:12px}}
.green{{background:#d8f0d8}}.yellow{{background:#f7ca50}}.red{{background:#f4c2c2}}
.card{{border:1px solid #d8d8d8;border-radius:16px;padding:16px;margin:16px 0}}
.sms{{font-family:ui-monospace,monospace;font-size:13px;background:#f8f4e6;padding:12px;border-radius:12px}}
.foot{{font-size:12px;color:#626263}}
@media print{{body{{margin:0}}}}
</style></head><body>
<h1>FieldShift farmer card</h1>
<p>{html_escape(setup.farmer_name or "Farmer")} · {html_escape(setup.farm.name)} · {html_escape(setup.crop)}</p>
<div class="card">
<p><strong>Try this:</strong> {html_escape(action_line(setup.crop, top, setup.farm.region))}</p>
<p>Score {top.score:.1f}/5 · {html_escape(top.sequence)}</p>
{tip_html}
<p>{flag_html}</p>
</div>
<div class="card"><strong>When</strong><ul>{timing_html}</ul></div>
<p class="sms">{html_escape(sms)}</p>
<p class="foot">{html_escape(DISCLAIMER)}</p>
</body></html>"""
