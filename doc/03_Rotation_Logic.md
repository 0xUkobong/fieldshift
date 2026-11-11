# Rotation Strategy Logic (Rule-Based)

## Rotation Options

| Rotation Option                  | Trigger Conditions                          | Main Benefits                              | Risks / Gaps                          |
|----------------------------------|---------------------------------------------|--------------------------------------------|---------------------------------------|
| Current rotation                 | Always shown as baseline                    | Familiar management & known yields         | May show rising heat/water stress     |
| Drought-tolerant + cover crop    | High max temps, low rainfall, or moisture trends | Lower water demand, better infiltration, soil cover | Market or equipment fit               |
| Nitrogen-fixing legume mix       | High soil-health / organic-matter priority  | N-fixing, organic matter, pest-cycle break | Yield or labor trade-offs possible    |
| Deep-rooting / forage mix        | Water-trend concern or erosion priority     | Better water access, erosion control, forage | Potential cash-crop reduction         |

## Scoring Example
Each rotation receives scores (1–5 or 0–100) for:
- Water resilience (derived from precip + temperature data)
- Soil health potential (based on crop characteristics)
- Priority match (user inputs)

Overall score = weighted average.  
Display the actual data evidence next to each score.

## Example Rule (pseudocode)
```python
if avg_t2m_max > threshold and precip_trend == "declining":
    recommend.append("Drought-tolerant + cover crop")
if "Improve soil organic matter" in priorities:
    recommend.append("Nitrogen-fixing legume mix")


