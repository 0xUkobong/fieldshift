"""Field location: continent → country → state → LGA → area, plus map and search."""

from __future__ import annotations

from dataclasses import replace
from html import escape

import folium
from streamlit_folium import st_folium
import streamlit as st

from rotation_explorer.config import EXAMPLE_FIELDS
from rotation_explorer.device_location import device_location_picker
from rotation_explorer.geo import (
    CONTINENT_VIEW,
    CONTINENTS,
    GeoLookupError,
    Place,
    countries_in,
    farm_from_place,
    lookup_area,
    match_state,
    reverse_geocode,
    search_places,
    states_in,
)
from rotation_explorer.models import Farm


def session_place() -> Place:
    value = st.session_state.get("place")
    if isinstance(value, Place):
        return value
    return Place()


def place_from_farm(farm: Farm) -> Place:
    return Place(
        continent=farm.continent,
        country=farm.country,
        country_code=farm.country_code,
        state=farm.state,
        lga=farm.lga,
        area=farm.area,
        lat=farm.lat,
        lon=farm.lon,
        display_name=farm.region,
    )


def hydrate_location(
    farm: Farm,
    *,
    approximate: bool = False,
    accuracy_m: float | None = None,
) -> None:
    place = place_from_farm(farm)
    st.session_state["place"] = place
    st.session_state["loc_continent"] = place.continent
    st.session_state["loc_country"] = (
        f"{place.country}|{place.country_code}" if place.country_code else ""
    )
    st.session_state["loc_state"] = match_state(place.country_code, place.state)
    st.session_state["loc_lga"] = place.lga
    st.session_state["loc_area"] = place.area
    st.session_state["field_name"] = farm.name
    st.session_state["loc_is_approximate"] = approximate
    st.session_state["loc_device_accuracy_m"] = accuracy_m
    if place.lat is not None and place.lon is not None:
        st.session_state["loc_lat"] = float(place.lat)
        st.session_state["loc_lon"] = float(place.lon)
        st.session_state["loc_has_point"] = True
        st.session_state["loc_map_zoom"] = 13
        st.session_state.pop("loc_map_preview", None)


def _clear_pin() -> None:
    st.session_state["loc_has_point"] = False
    st.session_state["loc_is_approximate"] = False
    st.session_state.pop("loc_lat", None)
    st.session_state.pop("loc_lon", None)


def _set_map_preview(lat: float, lon: float, zoom: int, label: str) -> None:
    st.session_state["loc_map_preview"] = {
        "lat": float(lat),
        "lon": float(lon),
        "zoom": int(zoom),
        "label": label,
    }


def _sync_location_from_fields(level: str) -> None:
    """Move the map to the best place match without an extra pin button."""
    _clear_pin()
    continent = st.session_state.get("loc_continent") or ""
    country_name, country_code = _split_country(st.session_state.get("loc_country") or "")
    if not country_code:
        view = CONTINENT_VIEW.get(continent)
        if view:
            _set_map_preview(view[0], view[1], int(view[2]), continent)
        else:
            st.session_state.pop("loc_map_preview", None)
        return

    state = (st.session_state.get("loc_state") or "").strip()
    lga = (st.session_state.get("loc_lga") or "").strip()
    area = (st.session_state.get("loc_area") or "").strip()
    zoom_by_level = {"country": 5, "state": 7, "lga": 9, "area": 12}
    try:
        found = lookup_area(
            country=country_name,
            country_code=country_code,
            state=state,
            lga=lga,
            area=area,
        )
    except GeoLookupError as exc:
        st.session_state["_location_message"] = ("warning", str(exc))
        return
    if not found or not found.has_point():
        return

    _set_map_preview(
        float(found.lat),
        float(found.lon),
        zoom_by_level.get(level, 7),
        found.region_label() or country_name,
    )
    if level == "area" and area:
        farm = farm_from_place(
            found,
            name=st.session_state.get("field_name") or found.suggested_name(),
            crop=st.session_state.get("field_crop", "Maize"),
        )
        hydrate_location(farm, approximate=True)
        st.session_state["loc_map_zoom"] = 13


