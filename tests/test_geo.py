from rotation_explorer.geo import (
    continent_for,
    countries_in,
    farm_from_place,
    match_state,
    place_from_nominatim,
    states_in,
)


def test_nigeria_is_africa():
    assert continent_for("NG") == "Africa"
    names = [name for name, iso in countries_in("Africa")]
    assert "Nigeria" in names


def test_kano_is_a_nigerian_state():
    states = states_in("NG")
    assert any("Kano" in item for item in states)
    assert match_state("NG", "Kano State") == "Kano"


def test_place_from_nominatim_fills_hierarchy():
    payload = {
        "lat": "12.002",
        "lon": "8.592",
        "display_name": "Kumbotso, Kano, Nigeria",
        "address": {
            "village": "Kumbotso",
            "county": "Kumbotso",
            "state": "Kano",
            "country": "Nigeria",
            "country_code": "ng",
        },
    }
    place = place_from_nominatim(payload)
    assert place.continent == "Africa"
    assert place.country == "Nigeria"
    assert place.country_code == "NG"
    assert place.state == "Kano"
    assert place.lga == "Kumbotso"
    assert place.area == "Kumbotso"
    assert place.has_point()
    assert "Africa" in place.region_label()
    farm = farm_from_place(place, name="North plot", crop="Sorghum")
    assert farm.lat == 12.002
    assert farm.country_code == "NG"
    assert farm.typical_crop == "Sorghum"
