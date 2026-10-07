"""Pydantic models for Risk Engine and Route Recommender."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CargoType(str, Enum):
    GENERAL = "general"
    PERISHABLE = "perishable"
    FRAGILE = "fragile"
    HAZARDOUS = "hazardous"


class AdvisoryType(str, Enum):
    GO = "GO"
    GO_WITH_CAUTION = "GO_WITH_CAUTION"
    DELAY = "DELAY"
    DO_NOT_GO = "DO_NOT_GO"


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    REROUTE = "REROUTE"
    HOLD = "HOLD"


class Coordinate(BaseModel):
    lat: float = Field(..., description="Latitude coordinate")
    lon: float = Field(..., description="Longitude coordinate")


class Segment(BaseModel):
    index: int
    lat: float
    lon: float
    length_m: float
    cum_dist_m: float
    cum_time_s: float
    eta: str
    elevation: float = 0.0
    rainfall_1h: float = 0.0
    rainfall_6h: float = 0.0
    rainfall_24h: float = 0.0
    historical_flood_frequency: float = 0.0
    flood_zone: float = 0.0
    static_missing: bool = False
    p: float = 0.0
    band: RiskBand = RiskBand.LOW
    closed: bool = False


class WorstSegment(BaseModel):
    index: int
    lat: float
    lon: float
    p: float
    band: RiskBand


class RouteMetrics(BaseModel):
    expected_disruptions: float
    p_any: float
    max_p: float
    high_risk_km: float
    n_high_cells: int
    closed_segments: int
    worst_segments: List[WorstSegment] = []


class GeoJSONGeometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]]  # [[lon, lat], ...]


class RouteOption(BaseModel):
    route_id: str
    label: str
    distance_km: float
    duration_min: float
    eta: str
    effective_time: float
    metrics: RouteMetrics
    reasons: List[str] = []
    geometry: GeoJSONGeometry
    segments: List[Segment]
    is_recommended: bool = False
    is_hard_filtered: bool = False


class PlanRouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    depart_time: Optional[str] = None  # ISO format string
    cargo: str = "general"
    deadline: Optional[str] = None     # ISO format string
    avoid_tolls: bool = False


class PlanRouteResponse(BaseModel):
    advisory: AdvisoryType
    recommended_route_id: Optional[str] = None
    routes: List[RouteOption]
    suggested_departure: Optional[str] = None
    generated_at: str
    data_sources: List[str] = []
    degraded: bool = False


class TripStartRequest(BaseModel):
    route_id: str
    cargo: str = "general"
    deadline: Optional[str] = None
    origin: Optional[Coordinate] = None
    destination: Optional[Coordinate] = None
    route_geometry: Optional[GeoJSONGeometry] = None
    initial_segments: Optional[List[Segment]] = None


class TripStartResponse(BaseModel):
    trip_id: str
    status: str
    started_at: str


class AlertItem(BaseModel):
    severity: AlertSeverity
    title: str
    message: str
    timestamp: str
    location: Optional[Coordinate] = None


class TripUpdateRequest(BaseModel):
    lat: float
    lon: float
    speed_kmh: Optional[float] = 0.0
    timestamp: Optional[str] = None


class TripUpdateResponse(BaseModel):
    trip_id: str
    status: str
    current_index: int
    snapped_lat: float
    snapped_lon: float
    distance_to_route_m: float
    is_off_route: bool
    alerts: List[AlertItem] = []
    reroute_offer: Optional[RouteOption] = None
    updated_eta: str
    risk_ahead_max_p: float
    risk_ahead_band: RiskBand
    next_poll_s: int


class ClosureCreateRequest(BaseModel):
    lat: float
    lon: float
    radius_m: float = 500.0
    reason: str
    expires_at: Optional[str] = None


class ClosureItem(BaseModel):
    id: str
    lat: float
    lon: float
    radius_m: float
    reason: str
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True


class EngineHealthResponse(BaseModel):
    status: str
    routing_provider: str
    weather_provider: str
    model_loaded: bool
    live_model_loaded: bool
    timestamp: str
