"""Map viewport flood risk query endpoint."""

from fastapi import APIRouter, Query, Request
import numpy as np
from app.schemas import MapRiskResponse, MapRiskSegment, RiskLevelEnum, SegmentInput
from ml.config import get_risk_level

router = APIRouter(prefix="/map", tags=["Map Risk Overlay"])


@router.get("/risk", response_model=MapRiskResponse)
def get_map_risk(
    request: Request,
    min_lat: float = Query(..., description="South boundary"),
    max_lat: float = Query(..., description="North boundary"),
    min_lon: float = Query(..., description="West boundary"),
    max_lon: float = Query(..., description="East boundary"),
) -> MapRiskResponse:
    """Return flood-risk information across road points for visible map viewport."""
    predictor = getattr(request.app.state, "predictor", None)
    
    # Generate representative grid of road points within the viewport
    lats = np.linspace(min_lat, max_lat, 4)
    lons = np.linspace(min_lon, max_lon, 4)

    segments_input = []
    idx = 1
    for lat in lats:
        for lon in lons:
            segments_input.append(
                SegmentInput(
                    segment_id=f"MAP_SEG_{idx:03d}",
                    latitude=round(float(lat), 5),
                    longitude=round(float(lon), 5),
                    rainfall_1h=12.0,
                    rainfall_6h=35.0,
                    rainfall_24h=80.0,
                    elevation=8.0,
                    historical_flood_frequency=2,
                    flood_zone="medium",
                )
            )
            idx += 1

    if predictor and predictor.is_loaded:
        preds, _ = predictor.predict_segments(segments_input)
        map_segments = [
            MapRiskSegment(
                id=p.segment_id,
                latitude=p.latitude,
                longitude=p.longitude,
                flood_probability=p.flood_probability,
                risk_level=p.risk_level,
            )
            for p in preds
        ]
    else:
        map_segments = [
            MapRiskSegment(
                id=s.segment_id,
                latitude=s.latitude,
                longitude=s.longitude,
                flood_probability=0.25,
                risk_level=RiskLevelEnum.LOW,
            )
            for s in segments_input
        ]

    return MapRiskResponse(segments=map_segments)
