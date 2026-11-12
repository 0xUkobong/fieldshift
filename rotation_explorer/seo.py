"""Search, social, and generative-engine metadata for every page."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any

import streamlit.components.v1 as components

from rotation_explorer.config import (
    FAVICON_PATH,
    FIELDSHIFT_APP_BASE_PATH,
    GITHUB_RAW_STATIC,
    SITE_DESCRIPTION,
    SITE_KEYWORDS,
    SITE_LOCALE,
    SITE_NAME,
    SITE_SHORT_NAME,
    SITE_TAGLINE,
    SITE_URL,
)


def public_url() -> str:
    return SITE_URL


def asset_url(filename: str) -> str:
    if "github.com" in SITE_URL:
        return f"{GITHUB_RAW_STATIC}/{filename}"
    # The production front door serves static files from /assets, regardless
    # of the Streamlit mount path (currently /explorer).
    return f"{SITE_URL}/assets/{filename}"


def asset_src(filename: str) -> str:
    """Browser path for a UI asset in local Streamlit or the hosted front door."""
    if FIELDSHIFT_APP_BASE_PATH:
        return f"/assets/{filename}"
    if "github.com" in SITE_URL:
        return asset_url(filename)
    if os.environ.get("FIELDSHIFT_PUBLIC_URL"):
        return f"/assets/{filename}"
    return f"/app/static/{filename}"


def app_route(path: str) -> str:
    if path.startswith("http"):
        return path
    normalized = "/" + path.lstrip("/")
    base_path = f"/{FIELDSHIFT_APP_BASE_PATH}" if FIELDSHIFT_APP_BASE_PATH else ""
    if normalized == "/":
        return f"{base_path}/"
    return f"{base_path}{normalized}"


def absolute(path: str) -> str:
    if path.startswith("http"):
        return path
    return f"{SITE_URL}{app_route(path)}"


@dataclass(frozen=True)
class PageSEO:
    title: str
    description: str
    path: str
    image: str = "og.png"
    keywords: str = SITE_KEYWORDS
    type: str = "website"
    extra_jsonld: list[dict[str, Any]] = field(default_factory=list)


EXPLORER = PageSEO(
    title=f"{SITE_NAME} | {SITE_TAGLINE}",
    description=SITE_DESCRIPTION,
    path="/",
)
ABOUT = PageSEO(
    title=f"About · {SITE_SHORT_NAME}",
    description=(
        "About Field Shift Rotation Explorer: a NASA Space Apps 2026 field tool "
        "that compares crop rotations using NASA POWER weather for a real place, "
        "not a demo farm."
    ),
    path="/About",
)
DISCLAIMER = PageSEO(
    title=f"Disclaimer · {SITE_SHORT_NAME}",
    description=(
        "Field Shift is decision support, not agronomic advice. NASA does not "
        "endorse rotation scores. No warranty for farm outcomes."
    ),
    path="/Disclaimer",
)
PRIVACY = PageSEO(
    title=f"Privacy · {SITE_SHORT_NAME}",
    description=(
        "Privacy notice for Field Shift: hosted field records are stored on the "
        "app server. NASA POWER and OpenStreetMap receive coordinates or searches."
    ),
    path="/Privacy",
)
DATA = PageSEO(
    title=f"Data sources · {SITE_SHORT_NAME}",
    description=(
        "Climate from NASA POWER, places from OpenStreetMap Nominatim, "
        "countries from ISO 3166. Attribution and licenses for Field Shift."
    ),
    path="/Data_sources",
)


def _software_application() -> dict[str, Any]:
    return {
        "@type": "SoftwareApplication",
        "name": SITE_NAME,
        "alternateName": ["Rotation Explorer", "FieldShift"],
        "applicationCategory": "EducationalApplication",
        "applicationSubCategory": "Agriculture",
        "operatingSystem": "Web",
        "inLanguage": ["en", "fr", "sw", "ha"],
        "url": absolute("/"),
        "image": asset_url("og.png"),
        "description": SITE_DESCRIPTION,
        "featureList": [
            "Locate a field by continent, country, state, local government, and area",
            "Load NASA POWER daily agroclimatology for that point",
            "Compare crop rotations with transparent rule-based scores",
            "Share SMS-length notes and printable farmer cards",
        ],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "audience": {
            "@type": "Audience",
            "audienceType": "Farmers and agricultural extension workers",
        },
        "areaServed": {"@type": "Place", "name": "Worldwide"},
        "keywords": SITE_KEYWORDS,
        "creator": {
            "@id": f"{SITE_URL}/#organization",
            "@type": "Organization",
            "name": "Field Shift project",
            "description": (
                "Independent NASA Space Apps Challenge 2026 entry. "
                "Not an official NASA product."
            ),
            "url": f"{SITE_URL}/",
        },
        "citation": "NASA Langley Research Center POWER Project",
    }


def _faq() -> dict[str, Any]:
    pairs = [
        (
            "What is Field Shift Rotation Explorer?",
            "A web tool that compares crop-rotation options using NASA POWER "
            "weather for a field you locate, built for NASA Space Apps 2026.",
        ),
        (
            "Does it replace an agronomist?",
            "No. Scores are conversation aids. Check results with local advice, "
            "soil tests, and what you see on the farm.",
        ),
        (
            "Which NASA data does it use?",
            "NASA POWER daily agroclimatology (temperature, rainfall, humidity, "
            "and solar) for the chosen latitude and longitude.",
        ),
        (
            "Where is farmer data stored?",
            "On the machine hosting the Field Shift service, in a local SQLite "
            "file and climate cache. The hosted service has no user accounts.",
        ),
    ]
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in pairs
        ],
    }


def graph_for(page: PageSEO) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": f"{SITE_URL}/",
            "description": SITE_DESCRIPTION,
            "inLanguage": "en",
            "publisher": {"@id": f"{SITE_URL}/#organization"},
        },
        {
            "@type": "Organization",
            "@id": f"{SITE_URL}/#organization",
            "name": "Field Shift",
            "url": f"{SITE_URL}/",
            "logo": {"@type": "ImageObject", "url": asset_url("icon-512.png")},
            "sameAs": ["https://github.com/0xUkobong/fieldshift"],
        },
        _software_application(),
        {
            "@type": "WebPage",
            "name": page.title,
            "url": absolute(page.path),
            "description": page.description,
            "isPartOf": {"@type": "WebSite", "url": absolute("/")},
            "inLanguage": "en",
            "primaryImageOfPage": asset_url(page.image),
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Explorer",
                    "item": absolute("/"),
                },
                *(
                    [
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": page.title.split("·")[0].strip(),
                            "item": absolute(page.path),
                        }
                    ]
                    if page.path != "/"
                    else []
                ),
            ],
        },
    ]
    if page.path == "/About":
        nodes.append(_faq())
    nodes.extend(page.extra_jsonld)
    return {"@context": "https://schema.org", "@graph": nodes}


def inject_seo(page: PageSEO) -> None:
    """Write title, description, Open Graph, Twitter, geo, and JSON-LD into the parent document."""
    page_url = absolute(page.path)
    image = asset_url(page.image)
    payload = {
        "title": page.title,
        "description": page.description,
        "keywords": page.keywords,
        "canonical": page_url,
        "locale": SITE_LOCALE,
        "ogType": page.type,
        "image": image,
        "siteName": SITE_NAME,
        "jsonld": graph_for(page),
        "icon": asset_url("favicon.png"),
        "appleIcon": asset_url("apple-touch-icon.png"),
        "manifest": asset_url("site.webmanifest"),
        "theme": "#1e1e1f",
    }
    blob = json.dumps(payload)
    components.html(
        f"""
