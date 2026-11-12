from rotation_explorer.models import Farm, FarmSetup
from rotation_explorer.store import load_last_setup, load_roster, save_field, save_roster_entry


def test_save_and_reload_field(tmp_path):
    db = tmp_path / "fields.db"
    farm = Farm(
        name="North plot",
        lat=12.0,
        lon=8.5,
        region="Africa · Nigeria · Kano",
        soil_note="sandy loam",
        typical_crop="Sorghum",
        continent="Africa",
        country="Nigeria",
        country_code="NG",
        state="Kano",
        lga="Kumbotso",
        area="North plot",
    )
    setup = FarmSetup(
        farm=farm,
        crop="Sorghum",
        priorities=("Conserve water / drought resilience",),
        farmer_name="Amina",
        soil_type="Sandy / Light",
    )
    field_id = save_field(setup, db)
    assert field_id > 0
    loaded = load_last_setup(db)
    assert loaded is not None
    assert loaded.farm.name == "North plot"
    assert loaded.farm.country_code == "NG"
    assert loaded.crop == "Sorghum"
    assert loaded.farmer_name == "Amina"


def test_roster_persists(tmp_path):
    db = tmp_path / "fields.db"
    save_roster_entry(
        {"farmer_name": "Amina", "farm_name": "North plot", "sms": "hello"},
        db,
    )
    rows = load_roster(db)
    assert rows[0]["farmer_name"] == "Amina"
    assert rows[0]["sms"] == "hello"
