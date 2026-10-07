"""Batch segment risk scorer interfacing with ML predictor and rule fallback."""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

from engine.config import BAND_HIGH, BAND_LOW, CLOSURE_SNAP_M
from engine.models import RiskBand, Segment
from engine.risk.rules import score_segment_rules

logger = logging.getLogger("floodrix.risk.scorer")


class SegmentRiskScorer:
    """Scores batches of road segments using trained ML models or heuristic fallback."""

    def __init__(self, predictor=None, closure_service=None):
        self.predictor = predictor
        self.closure_service = closure_service

    def score_segments(
        self,
        segments_raw: List[Dict],
        model_type: str = "full",  # 'full' or 'live'
    ) -> Tuple[List[Segment], str]:
        """Score all segments in a single batched vectorized inference pass.

        Returns:
        (scored_segments, source_used: 'ml_full' | 'ml_live' | 'rules')
        """
        if not segments_raw:
            return [], "none"

        # Check closures if service available
        closed_indices = set()
        if self.closure_service:
            for idx, s in enumerate(segments_raw):
                closure = self.closure_service.is_near_closure(
                    s["lat"], s["lon"], threshold_km=CLOSURE_SNAP_M / 1000.0
                )
                if closure:
                    closed_indices.add(idx)

        # Attempt ML Model inference
        probs: List[float] = []
        source_used = "rules"

        if self.predictor and getattr(self.predictor, "is_loaded", False):
            try:
                # Use shared build_features from ml.data_prep
                from ml.data_prep import build_features
                
                # Format dictionaries to match expected column names
                feat_inputs = []
                for s in segments_raw:
                    feat_inputs.append({
                        "latitude": s["lat"],
                        "longitude": s["lon"],
                        "rainfall_1h": s.get("rainfall_1h", 0.0),
                        "rainfall_6h": s.get("rainfall_6h", 0.0),
                        "rainfall_24h": s.get("rainfall_24h", 0.0),
                        "elevation": s.get("elevation", 10.0),
                        "historical_flood_frequency": s.get("historical_flood_frequency", 0.0),
                        "flood_zone": s.get("flood_zone", "low"),
                    })

                X = build_features(feat_inputs, feature_set=model_type if hasattr(self.predictor, "predict_live") else "full")

                # Single vectorized predict_proba call
                if model_type == "live" and hasattr(self.predictor, "predict_live_proba"):
                    raw_probs = self.predictor.predict_live_proba(X)
                    source_used = "ml_live"
                else:
                    raw_probs = self.predictor.model.predict_proba(X)[:, 1]
                    source_used = "ml_full"

                probs = [float(p) for p in raw_probs]
            except Exception as e:
                logger.warning(f"ML Predictor scoring failed ({e}). Falling back to rules engine.")
                probs = []

        if not probs:
            # Fallback to rules.py
            source_used = "rules"
            for s in segments_raw:
                p_rule = score_segment_rules(
                    rainfall_1h=s.get("rainfall_1h", 0.0),
                    rainfall_6h=s.get("rainfall_6h", 0.0),
                    rainfall_24h=s.get("rainfall_24h", 0.0),
                    elevation=s.get("elevation", 10.0),
                    historical_flood_frequency=s.get("historical_flood_frequency", 0.0),
                    flood_zone=s.get("flood_zone", 0.0),
                )
                probs.append(p_rule)

        # Assemble scored Segment models
        scored: List[Segment] = []
        for idx, (s, p) in enumerate(zip(segments_raw, probs)):
            is_closed = idx in closed_indices
            if is_closed:
                p = 1.0  # Closed segment forces p = 1.0

            if p < BAND_LOW:
                band = RiskBand.LOW
            elif p <= BAND_HIGH:
                band = RiskBand.MEDIUM
            else:
                band = RiskBand.HIGH

            seg = Segment(
                index=idx,
                lat=s["lat"],
                lon=s["lon"],
                length_m=s.get("length_m", 500.0),
                cum_dist_m=s.get("cum_dist_m", 0.0),
                cum_time_s=s.get("cum_time_s", 0.0),
                eta=s.get("eta", ""),
                elevation=round(s.get("elevation", 0.0), 1),
                rainfall_1h=round(s.get("rainfall_1h", 0.0), 2),
                rainfall_6h=round(s.get("rainfall_6h", 0.0), 2),
                rainfall_24h=round(s.get("rainfall_24h", 0.0), 2),
                historical_flood_frequency=round(s.get("historical_flood_frequency", 0.0), 1),
                flood_zone=round(s.get("flood_zone", 0.0), 1),
                static_missing=s.get("static_missing", False),
                p=round(p, 4),
                band=band,
                closed=is_closed,
            )
            scored.append(seg)

        return scored, source_used


def score_segments(
    data,
    predictor=None,
    mode: str = "full",
) -> Tuple[List[float], List[RiskBand]]:
    """Convenience function to score a DataFrame or list of dicts.

    Returns:
    (probabilities, risk_bands)
    """
    if isinstance(data, pd.DataFrame):
        records = data.to_dict(orient="records")
    else:
        records = [
            {
                "lat": getattr(s, "lat", s.get("lat", 0.0) if isinstance(s, dict) else 0.0),
                "lon": getattr(s, "lon", s.get("lon", 0.0) if isinstance(s, dict) else 0.0),
                "rainfall_1h": getattr(s, "rainfall_1h", s.get("rainfall_1h", 0.0) if isinstance(s, dict) else 0.0),
                "rainfall_6h": getattr(s, "rainfall_6h", s.get("rainfall_6h", 0.0) if isinstance(s, dict) else 0.0),
                "rainfall_24h": getattr(s, "rainfall_24h", s.get("rainfall_24h", 0.0) if isinstance(s, dict) else 0.0),
                "elevation": getattr(s, "elevation", s.get("elevation", 10.0) if isinstance(s, dict) else 10.0),
                "historical_flood_frequency": getattr(s, "historical_flood_frequency", s.get("historical_flood_frequency", 0.0) if isinstance(s, dict) else 0.0),
                "flood_zone": getattr(s, "flood_zone", s.get("flood_zone", 0.0) if isinstance(s, dict) else 0.0),
            }
            if not isinstance(s, dict) or "lat" not in s
            else s
            for s in data
        ]

    scorer = SegmentRiskScorer(predictor=predictor)
    scored, _ = scorer.score_segments(records, model_type=mode)
    probs = [s.p for s in scored]
    bands = [s.band for s in scored]
    return probs, bands

