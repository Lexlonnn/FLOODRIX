"""Rule-based heuristic flood risk scorer as fallback when ML models are unavailable."""

import math
from typing import Dict, List


def score_segment_rules(
    rainfall_1h: float,
    rainfall_6h: float,
    rainfall_24h: float,
    elevation: float,
    historical_flood_frequency: float = 0.0,
    flood_zone: float = 0.0,
) -> float:
    """Logistic heuristic nowcast: weighted normalized rain, rise trend, and elevation.

    Documented as rule-based fallback in risk_engine_plan.md section 3.
    """
    # 1. Normalized rainfall factors
    norm_r1 = rainfall_1h / 30.0    # 30 mm/h is very heavy cloudburst
    norm_r24 = rainfall_24h / 115.0  # 115 mm/24h is IMD heavy rain threshold

    # 2. Rain rise trend (burst intensity vs 6h total)
    rain_trend = (rainfall_1h * 6.0) / (rainfall_6h + 1e-4)
    rain_trend = min(rain_trend, 3.0)

    # 3. Low elevation vulnerability (lowlands < 15m heavily penalized)
    low_elev_factor = 1.0 / (max(elevation, 0.0) / 15.0 + 1.0)

    # 4. Latent logit
    z = (
        -3.5
        + 2.2 * norm_r24
        + 1.5 * norm_r1
        + 0.6 * (rain_trend - 1.0)
        + 1.8 * low_elev_factor
        + 0.15 * min(historical_flood_frequency, 8.0)
        + 0.35 * min(flood_zone, 3.0)
    )

    # Sigmoid
    p = 1.0 / (1.0 + math.exp(-z))
    return round(float(max(0.0, min(1.0, p))), 4)


def score_batch_rules(segments_data: List[Dict]) -> List[float]:
    """Score a list of segment dictionaries using rule-based fallback."""
    return [
        score_segment_rules(
            rainfall_1h=s.get("rainfall_1h", 0.0),
            rainfall_6h=s.get("rainfall_6h", 0.0),
            rainfall_24h=s.get("rainfall_24h", 0.0),
            elevation=s.get("elevation", 10.0),
            historical_flood_frequency=s.get("historical_flood_frequency", 0.0),
            flood_zone=s.get("flood_zone", 0.0),
        )
        for s in segments_data
    ]
