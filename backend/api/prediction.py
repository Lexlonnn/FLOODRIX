"""Prediction endpoints re-export."""
from api.v1.prediction import (
    predict_batch_segments,
    predict_route_risk,
    predict_route_segments,
    predict_single_point,
    router,
)

__all__ = [
    "router",
    "predict_single_point",
    "predict_route_risk",
    "predict_batch_segments",
    "predict_route_segments",
]
