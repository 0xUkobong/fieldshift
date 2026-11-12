"""App-wide constants, demo farms, and scoring weights."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from rotation_explorer.models import Farm

# ---------------------------------------------------------------------------
# NASA POWER — rolling 7-year window ending ~5 days ago (API data lag)
# ---------------------------------------------------------------------------
_today = date.today()
_end_date = _today - timedelta(days=5)
_start_date = _end_date.replace(year=_end_date.year - 7)

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_START = _start_date.strftime("%Y%m%d")
POWER_END = _end_date.strftime("%Y%m%d")
POWER_YEAR_MIN = _start_date.year
POWER_YEAR_MAX = _end_date.year
POWER_PARAMETERS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M"
POWER_COMMUNITY = "AG"
POWER_FILL_VALUE = -999.0
POWER_TIMEOUT_S = 90
POWER_CACHE_TTL_S = 60 * 60 * 12

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "power_cache"

HEAT_STRESS_C = 32.0
WET_ANNUAL_MM = 900.0

WATER_WEIGHT = 0.4
SOIL_WEIGHT = 0.3
PRIORITY_WEIGHT = 0.3

DEMO_FARMS: tuple[Farm, ...] = (
    Farm(
        name="Iowa Corn Belt",
        lat=42.0,
        lon=-93.5,
        region="U.S. Midwest",
        soil_note="Deep prairie soils (Mollisols); high organic-matter potential.",
        typical_crop="Maize",
        agrozone="Temperate maize–soybean",
        local_tip="Many farms already rotate maize with soybean. Cover crops after harvest close the winter bare-soil window.",
    ),
    Farm(
        name="California Central Valley",
        lat=36.7,
        lon=-119.8,
        region="U.S. California",
        soil_note="Irrigated alluvial soils; heat and water demand are the main risks.",
        typical_crop="Mixed",
        agrozone="Irrigated Mediterranean",
        local_tip="Irrigation often masks rainfall decline. Drought-tolerant sequences still help if water allocations tighten.",
    ),
    Farm(
        name="West Africa Maize Belt",
        lat=10.5,
        lon=-1.2,
        region="West Africa (Ghana / northern savanna)",
        soil_note="Savanna soils with seasonal rainfall; erosion and dry spells matter.",
        typical_crop="Maize",
        agrozone="Guinea savanna",
        local_tip="Farmers here often intercrop maize with cowpea or pigeon pea. Plant a cover or cowpea as soon as maize is harvested, before the dry season.",
    ),
    Farm(
        name="Kano / northern Nigeria",
        lat=12.0,
        lon=8.5,
        region="West Africa (Sudano-Sahel)",
        soil_note="Sandy loams; short rainy season and high heat.",
        typical_crop="Sorghum",
        agrozone="Sudano-Sahel",
        local_tip="Sorghum–millet–cowpea or groundnut rotations are familiar. Avoid leaving fields bare after harvest; residue and cowpea cover reduce wind erosion.",
    ),
    Farm(
        name="Ethiopian Highlands",
        lat=9.0,
        lon=38.7,
        region="East Africa (highland mixed)",
        soil_note="Highland soils; erosion on slopes and variable belg/kiremt rains.",
        typical_crop="Teff",
        agrozone="Highland mixed",
        local_tip="Teff–pulse sequences (chickpea, field pea, or faba bean) are common. Keep soil covered on slopes after teff harvest to slow erosion.",
    ),
)

FARMS_BY_NAME = {farm.name: farm for farm in DEMO_FARMS}

CROPS = (
    "Maize",
    "Sorghum",
    "Millet",
    "Teff",
    "Cowpea",
    "Groundnut",
    "Cassava",
    "Wheat",
    "Soybean",
    "Rice",
    "Mixed",
)

AFRICAN_CEREALS = {"Sorghum", "Millet", "Teff"}
LEGUMES = {"Cowpea", "Groundnut", "Soybean"}

PRIORITIES = (
    "Conserve water / drought resilience",
    "Improve soil organic matter",
    "Natural nitrogen fixing",
    "Reduce erosion",
    "Forage or supplemental income",
)

DEFAULT_PRIORITIES = (
    "Conserve water / drought resilience",
    "Improve soil organic matter",
)

LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "sw": "Kiswahili",
    "ha": "Hausa",
}

DISCLAIMER = (
    "This is an exploratory decision-support tool. Results are based on "
    "satellite and model data and should not replace local agronomic advice "
    "or on-farm observations."
)

CURRENT_SEQUENCES = {
    "Maize": "Maize → cowpea or soybean → maize",
    "Sorghum": "Sorghum → cowpea or groundnut → sorghum",
    "Millet": "Millet → cowpea → millet",
    "Teff": "Teff → pulse (chickpea/pea) → teff",
    "Cowpea": "Cowpea → cereal → cowpea",
    "Groundnut": "Groundnut → cereal → groundnut",
    "Cassava": "Cassava → grain/legume intercrop → cassava",
    "Wheat": "Wheat → summer cover or pulse → wheat",
    "Soybean": "Soybean → maize → soybean",
    "Rice": "Rice → rice (or rice–legume where water allows)",
    "Mixed": "Mixed cereals, legumes, and roots",
}

SOIL_BY_CROP = {
    "Maize": 2,
    "Sorghum": 3,
    "Millet": 3,
    "Teff": 3,
    "Cowpea": 5,
    "Groundnut": 4,
    "Cassava": 3,
    "Wheat": 3,
    "Soybean": 4,
    "Rice": 2,
    "Mixed": 3,
}

ROTATION_CURRENT = "Current Rotation"
ROTATION_DROUGHT = "Drought-Tolerant + Cover Crop"
ROTATION_LEGUME = "Nitrogen-Fixing Legume Mix"
ROTATION_AGROFORESTRY = "Agroforestry / Tree-Integrated"
ROTATION_INTERCROP = "Intensive Intercropping"

# Soil-health baseline scores for the two new rotations
SOIL_AGROFORESTRY = 5   # Trees drive long-term OM build-up
SOIL_INTERCROP = 4      # Mixed canopy improves over monoculture

# Crop sequences for new rotations
AGROFORESTRY_SEQUENCES = {
    "Africa": "Cereal + multipurpose trees (Faidherbia, Gliricidia) → legume understory",
    "default": "Cash crop + fruit / fuelwood trees → nitrogen-fixing understory",
}
INTERCROP_SEQUENCES = {
    "Africa": "Maize + cowpea (same beds) → sorghum + groundnut",
    "default": "Main cereal + legume (strip or row intercrop) → alternate cash crop",
}

SOIL_TYPES = (
    "Auto (from site)",
    "Loam",
    "Sandy / Light",
    "Clay / Heavy",
    "Silty / Alluvial",
    "Volcanic / Organic",
)


def infer_soil_type(soil_note: str) -> str:
    """Infer a standard soil texture bucket from a free-text site soil note."""
    note = soil_note.lower()
    if "sandy" in note or "sand" in note or "light" in note:
        return "Sandy / Light"
    if "clay" in note or "vertisol" in note or "heavy" in note:
        return "Clay / Heavy"
    if "silt" in note or "alluvial" in note:
        return "Silty / Alluvial"
    if "volcanic" in note or "organic" in note or "peat" in note:
        return "Volcanic / Organic"
    return "Loam"
