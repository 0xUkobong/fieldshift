# Field Shift · Rotation Explorer

Farmer-facing decision support for crop rotation, built for the NASA Space Apps Challenge 2026 challenge **Field Shift: Adapting Farms with NASA Data**.

Set a field, the current crop, and what matters on that farm. The app loads NASA POWER weather for that point, then compares three rotations with scores, charts, plain-language reasons, risks, and a shareable summary. It is a starting point for a conversation with local advice. It does not replace extension services, soil tests, or on-farm observation.

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

The default record is 2018–2025. A successful fetch is saved under `data/power_cache/` so the same point still works offline. Five demo sites ship with cached packs, including Kano / northern Nigeria and the West Africa maize belt. Custom latitude and longitude are supported; the first visit needs a network connection.

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
  config.py             demo farms, weights, disclaimer
data/power_cache/       offline POWER packs
doc/                    challenge notes and design write-up
tests/
```

## Share and languages

After a comparison, the app can download an SMS/USSD text, a printable farmer card, and full comparison notes. Share text is available in English, French, Kiswahili, and Hausa. Extension-worker mode can save several farmers on this device and download their SMS lines together.

## Disclaimer

Results come from satellite and model weather plus simple crop rules. They should not replace local agronomic advice or what you see in the field.
