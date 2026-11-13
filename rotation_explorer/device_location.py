"""Opt-in browser geolocation control for the field picker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "device_location_component"
_device_location_component = None


def device_location_picker(*, key: str) -> dict[str, Any] | None:
    """Render a consent-first button and return one location result or error."""
    global _device_location_component
    if _device_location_component is None:
        # Declare on the active Streamlit run so the component route registers
        # correctly in both local and hosted sessions.
        _device_location_component = components.declare_component(
            "fieldshift_device_location",
            path=str(_COMPONENT_DIR),
        )
    value = _device_location_component(default=None, key=key)
    return value if isinstance(value, dict) else None
