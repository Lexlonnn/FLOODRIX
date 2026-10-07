"""Inference engine wrapper with high-throughput vectorized predictions and route risk aggregation."""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd

from app.schemas import (
    DecisionActionEnum,
    RiskLevelEnum,
    RoutePredictResponse,
    SegmentInput,
    SegmentPrediction,
    WorstSegment,
)
from ml.config import (
    METADATA_FILE,
    MODEL_FILE,
    RISK_HIGH_THRESHOLD,
    RISK_LOW_THRESHOLD,
    get_risk_level,
)
from ml.data_prep import build_features


class FloodPredictor:
    """Production inference wrapper for calibrated flood risk predictions."""

    def __init__(self, model_path: Optional[Path] = None, metadata_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_FILE
        self.metadata_path = metadata_path or METADATA_FILE
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self._is_loaded = False

    def load(self) -> None:
        """Load model and metadata artifacts into memory. Fails loudly if missing."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact missing at '{self.model_path}'. "
                f"Please run model training and calibration pipeline first: "
                f"python -m ml.train && python -m ml.calibrate"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata artifact missing at '{self.metadata_path}'. "
                f"Please run model evaluation first: python -m ml.evaluate"
            )

        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

        self._is_loaded = True
        print(f"Successfully loaded calibrated model ({self.metadata.get('version', '1.0.0')}) into memory.")

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def predict_segments(
        self,
        segments: List[SegmentInput],
    ) -> Tuple[List[SegmentPrediction], float]:
        """Perform vectorized batch inference across hundreds of road segments in single-digit ms."""
        if not self._is_loaded:
            raise RuntimeError("Model is not loaded. Call predictor.load() during application lifespan.")

        t0 = time.perf_counter()

        # Vectorized feature conversion - single DataFrame, zero row loops
        dicts = [s.model_dump() for s in segments]
        X = build_features(dicts)

        # Single vectorized model predict_proba call
        probs = self.model.predict_proba(X)[:, 1]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        predictions: List[SegmentPrediction] = []
        for segment, prob in zip(segments, probs):
            p_val = float(np.clip(prob, 0.0, 1.0))
            level_str = get_risk_level(p_val)
            predictions.append(
                SegmentPrediction(
                    segment_id=str(segment.segment_id or "seg"),
                    latitude=segment.latitude,
                    longitude=segment.longitude,
                    flood_probability=round(p_val, 4),
                    risk_level=RiskLevelEnum(level_str),
                )
            )

        return predictions, round(elapsed_ms, 2)

    def predict_route(
        self,
        route_id: str,
        segments: List[SegmentInput],
    ) -> RoutePredictResponse:
        """Score ordered route segments and aggregate route-level risk and logistics action."""
        predictions, elapsed_ms = self.predict_segments(segments)

        probs = np.array([p.flood_probability for p in predictions])
        
        # Aggregated route risk: 1 - prod(1 - p_i)
        # Numerical stability with log1p: 1 - exp(sum(log(1 - p_i)))
        clipped_probs = np.clip(probs, 0.0, 0.99999)
        route_risk = 1.0 - float(np.exp(np.sum(np.log(1.0 - clipped_probs))))
        route_risk = float(np.clip(route_risk, 0.0, 1.0))

        max_risk = float(np.max(probs)) if len(probs) > 0 else 0.0
        high_risk_count = int(np.sum(probs > RISK_HIGH_THRESHOLD))

        # Sort worst segments by flood_probability descending
        sorted_preds = sorted(predictions, key=lambda x: x.flood_probability, reverse=True)
        worst_segments = [
            WorstSegment(
                segment_id=p.segment_id,
                latitude=p.latitude,
                longitude=p.longitude,
                flood_probability=p.flood_probability,
                risk_level=p.risk_level,
            )
            for p in sorted_preds[:5]
            if p.flood_probability >= RISK_LOW_THRESHOLD
        ]

        # Action determination policy
        if max_risk > RISK_HIGH_THRESHOLD or high_risk_count >= 2 or route_risk > 0.65:
            action = DecisionActionEnum.REROUTE
        elif route_risk > RISK_LOW_THRESHOLD or max_risk > RISK_LOW_THRESHOLD:
            action = DecisionActionEnum.WAIT
        else:
            action = DecisionActionEnum.GO

        return RoutePredictResponse(
            route_id=route_id,
            segments=predictions,
            route_risk=round(route_risk, 4),
            max_segment_risk=round(max_risk, 4),
            high_risk_segment_count=high_risk_count,
            worst_segments=worst_segments,
            recommended_action=action,
            risk_independence_note=(
                "Route risk is computed as 1 - prod(1 - p_i), assuming spatial independence "
                "between flood occurrences across distinct road segments."
            ),
            latency_ms=elapsed_ms,
        )
