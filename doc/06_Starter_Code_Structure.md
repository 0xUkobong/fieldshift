# Code structure

```
fieldshift/
  app.py                         # Streamlit entry: streamlit run app.py
  requirements.txt
  tests/
    test_climate.py
    test_scoring.py
  rotation_explorer/
    __init__.py
    config.py                    # farms, NASA POWER params, scoring weights
    models.py                    # Farm, FarmSetup, ClimateSummary, RotationResult
    power.py                     # NASA POWER fetch + parse (no Streamlit)
    climate.py                   # annual/monthly indicators
    scoring.py                   # rule-based rotation scores
    charts.py                    # Plotly figures
    ui.py                        # Streamlit widgets and layout
    app.py                       # wires data → scores → UI
```

Run: `streamlit run app.py`  
Tests: `python -m pytest`
