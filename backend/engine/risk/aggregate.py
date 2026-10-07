"""Aggregates segment-level predictions into 1 km spatial risk cells and route-level metrics."""

from typing import Dict, List, Tuple
import numpy as np

from engine.config import BAND_HIGH, BAND_LOW, CELL_KM
from engine.models import RiskBand, RouteMetrics, Segment, WorstSegment

KM_PER_LAT = 110.8
KM_PER_LON = 109.4


def aggregate_route_risk(segments: List[Segment]) -> RouteMetrics:
    """Collapse consecutive segments into 1 km spatial grid cells and compute risk metrics.

    Prevents the independence trap where long routes are unfairly penalized simply
    due to having higher segment sample counts.
    """
    if not segments:
        return RouteMetrics(
            expected_disruptions=0.0,
            p_any=0.0,
            max_p=0.0,
            high_risk_km=0.0,
            n_high_cells=0,
            closed_segments=0,
            worst_segments=[],
        )

    # 1. Group segments into 1 km grid cells
    cell_max_p: Dict[Tuple[int, int], float] = {}
    for seg in segments:
        cell_x = int(round((seg.lat * KM_PER_LAT) / CELL_KM))
        cell_y = int(round((seg.lon * KM_PER_LON) / CELL_KM))
        key = (cell_x, cell_y)
        cell_max_p[key] = max(cell_max_p.get(key, 0.0), seg.p)

    cell_probs = np.array(list(cell_max_p.values()))

    # 2. Compute aggregate metrics
    expected_disruptions = float(np.sum(cell_probs))

    # p_any = 1 - prod(1 - p_cell)
    clipped_probs = np.clip(cell_probs, 0.0, 0.99999)
    p_any = 1.0 - float(np.exp(np.sum(np.log(1.0 - clipped_probs))))
    p_any = float(np.clip(p_any, 0.0, 1.0))

    max_p = float(max(seg.p for seg in segments))
    high_risk_km = float(sum(seg.length_m for seg in segments if seg.p > BAND_HIGH) / 1000.0)
    n_high_cells = int(sum(1 for p_val in cell_probs if p_val > BAND_HIGH))
    closed_count = int(sum(1 for seg in segments if seg.closed))

    # Worst segments (top 5 with p >= BAND_LOW)
    candidates = [
        WorstSegment(
            index=s.index,
            lat=s.lat,
            lon=s.lon,
            p=round(s.p, 4),
            band=s.band,
        )
        for s in segments
        if s.p >= BAND_LOW
    ]
    sorted_worst = sorted(candidates, key=lambda x: x.p, reverse=True)[:5]

    return RouteMetrics(
        expected_disruptions=round(expected_disruptions, 2),
        p_any=round(p_any, 4),
        max_p=round(max_p, 4),
        high_risk_km=round(high_risk_km, 2),
        n_high_cells=n_high_cells,
        closed_segments=closed_count,
        worst_segments=sorted_worst,
    )
