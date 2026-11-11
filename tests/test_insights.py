from rotation_explorer.insights import (
    action_line,
    climate_risk_flags,
    rotation_visuals,
    sms_summary,
)
from rotation_explorer.models import ClimateSummary, Farm, FarmSetup, RotationResult
from rotation_explorer.config import ROTATION_DROUGHT, ROTATION_LEGUME


def _climate(**overrides) -> ClimateSummary:
    base = dict(
        avg_t2m=28.0,
        avg_tmax=34.0,
        avg_tmin=22.0,
        annual_precip_mm=420.0,
        precip_trend_pct=-12.0,
        heat_days_per_year=90.0,
        frost_days_per_year=0.0,
        n_years=8,
        start_year=2018,
        end_year=2025,
    )
    base.update(overrides)
    return ClimateSummary(**base)


def test_hot_dry_point_flags_drought_and_heat_red():
    flags = {item.label: item.level for item in climate_risk_flags(_climate())}
    assert flags["Drought"] == "red"
    assert flags["Heat"] == "red"


def test_sms_and_action_for_african_cereal():
    farm = Farm(
        name="Kano / northern Nigeria",
        lat=12.0,
        lon=8.5,
        region="Sahel",
        soil_note="sandy",
        typical_crop="Sorghum",
    )
    setup = FarmSetup(
        farm=farm,
        crop="Sorghum",
        priorities=("Conserve water / drought resilience",),
        farmer_name="Amina",
        language="ha",
    )
    top = RotationResult(
        name=ROTATION_LEGUME,
        tagline="",
        score=4.2,
        water=4,
        soil=5,
        priority=4,
        why="x",
        benefits=("b",),
        risks=("r",),
        sequence="x",
    )
    assert "cowpea" in action_line("Sorghum", top, "West Africa").lower()
    text = sms_summary(setup, top, "ha")
    assert "Amina" in text
    assert "FieldShift" in text


def test_visual_cues_have_four_measures():
    result = RotationResult(
        name=ROTATION_DROUGHT,
        tagline="",
        score=4.0,
        water=5,
        soil=4,
        priority=5,
        why="x",
        benefits=("b",),
        risks=("r",),
        sequence="x",
    )
    cues = rotation_visuals(result)
    assert [item.label for item in cues] == [
        "Water use",
        "Soil improvement",
        "Drought resilience",
        "Labor change",
    ]
    assert cues[0].value == "Low"
