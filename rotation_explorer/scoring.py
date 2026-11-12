"""Transparent, rule-based rotation scoring. No Streamlit dependency."""

from __future__ import annotations

from rotation_explorer.config import (
    AFRICAN_CEREALS,
    AGROFORESTRY_SEQUENCES,
    CURRENT_SEQUENCES,
    HEAT_STRESS_C,
    INTERCROP_SEQUENCES,
    PRIORITY_WEIGHT,
    ROTATION_AGROFORESTRY,
    ROTATION_CURRENT,
    ROTATION_DROUGHT,
    ROTATION_INTERCROP,
    ROTATION_LEGUME,
    SOIL_AGROFORESTRY,
    SOIL_BY_CROP,
    SOIL_INTERCROP,
    SOIL_WEIGHT,
    WATER_WEIGHT,
    WET_ANNUAL_MM,
)
from rotation_explorer.models import ClimateSummary, RotationResult


def clamp_score(value: float) -> int:
    return int(max(1, min(5, round(value))))


def heat_pressure(climate: ClimateSummary) -> float:
    """0 (cool) to 1 (very hot / many heat days)."""
    tmax_part = (climate.avg_tmax - 22.0) / 16.0
    days_part = climate.heat_days_per_year / 80.0
    return max(0.0, min(1.0, 0.6 * tmax_part + 0.4 * days_part))


def drought_pressure(climate: ClimateSummary) -> float:
    """0 (wet / stable) to 1 (dry and/or declining rain)."""
    rain_part = (WET_ANNUAL_MM - climate.annual_precip_mm) / (WET_ANNUAL_MM - 250.0)
    trend_part = (-climate.precip_trend_pct) / 25.0
    return max(0.0, min(1.0, 0.7 * rain_part + 0.3 * max(0.0, trend_part)))


def overall_score(water: int, soil: int, priority: int) -> float:
    return round(
        (WATER_WEIGHT * water + SOIL_WEIGHT * soil + PRIORITY_WEIGHT * priority),
        1,
    )


def precip_trend_word(pct: float) -> str:
    if pct <= -5:
        return "declining"
    if pct >= 5:
        return "increasing"
    return "fairly steady"


def priority_match(name: str, priorities: tuple[str, ...] | list[str]) -> int:
    """How well a rotation lines up with the farmer's stated goals."""
    water = "Conserve water / drought resilience" in priorities
    om = "Improve soil organic matter" in priorities
    nfix = "Natural nitrogen fixing" in priorities
    erosion = "Reduce erosion" in priorities
    forage = "Forage or supplemental income" in priorities
    n = max(len(priorities), 1)

    hits = 0.0
    if name == ROTATION_CURRENT:
        hits = 0.8
        if forage:
            hits += 0.4
    elif name == ROTATION_DROUGHT:
        if water:
            hits += 1.4
        if erosion:
            hits += 1.1
        if om:
            hits += 0.9
        if forage:
            hits += 0.6
        if nfix:
            hits += 0.4
    elif name == ROTATION_LEGUME:
        if nfix:
            hits += 1.5
        if om:
            hits += 1.2
        if erosion:
            hits += 0.7
        if forage:
            hits += 0.8
        if water:
            hits += 0.5
    elif name == ROTATION_AGROFORESTRY:
        if erosion:
            hits += 1.6
        if om:
            hits += 1.4
        if forage:
            hits += 1.2
        if nfix:
            hits += 0.8
        if water:
            hits += 0.6
    elif name == ROTATION_INTERCROP:
        if forage:
            hits += 1.3
        if nfix:
            hits += 1.0
        if om:
            hits += 0.9
        if water:
            hits += 0.7
        if erosion:
            hits += 0.6

    raw = 1.5 + (hits / n) * 3.5
    return clamp_score(raw)