def _on_continent_change() -> None:
    st.session_state["loc_country"] = ""
    st.session_state["loc_state"] = ""
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""
    st.session_state.pop("place_hits", None)
    _clear_pin()
    view = CONTINENT_VIEW.get(st.session_state.get("loc_continent") or "")
    if view:
        _set_map_preview(view[0], view[1], int(view[2]), st.session_state["loc_continent"])
    else:
        st.session_state.pop("loc_map_preview", None)


def _on_country_change() -> None:
    st.session_state["loc_state"] = ""
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""
    st.session_state.pop("place_hits", None)
    st.session_state.pop("loc_map_preview", None)
    _sync_location_from_fields("country")


def _on_state_change() -> None:
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""
    _sync_location_from_fields("state")


def _on_lga_change() -> None:
    st.session_state["loc_area"] = ""
    _sync_location_from_fields("lga")


def _on_area_change() -> None:
    _sync_location_from_fields("area")


def _country_options(continent: str) -> list[str]:
    return [""] + [f"{name}|{iso}" for name, iso in countries_in(continent)]


def _country_label(value: str) -> str:
    if not value:
        return "Select a country"
    return value.split("|", 1)[0]


def _split_country(value: str) -> tuple[str, str]:
    if "|" not in value:
        return "", ""
    name, iso = value.split("|", 1)
    return name, iso


def _apply_search_hit() -> None:
    hits: list[Place] = st.session_state.get("place_hits") or []
    index = st.session_state.get("place_hit_index")
    if index is None or not hits:
        return
    if index < 0 or index >= len(hits):
        return
    hydrate_location(
        farm_from_place(
            hits[index],
            name=st.session_state.get("field_name") or hits[index].suggested_name(),
            crop=st.session_state.get("field_crop", "Maize"),
        ),
        approximate=True,
    )


def _load_example_field() -> None:
    name = st.session_state.get("example_field")
    farm = next((item for item in EXAMPLE_FIELDS if item.name == name), None)
    if farm is None:
        return
    hydrate_location(farm)
    st.session_state["field_crop"] = farm.typical_crop
    st.session_state["climate_request_attempted"] = False


def _on_place_search() -> None:
    query = (st.session_state.get("place_search") or "").strip()
    if len(query) < 2:
        st.session_state["place_hits"] = []
        st.session_state.pop("place_hit_index", None)
        return
    try:
        hits = search_places(query, limit=8)
    except GeoLookupError as exc:
        st.session_state["place_hits"] = []
        st.session_state.pop("place_hit_index", None)
        st.session_state["_location_message"] = ("warning", str(exc))
        return
    # Nominatim can return the same place label for overlapping boundaries and
    # point records. Keep the best ranked match instead of repeating a radio row.
    unique_hits: list[Place] = []
    seen_labels: set[str] = set()
    for hit in hits:
        label = (hit.display_name or hit.region_label()).strip().casefold()
        if label and label not in seen_labels:
            unique_hits.append(hit)
            seen_labels.add(label)
    hits = unique_hits
    st.session_state["place_hits"] = hits
    if hits:
        st.session_state["place_hit_index"] = 0
        first_hit = hits[0]
        hydrate_location(
            farm_from_place(
                first_hit,
                name=st.session_state.get("field_name") or first_hit.suggested_name(),
                crop=st.session_state.get("field_crop", "Maize"),
            ),
            approximate=True,
        )
    else:
        st.session_state.pop("place_hit_index", None)
        st.session_state["_location_message"] = (
            "info",
            "No matching place found. Try a nearby town or click the map to set the field pin.",
        )


