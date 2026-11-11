import pandas as pd

from rotation_explorer.climate import (
    climate_story,
    describe_frost,
    describe_heat,
    describe_rain_trend,
    monthly_climate,
    summarize_climate,
)
from rotation_explorer.power import power_to_dataframe


def test_summarize_climate_annual_rain_and_heat():
    idx = pd.date_range("2020-01-01", periods=365, freq="D")
    df = pd.DataFrame(
        {
            "T2M": 20.0,
            "T2M_MAX": [35.0 if i % 10 == 0 else 25.0 for i in range(365)],
            "T2M_MIN": [-1.0 if i < 5 else 10.0 for i in range(365)],
            "PRECTOTCORR": 2.0,
        },
        index=idx,
    )
    summary = summarize_climate(df)
    assert summary.n_years == 1
    assert summary.start_year == 2020
    assert abs(summary.annual_precip_mm - 730.0) < 1e-6
    assert summary.heat_days_per_year == 37
    assert summary.frost_days_per_year == 5


def test_monthly_climate_resamples():
    idx = pd.date_range("2020-01-01", periods=31, freq="D")
    df = pd.DataFrame(
        {"T2M": 10.0, "T2M_MAX": 15.0, "PRECTOTCORR": 1.0},
        index=idx,
    )
    monthly = monthly_climate(df)
    assert len(monthly) == 1
    assert monthly["PRECTOTCORR"].iloc[0] == 31.0


def test_climate_story_uses_plain_language():
    idx = pd.date_range("2020-01-01", periods=365, freq="D")
    df = pd.DataFrame(
        {
            "T2M": 20.0,
            "T2M_MAX": 25.0,
            "T2M_MIN": 10.0,
            "PRECTOTCORR": 2.0,
        },
        index=idx,
    )
    story = climate_story(summarize_climate(df))
    assert "mm of rain" in story
    assert "°C" in story


def test_climate_descriptors():
    assert "common" in describe_heat(90)
    assert "drier" in describe_rain_trend(-12)
    assert "rare" in describe_frost(0)


def test_power_to_dataframe_drops_fill_values():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {"20180101": 10.0, "20180102": -999.0},
                "T2M_MAX": {"20180101": 12.0, "20180102": -999.0},
                "T2M_MIN": {"20180101": 8.0, "20180102": -999.0},
                "PRECTOTCORR": {"20180101": 1.5, "20180102": -999.0},
            }
        }
    }
    df = power_to_dataframe(payload)
    assert list(df.index.strftime("%Y-%m-%d")) == ["2018-01-01"]
    assert df.loc["2018-01-01", "PRECTOTCORR"] == 1.5
