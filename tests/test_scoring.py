from rotation_explorer.config import (
    ROTATION_AGROFORESTRY,
    ROTATION_CURRENT,
    ROTATION_DROUGHT,
    ROTATION_INTERCROP,
    ROTATION_LEGUME,
    infer_soil_type,
)
from rotation_explorer.models import ClimateSummary
from rotation_explorer.scoring import clamp_score, overall_score, score_rotations


def _climate(**overrides) -> ClimateSummary:
    base = dict(
        avg_t2m=20.0,
        avg_tmax=26.0,
        avg_tmin=10.0,
        annual_precip_mm=800.0,
        precip_trend_pct=0.0,
        heat_days_per_year=20.0,
        frost_days_per_year=10.0,
        n_years=8,
        start_year=2018,
        end_year=2025,
    )
    base.update(overrides)
    return ClimateSummary(**base)


def test_clamp_score_bounds():
    assert clamp_score(0) == 1
    assert clamp_score(9) == 5
    assert clamp_score(3.4) == 3


def test_overall_score_weights():
    assert overall_score(5, 5, 5) == 5.0
    assert overall_score(1, 1, 1) == 1.0


def test_hot_dry_climate_prefers_drought_rotation():
    climate = _climate(
        avg_tmax=32.0,
        annual_precip_mm=280.0,
        precip_trend_pct=-12.0,
        heat_days_per_year=120.0,
    )
    results = {r.name: r for r in score_rotations(climate, "Maize", ["Conserve water / drought resilience"])}
    assert results[ROTATION_DROUGHT].score > results[ROTATION_CURRENT].score
    assert results[ROTATION_DROUGHT].water >= results[ROTATION_CURRENT].water


def test_organic_matter_priority_lifts_legume_match():
    climate = _climate()
    results = {
        r.name: r
        for r in score_rotations(
            climate,
            "Wheat",
            ["Improve soil organic matter", "Natural nitrogen fixing"],
        )
    }
    assert results[ROTATION_LEGUME].priority >= results[ROTATION_CURRENT].priority
    assert results[ROTATION_LEGUME].soil == 5


def test_score_rotations_returns_all_five_options():
    climate = _climate(avg_et0_mm_day=4.5, avg_rh_pct=60.0)
    results = score_rotations(climate, "Maize", ["Improve soil organic matter"])
    names = {r.name for r in results}
    assert names == {
        ROTATION_CURRENT,
        ROTATION_DROUGHT,
        ROTATION_LEGUME,
        ROTATION_AGROFORESTRY,
        ROTATION_INTERCROP,
    }


def test_high_et0_increases_water_stress_for_current_rotation():
    low_et0 = _climate(annual_precip_mm=650.0, avg_et0_mm_day=2.5)
    high_et0 = _climate(annual_precip_mm=650.0, avg_et0_mm_day=6.5)
    res_low = {r.name: r for r in score_rotations(low_et0, "Maize", [])}
    res_high = {r.name: r for r in score_rotations(high_et0, "Maize", [])}
    assert res_high[ROTATION_CURRENT].water <= res_low[ROTATION_CURRENT].water


def test_soil_type_inference_and_scoring_modifiers():
    assert infer_soil_type("Sandy loam, well-drained") == "Sandy / Light"
    assert infer_soil_type("Heavy black clay vertisol") == "Clay / Heavy"
    assert infer_soil_type("Deep volcanic ash") == "Volcanic / Organic"
    assert infer_soil_type("Balanced medium loam") == "Loam"

    climate = _climate(annual_precip_mm=650.0, avg_et0_mm_day=4.5)
    loam = {r.name: r for r in score_rotations(climate, "Maize", [], soil_type="Loam")}
    sandy = {r.name: r for r in score_rotations(climate, "Maize", [], soil_type="Sandy / Light")}
    clay = {r.name: r for r in score_rotations(climate, "Maize", [], soil_type="Clay / Heavy")}
    assert sandy[ROTATION_CURRENT].water <= loam[ROTATION_CURRENT].water
    assert sandy[ROTATION_DROUGHT].water >= loam[ROTATION_DROUGHT].water
    assert clay[ROTATION_CURRENT].soil <= loam[ROTATION_CURRENT].soil
