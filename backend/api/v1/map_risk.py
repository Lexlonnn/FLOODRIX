"""FLOODRIX API v1 - Map risk overlay endpoint."""

from fastapi import APIRouter, Query, Request
import numpy as np
from app.schemas import MapRiskResponse, MapRiskSegment, RiskLevelEnum, SegmentInput

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

    # Create a dummy "severe flood" cluster
    map_segments = []
    
    # 1. High risk cluster around Ernakulam / Alappuzha (Approx 9.5 to 10.1, 76.2 to 76.5)
    cluster_center_lat = (min_lat + max_lat) / 2
    cluster_center_lon = (min_lon + max_lon) / 2
    
    import random
    random.seed(42)
    
    # Generate 50 random spots around the center
    for i in range(50):
        lat_offset = random.uniform(-0.15, 0.15)
        lon_offset = random.uniform(-0.15, 0.15)
        dist = (lat_offset**2 + lon_offset**2)**0.5
        
        # Closer to center = higher risk
        if dist < 0.05:
            prob = random.uniform(0.7, 0.99)
            lvl = RiskLevelEnum.HIGH
        elif dist < 0.1:
            prob = random.uniform(0.4, 0.69)
            lvl = RiskLevelEnum.MEDIUM
        else:
            prob = random.uniform(0.1, 0.39)
            lvl = RiskLevelEnum.LOW
            
        map_segments.append(
            MapRiskSegment(
                id=f"TEST_ZONE_{i}",
                latitude=cluster_center_lat + lat_offset,
                longitude=cluster_center_lon + lon_offset,
                flood_probability=prob,
                risk_level=lvl,
            )
        )

    return MapRiskResponse(segments=map_segments)