def score_rotations(
    climate: ClimateSummary,
    crop: str,
    priorities: tuple[str, ...] | list[str],
    region: str = "",
    soil_type: str = "Loam",
) -> list[RotationResult]:
    heat = heat_pressure(climate)
    drought = drought_pressure(climate)

    # ET₀ adds evaporative demand pressure when solar data is available
    if climate.avg_et0_mm_day > 0:
        annual_et0_mm = climate.avg_et0_mm_day * 365
        et0_pressure = max(0.0, min(1.0,
            (annual_et0_mm - climate.annual_precip_mm) / 800.0
        ))
        stress = 0.35 * drought + 0.35 * heat + 0.30 * et0_pressure
    else:
        stress = 0.55 * drought + 0.45 * heat

    if soil_type == "Sandy / Light":
        stress = min(1.0, stress + 0.08)

    is_africa = "Africa" in region or crop in AFRICAN_CEREALS or crop == "Cassava"
    seq_key = "Africa" if is_africa else "default"

    soil_water_adj = {
        "Sandy / Light": (-0.4, 0.3, 0.1, 0.2, 0.1),
        "Clay / Heavy": (-0.2, 0.0, 0.2, 0.2, 0.0),
        "Volcanic / Organic": (0.2, 0.0, 0.0, 0.1, 0.1),
    }.get(soil_type, (0.0, 0.0, 0.0, 0.0, 0.0))

    current_water = clamp_score(4.2 - stress * 2.6 + soil_water_adj[0])
    drought_water = clamp_score(3.2 + stress * 2.0 + soil_water_adj[1])
    legume_water = clamp_score(3.0 + stress * 0.8 + soil_water_adj[2])
    # Agroforestry: trees shade & buffer moisture; stronger benefit under stress
    agro_water = clamp_score(2.6 + stress * 1.8 + soil_water_adj[3])
    # Intercropping: mixed canopy provides moderate water benefit
    intercrop_water = clamp_score(3.0 + stress * 1.1 + soil_water_adj[4])

    base_crop_soil = SOIL_BY_CROP.get(crop, 3)
    if soil_type == "Clay / Heavy":
        current_soil = clamp_score(base_crop_soil - 0.5)
    elif soil_type == "Volcanic / Organic":
        current_soil = clamp_score(base_crop_soil + 0.5)
    else:
        current_soil = base_crop_soil
    drought_soil = 4
    legume_soil = 5
    agro_soil = SOIL_AGROFORESTRY   # always 5 — trees drive long-term OM
    intercrop_soil = SOIL_INTERCROP  # always 4 — mixed root systems improve structure

    current_pri = priority_match(ROTATION_CURRENT, priorities)
    drought_pri = priority_match(ROTATION_DROUGHT, priorities)
    legume_pri = priority_match(ROTATION_LEGUME, priorities)
    agro_pri = priority_match(ROTATION_AGROFORESTRY, priorities)
    intercrop_pri = priority_match(ROTATION_INTERCROP, priorities)

    trend_word = precip_trend_word(climate.precip_trend_pct)
    rain = climate.annual_precip_mm
    tmax = climate.avg_tmax
    heat_days = climate.heat_days_per_year
    years = f"{climate.start_year}–{climate.end_year}"

    current = RotationResult(
        name=ROTATION_CURRENT,
        tagline="Baseline — keep what you know",
        score=overall_score(current_water, current_soil, current_pri),
        water=current_water,
        soil=current_soil,
        priority=current_pri,
        why=(
            f"Your {crop.lower()} system is the comparison baseline. NASA POWER "
            f"for this field ({years}) shows mean daily max temperature of "
            f"{tmax:.1f} °C and about {rain:.0f} mm of rain per year, with "
            f"{heat_days:.0f} days/year above {HEAT_STRESS_C:.0f} °C. Rainfall "
            f"is {trend_word} ({climate.precip_trend_pct:+.0f}% late vs early years). "
            "This rotation stays familiar, but scores lower if heat or dryness is rising."
        ),
        benefits=(
            "Known management, seed, and markets",
            "Yield history you can compare against",
            "No extra equipment or new crop learning curve",
        ),
        risks=(
            "May expose the same soil window to heat and dry spells each year",
            "Limited soil-cover or nitrogen-fixing benefit unless already in the mix",
            "Satellite climate trends do not capture local drainage or irrigation",
        ),
        sequence=CURRENT_SEQUENCES.get(crop, CURRENT_SEQUENCES["Mixed"]),
    )

    drought_rot = RotationResult(
        name=ROTATION_DROUGHT,
        tagline="Cover the soil, ease water demand",
        score=overall_score(drought_water, drought_soil, drought_pri),
        water=drought_water,
        soil=drought_soil,
        priority=drought_pri,
        why=(
            f"Suggested more strongly where heat or dryness shows up in the record. "
            f"Here, annual rain is {rain:.0f} mm and max temperature averages "
            f"{tmax:.1f} °C, with {heat_days:.0f} hot days per year. "
            f"Rainfall is {trend_word}. A drought-tolerant cash crop plus a cover "
            "crop shortens bare-soil periods and can improve infiltration — useful "
            "when POWER points to heat stress or tight moisture."
        ),
        benefits=(
            "Lower peak water demand than a thirsty continuous cereal",
            "Cover crop residue protects soil and slows runoff",
            "Better fit when farmer priority is drought resilience or erosion control",
        ),
        risks=(
            "Cover-crop seed, termination timing, and equipment may be new",
            "Market premiums for drought-tolerant varieties are location-specific",
            "POWER precipitation is a model product — confirm with rain gauges",
        ),
        sequence=(
            "Sorghum or millet → cowpea/cover → cereal"
            if is_africa
            else "Drought-tolerant cereal → cover mix → cash crop"
        ),
    )

    legume = RotationResult(
        name=ROTATION_LEGUME,
        tagline="Feed the soil, break pest cycles",
        score=overall_score(legume_water, legume_soil, legume_pri),
        water=legume_water,
        soil=legume_soil,
        priority=legume_pri,
        why=(
            f"This option scores highest on soil health. It is a stronger match when "
            "you selected organic matter or natural nitrogen. Climate context: "
            f"{tmax:.1f} °C mean max temperature and {rain:.0f} mm/year rain "
            f"({trend_word}). Legumes still need enough moisture to establish; "
            f"with {heat_days:.0f} hot days/year, choose heat-adapted varieties "
            "and keep the current crop in the mix rather than replacing it entirely."
        ),
        benefits=(
            "Biological nitrogen for the following cereal",
            "Residue and roots build organic matter and soil structure",
            "Breaks some pest and disease cycles tied to continuous cereals",
        ),
        risks=(
            "Possible short-term cash-crop area or yield trade-off",
            "Inoculant, weed, and harvest management differ from maize/wheat",
            "Does not replace a soil test or local fertilizer recommendation",
        ),
        sequence=(
            "Cereal → cowpea or groundnut → cereal"
            if is_africa
            else "Cereal → cowpea/soybean/clover mix → cereal"
        ),
    )

    agroforestry = RotationResult(
        name=ROTATION_AGROFORESTRY,
        tagline="Grow trees with crops for lasting soil and shade",
        score=overall_score(agro_water, agro_soil, agro_pri),
        water=agro_water,
        soil=agro_soil,
        priority=agro_pri,
        why=(
            "Integrating multipurpose trees (e.g. Faidherbia, Gliricidia, fruit trees) "
            "into the cropping system builds soil carbon over years, reduces runoff, "
            f"and buffers temperature. With {heat_days:.0f} hot days/year and "
            f"{rain:.0f} mm annual rain ({trend_word}), tree shade can moderate "
            "heat stress and tree roots improve infiltration during dry spells. "
            "Scores highest on erosion and long-term soil organic matter."
        ),
        benefits=(
            "Long-term soil carbon and organic matter accumulation under trees",
            "Tree canopy moderates heat stress on understorey crops",
            "Fruit, fodder, or fuelwood provide supplemental income and food",
            "Deep roots access subsoil moisture during dry spells",
        ),
        risks=(
            "Establishment takes 2–3 seasons before full benefit is seen",
            "Tree spacing and species choice require local agronomic advice",
            "Some crops dislike heavy shade — match species to your main crop",
            "Land tenure security matters for long-term tree investment",
        ),
        sequence=AGROFORESTRY_SEQUENCES[seq_key],
    )

    intercrop = RotationResult(
        name=ROTATION_INTERCROP,
        tagline="Two crops, one season — diversify risk and income",
        score=overall_score(intercrop_water, intercrop_soil, intercrop_pri),
        water=intercrop_water,
        soil=intercrop_soil,
        priority=intercrop_pri,
        why=(
            "Growing two complementary crops simultaneously (e.g. cereal + legume "
            "in strip or row intercrop) spreads yield risk across the season, adds "
            "nitrogen fixation, and covers soil faster than a pure stand. "
            f"With {rain:.0f} mm/year rain ({trend_word}) and {heat_days:.0f} "
            "hot days, a mixed canopy can reduce bare-soil evaporation and smooth "
            "the impact of a mid-season dry spell."
        ),
        benefits=(
            "Yield diversity reduces income risk if one crop fails",
            "Legume component fixes nitrogen for the companion cereal",
            "Denser canopy reduces weed pressure and soil moisture loss",
            "Familiar to many smallholders — lower learning curve than agroforestry",
        ),
        risks=(
            "Harvesting two crops at the same time increases peak labour demand",
            "Species competition can reduce individual crop yields if poorly managed",
            "Equipment designed for pure stands may not suit mixed beds",
            "Market for the second crop must exist locally",
        ),
        sequence=INTERCROP_SEQUENCES[seq_key],
    )

    return [current, drought_rot, legume, agroforestry, intercrop]
