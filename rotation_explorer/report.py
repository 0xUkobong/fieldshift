"""Plain-text comparison report for download or sharing."""

from __future__ import annotations

from rotation_explorer.climate import climate_story
from rotation_explorer.config import DISCLAIMER, PRIORITY_WEIGHT, SOIL_WEIGHT, WATER_WEIGHT
from rotation_explorer.models import ClimateSummary, FarmSetup, RotationResult


def comparison_report(
    setup: FarmSetup,
    climate: ClimateSummary,
    rotations: list[RotationResult],
) -> str:
    farm = setup.farm
    top = max(rotations, key=lambda item: item.score)
    lines = [
        "Field Shift · Rotation Explorer",
        "NASA Space Apps Challenge 2026",
        "",
        f"Location: {farm.name} ({farm.lat:.2f}, {farm.lon:.2f})",
        f"Region: {farm.region}",
        f"Current crop: {setup.crop}",
        f"Priorities: {', '.join(setup.priorities)}",
        f"Soils: {farm.soil_note}",
        "",
        f"Climate ({climate.start_year}–{climate.end_year}, NASA POWER)",
        climate_story(climate),
        f"Mean max temperature: {climate.avg_tmax:.1f} °C",
        f"Typical annual rain: {climate.annual_precip_mm:.0f} mm",
        f"Rain trend: {climate.precip_trend_pct:+.0f}%",
        f"Hot days above 32 °C: {climate.heat_days_per_year:.0f} / year",
        f"Frost days: {climate.frost_days_per_year:.0f} / year",
        "",
        (
            f"Scoring: {int(WATER_WEIGHT * 100)}% water, "
            f"{int(SOIL_WEIGHT * 100)}% soil, "
            f"{int(PRIORITY_WEIGHT * 100)}% priority match."
        ),
        f"Top match: {top.name} ({top.score:.1f} / 5)",
        "",
    ]
    for result in rotations:
        lines.extend(
            [
                f"## {result.name} — {result.score:.1f} / 5",
                result.tagline,
                f"Sequence: {result.sequence}",
                f"Water {result.water}/5 · Soil {result.soil}/5 · Priorities {result.priority}/5",
                "",
                "Why suggested",
                result.why,
                "",
                "Benefits",
                *[f"- {item}" for item in result.benefits],
                "",
                "Risks / limitations",
                *[f"- {item}" for item in result.risks],
                "",
            ]
        )
    lines.extend(
        [
            DISCLAIMER,
            "",
            "Data: NASA POWER daily agroclimatology, community AG.",
        ]
    )
    return "\n".join(lines)
