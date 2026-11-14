from rotation_explorer.config import DISCLAIMER
from rotation_explorer.seo import DOCS
from rotation_explorer.site import UPDATED, render_documentation


def test_disclaimer_is_decision_support_not_advice():
    assert "should not replace local agronomic advice" in DISCLAIMER
    assert UPDATED.endswith("2026")


def test_documentation_seo_and_structure():
    assert DOCS.path == "/Documentation"
    assert "User guide" in DOCS.description
