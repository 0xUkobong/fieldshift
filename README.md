# Field Shift · Rotation Explorer

Farmer-facing decision support for crop rotation, built for the NASA Space Apps Challenge 2026 challenge **Field Shift: Adapting Farms with NASA Data**.

Locate a real field (continent, country, state, local government, area, or a map pin), set the current crop, and say what matters on that farm. The app loads NASA POWER weather for that point, then compares rotations with scores, charts, plain-language reasons, risks, and a shareable summary. It is a starting point for a conversation with local advice. It does not replace extension services, soil tests, or on-farm observation.

## What it compares

| Rotation | Role |
| --- | --- |
| Current rotation | Baseline the farmer already knows |
| Drought-tolerant + cover crop | Lower water demand and soil cover when heat or rainfall looks tight |
| Nitrogen-fixing legume mix | Soil organic matter and nitrogen when those are the priority |

Scores are rule-based (water resilience, soil-health potential, and priority match). Each explanation cites values from the climate record, not a black-box model.

## NASA data

Live requests use the [NASA POWER](https://power.larc.nasa.gov/) daily point API, agriculture community, with no API key:

- `T2M`, `T2M_MAX`, `T2M_MIN` — mean and extreme air temperature
- `PRECTOTCORR` — corrected precipitation

The default record is a rolling 7-year NASA POWER window. A successful fetch is saved under `data/power_cache/` so the same point still works offline. Saved fields and extension rosters are stored in `data/fieldshift.db` on the machine running the app. Example cache packs are optional; the app starts with no field selected.

This build does not include SMAP soil moisture or ECOSTRESS water-stress tiles.

## Run locally

Python 3.11+ is enough. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501).

The public launch page is in `public/index.html`. It contains crawlable product information, descriptions, Open Graph/Twitter tags, and JSON-LD. Brand assets, crawler files, and the app's page metadata live in `static/` and `rotation_explorer/seo.py`.

The production target is `https://fieldshift.cloud/`, deployed with the included Caddy front door. Caddy serves the static landing page and root-level crawler files, then proxies the interactive Streamlit explorer at `/explorer/`. See [`deploy/README.md`](deploy/README.md) for the server, DNS, and service setup.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Layout

```
app.py                  Streamlit entrypoint
rotation_explorer/
  app.py                wires inputs → POWER → scores → UI
  power.py              NASA POWER fetch and parse
  climate.py            annual and monthly indicators
  scoring.py            rotation scores
  insights.py           risks, timing, SMS and farmer card
  charts.py             Plotly figures
  ui.py                 Streamlit layout
  config.py             weights, crops, optional example fields
  geo.py                world place hierarchy and Nominatim
  store.py              saved fields and roster
data/power_cache/       offline POWER packs
doc/                    challenge notes and design write-up
tests/
```

## Share and languages

After a comparison, the app can download an SMS/USSD text, a printable farmer card, and full comparison notes. Share text is available in English, French, Kiswahili, and Hausa. Extension-worker mode can save several field records in the app's database and download their SMS lines together. On a hosted deployment, those records are stored on the service's machine; see the privacy page before entering field information.

## Disclaimer

Results come from satellite and model weather plus simple crop rules. They should not replace local agronomic advice or what you see in the field.
