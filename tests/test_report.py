from rotation_explorer.config import DISCLAIMER
from rotation_explorer.models import ClimateSummary, Farm, FarmSetup, RotationResult
from rotation_explorer.report import comparison_report


def test_comparison_report_includes_top_match_and_disclaimer():
    farm = Farm(
        name="Test Farm",
        lat=1.0,
        lon=2.0,
        region="Test",
        soil_note="Loam",
        typical_crop="Maize",
    )
    setup = FarmSetup(farm=farm, crop="Maize", priorities=("Conserve water / drought resilience",))
    climate = ClimateSummary(
        avg_t2m=20,
        avg_tmax=26,
        avg_tmin=10,
        annual_precip_mm=700,
        precip_trend_pct=-8,
        heat_days_per_year=20,
        frost_days_per_year=5,
        n_years=8,
        start_year=2018,
        end_year=2025,
    )
    rotations = [
        RotationResult(
            name="Current Rotation",
            tagline="Baseline",
            score=3.1,
            water=4,
            soil=2,
            priority=3,
            why="Because the record shows heat.",
            benefits=("Known management",),
            risks=("Stress may rise",),
            sequence="Maize → soybean",
        ),
        RotationResult(
            name="Drought-Tolerant + Cover Crop",
            tagline="Cover",
            score=4.2,
            water=5,
            soil=4,
            priority=5,
            why="Drier later years.",
            benefits=("Cover",),
            risks=("Equipment",),
            sequence="Cover mix",
        ),
    ]
    text = comparison_report(setup, climate, rotations)
    assert "Top match: Drought-Tolerant + Cover Crop" in text
    assert DISCLAIMER in text
    assert "Test Farm" in text