def _apply_device_location(result: dict[str, object]) -> None:
    event_id = result.get("eventId")
    if event_id is None or event_id == st.session_state.get("loc_device_event_id"):
        return
    st.session_state["loc_device_event_id"] = event_id
    lat = result.get("lat")
    lon = result.get("lon")
    if result.get("error"):
        return
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return

    accuracy = result.get("accuracy")
    accuracy_m = (
        float(accuracy)
        if isinstance(accuracy, (int, float)) and accuracy >= 0
        else None
    )
    place = Place(lat=float(lat), lon=float(lon), display_name="Device location")
    farm = farm_from_place(
        place,
        name=st.session_state.get("field_name") or "My field",
        crop=st.session_state.get("field_crop", "Maize"),
    )
    hydrate_location(farm, accuracy_m=accuracy_m)


def _name_pin_from_coordinates() -> None:
    place = _pin_from_widgets()
    if not place.has_point():
        return
    try:
        named = reverse_geocode(float(place.lat), float(place.lon))
    except GeoLookupError as exc:
        st.session_state["_location_message"] = ("warning", str(exc))
        return
    named = replace(named, lat=float(place.lat), lon=float(place.lon))
    hydrate_location(
        farm_from_place(
            named,
            name=st.session_state.get("field_name") or named.suggested_name(),
            crop=st.session_state.get("field_crop", "Maize"),
        )
    )


def _pin_from_widgets() -> Place:
    continent = st.session_state.get("loc_continent") or ""
    country_name, country_code = _split_country(st.session_state.get("loc_country") or "")
    state = st.session_state.get("loc_state") or ""
    lga = (st.session_state.get("loc_lga") or "").strip()
    area = (st.session_state.get("loc_area") or "").strip()
    lat = st.session_state.get("loc_lat")
    lon = st.session_state.get("loc_lon")
    current = session_place()
    has_point = bool(st.session_state.get("loc_has_point"))
    point_lat = lat if has_point and isinstance(lat, (int, float)) else None
    point_lon = lon if has_point and isinstance(lon, (int, float)) else None
    return Place(
        continent=continent,
        country=country_name,
        country_code=country_code,
        state=state,
        lga=lga,
        area=area,
        lat=point_lat,
        lon=point_lon,
        display_name=current.display_name,
    )


