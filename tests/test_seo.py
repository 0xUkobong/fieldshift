from rotation_explorer.seo import ABOUT, EXPLORER, asset_url, graph_for, public_url


def test_explorer_graph_has_software_and_website():
    types = {node["@type"] for node in graph_for(EXPLORER)["@graph"]}
    assert "SoftwareApplication" in types
    assert "WebSite" in types
    assert "FAQPage" not in types


def test_about_graph_includes_faq():
    types = {node["@type"] for node in graph_for(ABOUT)["@graph"]}
    assert "FAQPage" in types


def test_asset_url_is_absolute():
    url = asset_url("og.png")
    assert url.startswith("http")
    assert url.endswith("/og.png")
    assert public_url()
