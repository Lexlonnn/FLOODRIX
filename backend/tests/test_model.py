"""Unit tests for calibrated model predictions, monotonic constraints, and risk bands."""

import joblib
import numpy as np
import pytest

from app.predictor import FloodPredictor
from app.schemas import RiskLevelEnum, SegmentInput
from ml.config import (
    MODEL_FILE,
    RISK_HIGH_THRESHOLD,
    RISK_LOW_THRESHOLD,
    get_risk_level,
)


@pytest.fixture(scope="module")
def loaded_predictor():
    pred = FloodPredictor()
    pred.load()
    return pred


def test_model_predictions_strictly_bounded(loaded_predictor):
    segments = [
        SegmentInput(
            segment_id=f"seg_{i}",
            latitude=10.0 + i * 0.1,
            longitude=76.2 + i * 0.05,
            rainfall_1h=float(i * 5),
            rainfall_6h=float(i * 15),
            rainfall_24h=float(i * 35),
            elevation=10.0,
            historical_flood_frequency=i % 4,
            flood_zone="medium",
        )
        for i in range(1, 6)
    ]

    preds, _ = loaded_predictor.predict_segments(segments)
    for p in preds:
        assert 0.0 <= p.flood_probability <= 1.0
        assert p.risk_level in [RiskLevelEnum.LOW, RiskLevelEnum.MEDIUM, RiskLevelEnum.HIGH]


def test_model_rainfall_monotonic_sanity(loaded_predictor):
    """Verify that increasing rainfall does not decrease flood probability."""
    dry_segment = SegmentInput(
        segment_id="dry",
        latitude=9.98,
        longitude=76.28,
        rainfall_1h=0.0,
        rainfall_6h=0.0,
        rainfall_24h=0.0,
        elevation=5.0,
        historical_flood_frequency=3,
        flood_zone="high",
    )

    moderate_segment = SegmentInput(
        segment_id="moderate",
        latitude=9.98,
        longitude=76.28,
        rainfall_1h=15.0,
        rainfall_6h=45.0,
        rainfall_24h=90.0,
        elevation=5.0,
        historical_flood_frequency=3,
        flood_zone="high",
    )

    deluge_segment = SegmentInput(
        segment_id="deluge",
        latitude=9.98,
        longitude=76.28,
        rainfall_1h=50.0,
        rainfall_6h=140.0,
        rainfall_24h=280.0,
        elevation=5.0,
        historical_flood_frequency=3,
        flood_zone="high",
    )

    preds, _ = loaded_predictor.predict_segments([dry_segment, moderate_segment, deluge_segment])
    p_dry, p_mod, p_deluge = preds[0].flood_probability, preds[1].flood_probability, preds[2].flood_probability

    assert p_mod >= p_dry - 1e-4, f"Moderate rain ({p_mod}) unexpectedly lower than dry ({p_dry})"
    assert p_deluge >= p_mod - 1e-4, f"Deluge rain ({p_deluge}) unexpectedly lower than moderate ({p_mod})"


def test_model_elevation_monotonic_sanity(loaded_predictor):
    """Verify that high elevation mitigates flooding compared to lowlands."""
    lowland = SegmentInput(
        segment_id="lowland",
        latitude=9.98,
        longitude=76.28,
        rainfall_1h=20.0,
        rainfall_6h=50.0,
        rainfall_24h=100.0,
        elevation=2.0,  # Coastal lowlands
        historical_flood_frequency=3,
        flood_zone="high",
    )

    highland = SegmentInput(
        segment_id="highland",
        latitude=9.98,
        longitude=76.28,
        rainfall_1h=20.0,
        rainfall_6h=50.0,
        rainfall_24h=100.0,
        elevation=850.0,  # Ghat hills
        historical_flood_frequency=3,
        flood_zone="high",
    )

    preds, _ = loaded_predictor.predict_segments([lowland, highland])
    p_lowland, p_highland = preds[0].flood_probability, preds[1].flood_probability

    assert p_lowland >= p_highland - 1e-4, f"Lowland ({p_lowland}) unexpectedly lower than highland ({p_highland})"


def test_risk_level_threshold_mapping():
    assert get_risk_level(0.10) == "LOW"
    assert get_risk_level(0.29) == "LOW"
    assert get_risk_level(0.30) == "MEDIUM"
    assert get_risk_level(0.55) == "MEDIUM"
    assert get_risk_level(0.60) == "MEDIUM"
    assert get_risk_level(0.61) == "HIGH"
    assert get_risk_level(0.95) == "HIGH"