def render_location_picker() -> Place:
    pending_farm = st.session_state.pop("_pending_location_hydration", None)
    if isinstance(pending_farm, Farm):
        hydrate_location(pending_farm)

    st.session_state.setdefault("loc_continent", "")
    st.session_state.setdefault("loc_country", "")
    st.session_state.setdefault("loc_state", "")
    st.session_state.setdefault("loc_lga", "")
    st.session_state.setdefault("loc_area", "")
    st.session_state.setdefault("field_name", "")
    st.session_state.setdefault("place_search", "")
    st.session_state.setdefault("loc_has_point", False)

    location_message = st.session_state.pop("_location_message", None)
    if location_message:
        level, message = location_message
        getattr(st, level)(message)

    st.markdown(
        """
        <div class="section-head stacked" id="field">
          <h2>Where is this field?</h2>
          <p>Search a place, walk down from continent to area, or click the map. NASA weather loads for the pin you set — not a sample farm.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    device_result = device_location_picker(key="fieldshift-device-location")
    if device_result:
        _apply_device_location(device_result)

    st.text_input(
        "Search any place",
        key="place_search",
        placeholder="e.g. Kumbotso, Kano, Nigeria",
        help="Type a town, village, local government, or landmark, then press Enter. The map will move to the closest match.",
        on_change=_on_place_search,
    )

    hits: list[Place] = st.session_state.get("place_hits") or []
    if hits:
        labels = [
            item.display_name or item.region_label() or item.suggested_name()
            for item in hits
        ]
        st.radio(
            "Matching places",
            options=list(range(len(hits))),
            format_func=lambda i: labels[i],
            key="place_hit_index",
            on_change=_apply_search_hit,
        )

    continent = st.selectbox(
        "Continent",
        [""] + list(CONTINENTS),
        format_func=lambda value: value or "Select a continent",
        key="loc_continent",
        on_change=_on_continent_change,
    )

    country_values = _country_options(continent) if continent else [""]
    if st.session_state.get("loc_country") not in country_values:
        st.session_state["loc_country"] = ""
    country_value = st.selectbox(
        "Country",
        country_values,
        format_func=_country_label,
        key="loc_country",
        on_change=_on_country_change,
        disabled=not continent,
    )
    country_name, country_code = _split_country(country_value)

    states = states_in(country_code) if country_code else []
    if states:
        state_options = [""] + states
        if st.session_state.get("loc_state") not in state_options:
            st.session_state["loc_state"] = ""
        state = st.selectbox(
            "State / province",
            state_options,
            format_func=lambda value: value or "Select a state or province",
            key="loc_state",
            on_change=_on_state_change,
            disabled=not country_code,
        )
    else:
        state = st.text_input(
            "State / province / region",
            key="loc_state",
            on_change=_on_state_change,
            disabled=not country_code,
            placeholder="e.g. Kano, Punjab, California",
        )

    lga_col, area_col = st.columns(2)
    with lga_col:
        st.text_input(
            "Local government / county / district",
            key="loc_lga",
            on_change=_on_lga_change,
            disabled=not country_code,
            placeholder="e.g. Kumbotso, Kiambu, Cook County",
        )
    with area_col:
        st.text_input(
            "Area / town / village",
            key="loc_area",
            on_change=_on_area_change,
            disabled=not country_code,
            placeholder="e.g. farm settlement, ward, village",
        )

    place = _pin_from_widgets()
    view = CONTINENT_VIEW.get(place.continent, (10.0, 20.0, 2.0))
    preview = st.session_state.get("loc_map_preview") or {}
    center_lat = place.lat if place.lat is not None else preview.get("lat", view[0])
    center_lon = place.lon if place.lon is not None else preview.get("lon", view[1])
    zoom = (
        int(st.session_state.get("loc_map_zoom", 13))
        if place.has_point()
        else int(preview.get("zoom", view[2] if place.continent else 2))
    )

    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=int(zoom),
        tiles="OpenStreetMap",
    )
    if place.has_point():
        folium.CircleMarker(
            location=[place.lat, place.lon],
            radius=8,
            color="#1e1e1f",
            fill=True,
            fill_color="#8ec7e2",
            fill_opacity=0.95,
            popup=place.suggested_name(),
        ).add_to(fmap)
    elif preview.get("lat") is not None and preview.get("lon") is not None:
        folium.CircleMarker(
            location=[float(preview["lat"]), float(preview["lon"])],
            radius=7,
            color="#626263",
            weight=2,
            fill=True,
            fill_color="#f7ca50",
            fill_opacity=0.9,
            tooltip=f"Approximate area · {escape(str(preview.get('label') or ''))}",
        ).add_to(fmap)

    map_col, note_col = st.columns((1.45, 0.55), gap="large")
    with map_col:
        event = st_folium(
            fmap,
            height=440,
            use_container_width=True,
            returned_objects=["last_clicked"],
            key=f"field-map-{round(float(center_lat), 5)}-{round(float(center_lon), 5)}-{zoom}",
        )
    clicked = (event or {}).get("last_clicked") if event else None
    if clicked and "lat" in clicked and "lng" in clicked:
        click_key = (round(float(clicked["lat"]), 4), round(float(clicked["lng"]), 4))
        if st.session_state.get("last_map_click") != click_key:
            st.session_state["last_map_click"] = click_key
            try:
                named = reverse_geocode(float(clicked["lat"]), float(clicked["lng"]))
            except GeoLookupError as exc:
                named = Place(
                    lat=float(clicked["lat"]),
                    lon=float(clicked["lng"]),
                    continent=place.continent,
                    country=place.country,
                    country_code=place.country_code,
                    state=place.state,
                    lga=place.lga,
                    area=place.area,
                )
                st.session_state["_location_message"] = ("warning", str(exc))
            else:
                # Keep the exact point chosen by the farmer; reverse geocoding
                # supplies the place label, whose coordinates may be a centroid.
                named = replace(
                    named,
                    lat=float(clicked["lat"]),
                    lon=float(clicked["lng"]),
                )
            st.session_state["_pending_location_hydration"] = farm_from_place(
                named,
                name=st.session_state.get("field_name") or named.suggested_name(),
                crop=st.session_state.get("field_crop", "Maize"),
            )
            st.rerun()

    with note_col:
        crumbs = place.region_label() if (place.country or place.continent) else "No field selected yet"
        if place.has_point():
            coordinates = f"{place.lat:.4f}°, {place.lon:.4f}°"
            device_accuracy = st.session_state.get("loc_device_accuracy_m")
            if device_accuracy is not None:
                hint = f"Device location · about ±{device_accuracy:.0f} m reported accuracy. Click the map to adjust; NASA weather uses this pin."
            elif st.session_state.get("loc_is_approximate"):
                hint = "Approximate place match. Click the map to move the pin onto your field; NASA weather uses the pin."
            else:
                hint = "Field pin selected. Click the map to adjust it; NASA weather uses these coordinates."
        elif preview.get("label"):
            coordinates = f"Near {escape(str(preview['label']))}"
            hint = "Approximate area view. Add a village or area, or click the map to set the field pin."
        else:
            coordinates = "No coordinates yet"
            hint = "Choose a country and pin the place, search a name, or click the map."
        st.markdown(
            f"""
            <div class="map-panel">
              <span class="eyebrow">Selected field</span>
              <h3>{escape(st.session_state.get("field_name") or place.suggested_name())}</h3>
              <p>{escape(crumbs)}</p>
              <strong>{escape(coordinates)}</strong>
              <hr>
              <p>{escape(hint)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.text_input(
        "Field name",
        key="field_name",
        placeholder="e.g. Amina's plot, North field, Cooperative block 4",
        max_chars=80,
    )
    enter_coords = st.checkbox("I already know the coordinates", key="enter_coords")
    if enter_coords or place.has_point():
        known_lat = float(place.lat) if place.has_point() else 0.0
        known_lon = float(place.lon) if place.has_point() else 0.0
        fine_lat, fine_lon = st.columns(2)
        with fine_lat:
            manual_lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                step=0.01,
                format="%.4f",
                value=known_lat,
            )
        with fine_lon:
            manual_lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                step=0.01,
                format="%.4f",
                value=known_lon,
            )
        coord_btn_col1, coord_btn_col2 = st.columns((1, 1))
        with coord_btn_col1:
            if st.button("Use these coordinates", use_container_width=True):
                st.session_state["loc_lat"] = float(manual_lat)
                st.session_state["loc_lon"] = float(manual_lon)
                st.session_state["loc_has_point"] = True
                st.session_state["loc_is_approximate"] = False
                st.session_state["loc_map_zoom"] = 14
                st.session_state.pop("loc_map_preview", None)
                st.rerun()
        with coord_btn_col2:
            device_coord_result = device_location_picker(
                key="fieldshift-device-location-coords",
                button_label="◎ &nbsp; Capture Current Coordinates",
            )
            if device_coord_result:
                _apply_device_location(device_coord_result)

    place = _pin_from_widgets()

    st.button(
        "Name the pin from coordinates",
        disabled=not place.has_point(),
        on_click=_name_pin_from_coordinates,
    )

    with st.expander("Optional example fields (not used unless you pick one)"):
        st.caption("These are only shortcuts to known NASA POWER cache points. Your field does not have to be one of them.")
        names = [farm.name for farm in EXAMPLE_FIELDS]
        example = st.selectbox("Example field", ["—"] + names, key="example_field")
        if example != "—":
            st.button("Load example field", on_click=_load_example_field)

    st.session_state["place"] = place
    return place
