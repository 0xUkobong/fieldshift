### File 4: `04_Data_Sources.md`

```markdown
# Data Sources

## Primary – NASA POWER (start here)
- Free API, no authentication required for basic use
- Excellent for temperature, precipitation, humidity, solar radiation
- Docs: https://power.larc.nasa.gov/api/pages/
- Tutorial: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/

### Example API Call (Daily Point)
https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M&community=AG&longitude=-95.36&latitude=29.76&start=20180101&end=20251231&format=JSON

### Key Parameters (AG community)
- T2M, T2M_MAX, T2M_MIN → temperature / heat stress / frost risk
- PRECTOTCORR → corrected precipitation
- RH2M → relative humidity
- ALLSKY_SFC_SW_DWN → solar radiation

## Secondary (optional / sample data)
- **SMAP** – soil moisture
- **ECOSTRESS** – land surface temperature, evaporative stress, water use
- **MODIS / Landsat** – NDVI / vegetation health

## Implementation Advice
- Use live POWER API for the prototype
- Pre-fetch or hard-code sample SMAP/ECOSTRESS values for 2–3 demo locations if live access is slow
- Always cite the data sources in the UI and project description