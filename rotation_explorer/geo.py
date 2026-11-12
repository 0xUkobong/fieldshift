"""World place hierarchy and OpenStreetMap Nominatim lookup."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pycountry
import requests

from rotation_explorer.models import Farm

GEO_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "geo_cache"
NOMINATIM_URL = "https://nominatim.openstreetmap.org"
NOMINATIM_USER_AGENT = "FieldShift-RotationExplorer/1.0 (NASA Space Apps)"
NOMINATIM_TIMEOUT_S = 20
NOMINATIM_MIN_INTERVAL_S = 1.05

CONTINENTS = (
    "Africa",
    "Asia",
    "Europe",
    "North America",
    "South America",
    "Oceania",
    "Antarctica",
)

CONTINENT_VIEW = {
    "Africa": (7.0, 20.0, 3.0),
    "Asia": (28.0, 90.0, 2.4),
    "Europe": (50.0, 15.0, 3.2),
    "North America": (40.0, -100.0, 2.4),
    "South America": (-15.0, -60.0, 2.6),
    "Oceania": (-18.0, 150.0, 2.6),
    "Antarctica": (-80.0, 0.0, 2.0),
}

# ISO 3166-1 alpha-2 → continent (UN M49, with common territories).
_CONTINENT_ISO = {
    "Africa": (
        "AO BF BI BJ BW CD CF CG CI CM CV DJ DZ EG EH ER ET GA GH GM GN GQ GW "
        "KE KM LR LS LY MA MG ML MR MU MW MZ NA NE NG RW SC SD SL SN SO SS ST "
        "SZ TD TG TN TZ UG YT ZA ZM ZW RE SH"
    ),
    "Asia": (
        "AE AF AM AZ BD BH BN BT CN CY GE HK ID IL IN IQ IR JO JP KG KH KP KR "
        "KW KZ LA LB LK MM MN MO MV MY NP OM PH PK PS QA SA SG SY TH TJ TL TM "
        "TR TW UZ VN YE"
    ),
    "Europe": (
        "AD AL AT AX BA BE BG BY CH CZ DE DK EE ES FI FO FR GB GG GI GR HR HU "
        "IE IM IS IT JE LI LT LU LV MC MD ME MK MT NL NO PL PT RO RS RU SE SI "
        "SJ SK SM UA VA XK"
    ),
    "North America": (
        "AG AI AW BB BL BM BQ BS BZ CA CR CU CW DM DO GD GL GP GT HN HT JM KN "
        "KY LC MF MQ MS MX NI PA PM PR SV SX TC TT US VC VG VI"
    ),
    "South America": "AR BO BR CL CO EC FK GF GY PE PY SR UY VE",
    "Oceania": (
        "AS AU CK FJ FM GU KI MH MP NC NF NR NU NZ PF PG PN PW SB TK TO TV VU "
        "WF WS"
    ),
    "Antarctica": "AQ BV GS HM TF",
}

_ISO_TO_CONTINENT: dict[str, str] = {}
for _continent, _codes in _CONTINENT_ISO.items():
    for _code in _codes.split():
        _ISO_TO_CONTINENT[_code] = _continent

_last_nominatim_at = 0.0


@dataclass(frozen=True)
class Place:
    continent: str = ""
    country: str = ""
    country_code: str = ""
    state: str = ""
    lga: str = ""
    area: str = ""
    lat: float | None = None
    lon: float | None = None
    display_name: str = ""

    def has_point(self) -> bool:
        return self.lat is not None and self.lon is not None

    def region_label(self) -> str:
        parts: list[str] = []
        for part in (self.continent, self.country, self.state, self.lga, self.area):
            if part and part not in parts:
                parts.append(part)
        return " · ".join(parts) or self.display_name or "Unnamed field"

    def suggested_name(self) -> str:
        return self.area or self.lga or self.state or self.country or "My field"


class GeoLookupError(Exception):
    """Raised when a place lookup cannot be completed."""


def continent_for(country_code: str) -> str:
    return _ISO_TO_CONTINENT.get((country_code or "").upper(), "")


def countries_in(continent: str) -> list[tuple[str, str]]:
    """Return (name, alpha_2) pairs for a continent, sorted by name."""
    rows: list[tuple[str, str]] = []
    for iso, name_continent in _ISO_TO_CONTINENT.items():
        if name_continent != continent:
            continue
        record = pycountry.countries.get(alpha_2=iso)
        label = record.name if record else iso
        rows.append((label, iso))
    rows.sort(key=lambda item: item[0])
    return rows


def country_name(country_code: str) -> str:
    record = pycountry.countries.get(alpha_2=(country_code or "").upper())
    return record.name if record else country_code


def states_in(country_code: str) -> list[str]:
    try:
        parts = pycountry.subdivisions.get(country_code=country_code.upper())
    except KeyError:
        return []
    if not parts:
        return []
    names = sorted({item.name for item in parts if item.name})
    return names


def match_state(country_code: str, raw: str) -> str:
    """Map OSM names like 'Kano State' onto pycountry subdivision names."""
    text = (raw or "").strip()
    if not text:
        return ""
    options = states_in(country_code)
    if text in options:
        return text
    lowered = text.lower().replace(" state", "").replace(" province", "").replace(" region", "")
    for option in options:
        if option.lower() == lowered or lowered in option.lower() or option.lower() in lowered:
            return option
    return text


def place_from_nominatim(payload: dict[str, Any]) -> Place:
    address = payload.get("address") or {}
    country_code = str(address.get("country_code") or "").upper()
    state = (
        address.get("state")
        or address.get("region")
        or address.get("province")
        or address.get("state_district")
        or ""
    )
    lga = (
        address.get("county")
        or address.get("municipality")
        or address.get("district")
        or address.get("city_district")
        or ""
    )
    area = (
        address.get("village")
        or address.get("hamlet")
        or address.get("town")
        or address.get("suburb")
        or address.get("neighbourhood")
        or address.get("city")
        or ""
    )
    if area and area == lga:
        area = address.get("suburb") or address.get("neighbourhood") or area
    lat_raw = payload.get("lat")
    lon_raw = payload.get("lon")
    return Place(
        continent=continent_for(country_code),
        country=address.get("country") or country_name(country_code),
        country_code=country_code,
        state=str(state),
        lga=str(lga),
        area=str(area),
        lat=float(lat_raw) if lat_raw not in (None, "") else None,
        lon=float(lon_raw) if lon_raw not in (None, "") else None,
        display_name=str(payload.get("display_name") or ""),
    )


def _cache_path(kind: str, params: dict[str, str]) -> Path:
    GEO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = urlencode(sorted(params.items()))
    safe = "".join(ch if ch.isalnum() else "_" for ch in f"{kind}_{key}")[:180]
    return GEO_CACHE_DIR / f"{safe}.json"


def _throttle() -> None:
    global _last_nominatim_at
    wait = NOMINATIM_MIN_INTERVAL_S - (time.monotonic() - _last_nominatim_at)
    if wait > 0:
        time.sleep(wait)
    _last_nominatim_at = time.monotonic()


def _nominatim_get(path: str, params: dict[str, str]) -> Any:
    cache = _cache_path(path.strip("/"), params)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    _throttle()
    try:
        response = requests.get(
            f"{NOMINATIM_URL}{path}",
            params=params,
            headers={"User-Agent": NOMINATIM_USER_AGENT, "Accept-Language": "en"},
            timeout=NOMINATIM_TIMEOUT_S,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise GeoLookupError("Place lookup timed out. Try again, or enter coordinates.") from exc
    except requests.RequestException as exc:
        raise GeoLookupError("Could not reach the place directory (OpenStreetMap).") from exc
    except ValueError as exc:
        raise GeoLookupError("Place directory returned invalid data.") from exc
    cache.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def search_places(
    query: str,
    *,
    country_code: str = "",
    limit: int = 8,
) -> list[Place]:
    text = query.strip()
    if len(text) < 2:
        return []
    params = {
        "q": text,
        "format": "jsonv2",
        "addressdetails": "1",
        "limit": str(limit),
    }
    if country_code:
        params["countrycodes"] = country_code.lower()
    payload = _nominatim_get("/search", params)
    if not isinstance(payload, list):
        return []
    places = [place_from_nominatim(item) for item in payload if isinstance(item, dict)]
    return [item for item in places if item.has_point()]


def lookup_area(
    *,
    country: str,
    country_code: str,
    state: str = "",
    lga: str = "",
    area: str = "",
) -> Place | None:
    parts = [part for part in (area, lga, state, country) if part]
    if not parts:
        return None
    hits = search_places(", ".join(parts), country_code=country_code, limit=5)
    if not hits:
        return None
    best = hits[0]
    return replace(
        best,
        continent=best.continent or continent_for(country_code),
        country=best.country or country,
        country_code=best.country_code or country_code,
        state=best.state or state,
        lga=best.lga or lga,
        area=best.area or area,
    )


def farm_from_place(
    place: Place,
    *,
    name: str,
    crop: str,
    soil_note: str = "",
    local_tip: str = "",
    agrozone: str = "",
) -> Farm:
    label = name.strip() or place.suggested_name()
    return Farm(
        name=label,
        lat=float(place.lat or 0.0),
        lon=float(place.lon or 0.0),
        region=place.region_label(),
        soil_note=soil_note.strip()
        or "Field-specific soil information has not been provided.",
        typical_crop=crop,
        local_tip=local_tip,
        agrozone=agrozone,
        continent=place.continent,
        country=place.country,
        country_code=place.country_code,
        state=place.state,
        lga=place.lga,
        area=place.area,
    )


def reverse_geocode(lat: float, lon: float) -> Place:
    payload = _nominatim_get(
        "/reverse",
        {
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "format": "jsonv2",
            "addressdetails": "1",
            "zoom": "14",
        },
    )
    if not isinstance(payload, dict):
        raise GeoLookupError("Could not name this map point.")
    place = place_from_nominatim(payload)
    if place.lat is None:
        place = replace(place, lat=lat, lon=lon)
    return place
