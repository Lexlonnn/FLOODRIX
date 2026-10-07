"""Unit tests for Pydantic v2 schemas and validation constraints."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    BatchSegmentsRequest,
    DecisionActionEnum,
    RiskLevelEnum,
    RoutePredictRequest,
    SegmentInput,
)


def test_segment_input_valid():
    seg = SegmentInput(
        segment_id="seg_01",
        latitude=10.0,
        longitude=76.3,
        rainfall_1h=10.0,
        rainfall_6h=30.0,
        rainfall_24h=70.0,
        elevation=15.0,
        historical_flood_frequency=2,
        flood_zone="high",
    )
    assert seg.segment_id == "seg_01"
    assert seg.latitude == 10.0
    assert seg.flood_zone == "high"


def test_segment_input_rejects_rainfall_ordering_1h_greater_than_6h():
    with pytest.raises(ValidationError, match="Rainfall ordering violated"):
        SegmentInput(
            segment_id="bad_01",
            latitude=10.0,
            longitude=76.3,
            rainfall_1h=50.0,
            rainfall_6h=30.0,  # 1h > 6h
            rainfall_24h=70.0,
            elevation=15.0,
            historical_flood_frequency=2,
            flood_zone="medium",
        )


def test_segment_input_rejects_rainfall_ordering_6h_greater_than_24h():
    with pytest.raises(ValidationError, match="Rainfall ordering violated"):
        SegmentInput(
            segment_id="bad_02",
            latitude=10.0,
            longitude=76.3,
            rainfall_1h=10.0,
            rainfall_6h=90.0,
            rainfall_24h=70.0,  # 6h > 24h
            elevation=15.0,
            historical_flood_frequency=2,
            flood_zone="medium",
        )


def test_segment_input_rejects_out_of_bounds_coords():
    with pytest.raises(ValidationError):
        SegmentInput(
            segment_id="bad_lat",
            latitude=18.5,  # Far outside Kerala
            longitude=76.3,
            rainfall_1h=10.0,
            rainfall_6h=20.0,
            rainfall_24h=30.0,
            elevation=10.0,
            historical_flood_frequency=0,
            flood_zone="low",
        )


def test_batch_segments_request_validation():
    valid_seg = SegmentInput(
        segment_id="s1",
        latitude=10.0,
        longitude=76.3,
        rainfall_1h=5.0,
        rainfall_6h=15.0,
        rainfall_24h=40.0,
        elevation=10.0,
        historical_flood_frequency=1,
        flood_zone="low",
    )
    req = BatchSegmentsRequest(segments=[valid_seg])
    assert len(req.segments) == 1

    # Empty batch rejected
    with pytest.raises(ValidationError):
        BatchSegmentsRequest(segments=[])
