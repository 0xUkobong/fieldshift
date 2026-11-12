"""Field location: continent → country → state → LGA → area, plus map and search."""

from __future__ import annotations

from html import escape

import folium
from streamlit_folium import st_folium
import streamlit as st

from rotation_explorer.config import EXAMPLE_FIELDS
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


def hydrate_location(farm: Farm) -> None:
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
    if place.lat is not None and place.lon is not None:
        st.session_state["loc_lat"] = float(place.lat)
        st.session_state["loc_lon"] = float(place.lon)
        st.session_state["loc_has_point"] = True


def _clear_pin() -> None:
    st.session_state["loc_has_point"] = False
    st.session_state.pop("loc_lat", None)
    st.session_state.pop("loc_lon", None)


def _on_continent_change() -> None:
    st.session_state["loc_country"] = ""
    st.session_state["loc_state"] = ""
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""
    st.session_state.pop("place_hits", None)
    _clear_pin()


def _on_country_change() -> None:
    st.session_state["loc_state"] = ""
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""
    st.session_state.pop("place_hits", None)


def _on_state_change() -> None:
    st.session_state["loc_lga"] = ""
    st.session_state["loc_area"] = ""


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
            name=hits[index].suggested_name(),
            crop=st.session_state.get("field_crop", "Maize"),
        )
    )


def _load_example_field() -> None:
    name = st.session_state.get("example_field")
    farm = next((item for item in EXAMPLE_FIELDS if item.name == name), None)
    if farm is None:
        return
    hydrate_location(farm)
    st.session_state["field_crop"] = farm.typical_crop
    st.session_state["climate_request_attempted"] = False


def _pin_selected_place() -> None:
    country_name, country_code = _split_country(st.session_state.get("loc_country") or "")
    if not country_code:
        return
    try:
        found = lookup_area(
            country=country_name,
            country_code=country_code,
            state=st.session_state.get("loc_state") or "",
            lga=(st.session_state.get("loc_lga") or "").strip(),
            area=(st.session_state.get("loc_area") or "").strip(),
        )
    except GeoLookupError as exc:
        st.session_state["_location_message"] = ("warning", str(exc))
        return
    if not found or not found.has_point():
        st.session_state["_location_message"] = (
            "warning",
            "No match for that place. Try a nearby town name, or click the map.",
        )
        return
    hydrate_location(
        farm_from_place(
            found,
            name=st.session_state.get("field_name") or found.suggested_name(),
            crop=st.session_state.get("field_crop", "Maize"),
        )
    )


def _name_pin_from_coordinates() -> None:
    place = _pin_from_widgets()
    if not place.has_point():
        return
    try:
        named = reverse_geocode(float(place.lat), float(place.lon))
    except GeoLookupError as exc:
        st.session_state["_location_message"] = ("warning", str(exc))
        return
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

    with st.form("place_search_form", border=False, clear_on_submit=False):
        search_col, go_col = st.columns((3.2, 0.8), gap="small")
        with search_col:
            query = st.text_input(
                "Search any place",
                placeholder="e.g. Kumbotso, Kano, Nigeria",
                help="Town, village, local government, or landmark anywhere in the world.",
            )
        with go_col:
            st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
            find = st.form_submit_button("Find places", use_container_width=True)

    if find:
        query = (query or "").strip()
        if len(query) < 2:
            st.warning("Type at least two letters to search.")
        else:
            try:
                st.session_state["place_hits"] = search_places(query, limit=8)
            except GeoLookupError as exc:
                st.session_state["place_hits"] = []
                st.error(str(exc))

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
        st.button("Use selected place", on_click=_apply_search_hit)

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
            disabled=not country_code,
            placeholder="e.g. Kano, Punjab, California",
        )

    lga_col, area_col = st.columns(2)
    with lga_col:
        st.text_input(
            "Local government / county / district",
            key="loc_lga",
            disabled=not country_code,
            placeholder="e.g. Kumbotso, Kiambu, Cook County",
        )
    with area_col:
        st.text_input(
            "Area / town / village",
            key="loc_area",
            disabled=not country_code,
            placeholder="e.g. farm settlement, ward, village",
        )

    st.button(
        "Pin this place on the map",
        disabled=not country_code,
        help="Looks up coordinates from the names you entered.",
        on_click=_pin_selected_place,
    )

    place = _pin_from_widgets()
    view = CONTINENT_VIEW.get(place.continent, (10.0, 20.0, 2.0))
    center_lat = place.lat if place.lat is not None else view[0]
    center_lon = place.lon if place.lon is not None else view[1]
    zoom = 11 if place.has_point() else (view[2] if place.continent else 2)

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

    map_col, note_col = st.columns((1.45, 0.55), gap="large")
    with map_col:
        event = st_folium(
            fmap,
            height=360,
            use_container_width=True,
            returned_objects=["last_clicked"],
            key="field_folium_map",
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
            hint = "Click the map to refine the pin. Apply in the setup panel to load NASA weather for this point."
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
        if st.button("Use these coordinates"):
            st.session_state["loc_lat"] = float(manual_lat)
            st.session_state["loc_lon"] = float(manual_lon)
            st.session_state["loc_has_point"] = True
            st.rerun()

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