<script>
(function () {{
  const d = window.parent.document;
  const head = d.head;
  const data = {blob};
  d.title = data.title;
  function upsert(sel, make) {{
    let el = head.querySelector(sel);
    if (!el) {{ el = make(); head.appendChild(el); }}
    return el;
  }}
  function meta(attr, key, content) {{
    const el = upsert('meta[' + attr + '="' + key + '"]', () => {{
      const m = d.createElement('meta');
      m.setAttribute(attr, key);
      return m;
    }});
    el.setAttribute('content', content);
  }}
  function link(rel, href, extra) {{
    const el = upsert('link[rel="' + rel + '"]' + (extra || ''), () => {{
      const n = d.createElement('link');
      n.setAttribute('rel', rel);
      return n;
    }});
    el.setAttribute('href', href);
  }}
  meta('name', 'description', data.description);
  meta('name', 'keywords', data.keywords);
  meta('name', 'author', 'Field Shift project');
  meta('name', 'robots', 'index, follow, max-image-preview:large');
  meta('name', 'googlebot', 'index, follow');
  meta('name', 'theme-color', data.theme);
  meta('name', 'application-name', 'Field Shift');
  meta('name', 'apple-mobile-web-app-title', 'Field Shift');
  meta('name', 'apple-mobile-web-app-capable', 'yes');
  meta('name', 'format-detection', 'telephone=no');
  meta('name', 'geo.region', '001');
  meta('name', 'geo.placename', 'Worldwide smallholder and family farms');
  meta('name', 'language', 'English');
  meta('name', 'content-language', 'en');
  meta('property', 'og:title', data.title);
  meta('property', 'og:description', data.description);
  meta('property', 'og:type', data.ogType);
  meta('property', 'og:url', data.canonical);
  meta('property', 'og:image', data.image);
  meta('property', 'og:image:width', '1200');
  meta('property', 'og:image:height', '630');
  meta('property', 'og:image:alt', 'Field Shift Rotation Explorer');
  meta('property', 'og:site_name', data.siteName);
  meta('property', 'og:locale', data.locale);
  meta('name', 'twitter:card', 'summary_large_image');
  meta('name', 'twitter:title', data.title);
  meta('name', 'twitter:description', data.description);
  meta('name', 'twitter:image', data.image);
  link('canonical', data.canonical);
  link('icon', data.icon);
  const apple = upsert('link[rel="apple-touch-icon"]', () => {{
    const n = d.createElement('link');
    n.setAttribute('rel', 'apple-touch-icon');
    return n;
  }});
  apple.setAttribute('href', data.appleIcon);
  const man = upsert('link[rel="manifest"]', () => {{
    const n = d.createElement('link');
    n.setAttribute('rel', 'manifest');
    return n;
  }});
  man.setAttribute('href', data.manifest);
  let ld = head.querySelector('script[data-fieldshift-jsonld]');
  if (!ld) {{
    ld = d.createElement('script');
    ld.type = 'application/ld+json';
    ld.setAttribute('data-fieldshift-jsonld', '1');
    head.appendChild(ld);
  }}
  ld.textContent = JSON.stringify(data.jsonld);
}})();
</script>
        """,
        height=0,
        width=0,
    )


def page_icon() -> str:
    return str(FAVICON_PATH) if FAVICON_PATH.exists() else "F"
