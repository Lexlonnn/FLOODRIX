"""Configuration tunables for the Risk Engine and Route Recommender.

All values are overridable via environment variables and follow section 13 of risk_engine_plan.md.
All paths resolve via pathlib relative to the backend/ root.
"""

import os
from pathlib import Path
from typing import Dict, NamedTuple

# Base directory: backend/
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Static data paths
DATA_STATIC_DIR: Path = BASE_DIR / "data" / "static"
DATA_STATIC_DIR.mkdir(parents=True, exist_ok=True)

ELEVATION_CACHE_FILE: Path = DATA_STATIC_DIR / "elevation_cache.csv"
STATIC_LOOKUP_FILE: Path = DATA_STATIC_DIR / "static_lookup.parquet"
TRIPS_DB_FILE: Path = BASE_DIR / "data" / "trips.db"

# Core Segmentation & Grid Tunables
SEGMENT_LEN_M: float = float(os.getenv("SEGMENT_LEN_M", "500.0"))
CELL_KM: float = float(os.getenv("CELL_KM", "1.0"))
ROUTE_OVERLAP_DEDUPE_THRESH: float = float(os.getenv("ROUTE_OVERLAP_DEDUPE_THRESH", "0.90"))

# Risk Thresholds & Bands
P_BLOCK: float = float(os.getenv("P_BLOCK", "0.7"))
BAND_LOW: float = float(os.getenv("BAND_LOW", "0.3"))
BAND_HIGH: float = float(os.getenv("BAND_HIGH", "0.6"))

# Live Monitoring Triggers
LIVE_WARN_P: float = float(os.getenv("LIVE_WARN_P", "0.5"))
HEAVY_RAIN_1H: float = float(os.getenv("HEAVY_RAIN_1H", "15.0"))
LOOKAHEAD_MIN: int = int(os.getenv("LOOKAHEAD_MIN", "60"))
LOOKAHEAD_KM: float = float(os.getenv("LOOKAHEAD_KM", "40.0"))
OFF_ROUTE_M: float = float(os.getenv("OFF_ROUTE_M", "150.0"))
MIN_REROUTE_GAP_MIN: float = float(os.getenv("MIN_REROUTE_GAP_MIN", "5.0"))
REROUTE_MARGIN_MIN: float = float(os.getenv("REROUTE_MARGIN_MIN", "10.0"))
REROUTE_MARGIN_RATIO: float = float(os.getenv("REROUTE_MARGIN_RATIO", "0.15"))
CLOSURE_SNAP_M: float = float(os.getenv("CLOSURE_SNAP_M", "500.0"))

# Vehicle & Weather Factors
VEHICLE_SPEED_FACTOR: float = float(os.getenv("VEHICLE_SPEED_FACTOR", "1.25"))
RAIN_SAFETY_FACTOR: float = float(os.getenv("RAIN_SAFETY_FACTOR", "1.0"))
LATENESS_WEIGHT: float = float(os.getenv("LATENESS_WEIGHT", "3.0"))

# Delay Advisory Scan Settings
DELAY_SCAN_MAX_MIN: int = int(os.getenv("DELAY_SCAN_MAX_MIN", "360"))
DELAY_SCAN_STEP_MIN: int = int(os.getenv("DELAY_SCAN_STEP_MIN", "30"))

# Cache TTLs
WEATHER_CACHE_PLANNING_TTL_SEC: int = int(os.getenv("WEATHER_CACHE_PLANNING_TTL_SEC", "1800"))  # 30 min
WEATHER_CACHE_LIVE_TTL_SEC: int = int(os.getenv("WEATHER_CACHE_LIVE_TTL_SEC", "600"))  # 10 min
TRIP_TTL_HOURS: int = int(os.getenv("TRIP_TTL_HOURS", "24"))

# Routing Provider Selection
ROUTING_PROVIDER: str = os.getenv("ROUTING_PROVIDER", "mock")  # 'osrm', 'mock'
OSRM_URL: str = os.getenv("OSRM_URL", "http://router.project-osrm.org")

# Cargo Profiles
class CargoProfile(NamedTuple):
    delay_penalty_min: float
    risk_aversion: float

CARGO_PROFILES: Dict[str, CargoProfile] = {
    "general": CargoProfile(
        delay_penalty_min=float(os.getenv("CARGO_GENERAL_DELAY_PENALTY", "90.0")),
        risk_aversion=float(os.getenv("CARGO_GENERAL_RISK_AVERSION", "1.0")),
    ),
    "perishable": CargoProfile(
        delay_penalty_min=float(os.getenv("CARGO_PERISHABLE_DELAY_PENALTY", "180.0")),
        risk_aversion=float(os.getenv("CARGO_PERISHABLE_RISK_AVERSION", "1.5")),
    ),
    "fragile": CargoProfile(
        delay_penalty_min=float(os.getenv("CARGO_FRAGILE_DELAY_PENALTY", "150.0")),
        risk_aversion=float(os.getenv("CARGO_FRAGILE_RISK_AVERSION", "1.5")),
    ),
    "hazardous": CargoProfile(
        delay_penalty_min=float(os.getenv("CARGO_HAZARDOUS_DELAY_PENALTY", "240.0")),
        risk_aversion=float(os.getenv("CARGO_HAZARDOUS_RISK_AVERSION", "2.5")),
    ),
}

def get_cargo_profile(cargo: str) -> CargoProfile:
    """Return CargoProfile for cargo type with graceful default to 'general'."""
    return CARGO_PROFILES.get(cargo.lower(), CARGO_PROFILES["general"])
