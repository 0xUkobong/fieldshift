from rotation_explorer.config import DISCLAIMER
from rotation_explorer.site import UPDATED


def test_disclaimer_is_decision_support_not_advice():
    assert "should not replace local agronomic advice" in DISCLAIMER
    assert UPDATED.endswith("2026")
