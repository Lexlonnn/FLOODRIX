"""Configuration and constants for Flood-Aware Predictive Logistics Planner.

All file paths resolve relative to the backend/ root directory using pathlib.
"""

from pathlib import Path
from typing import Dict, List

# Base directory: backend/
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR: Path = BASE_DIR / "data"
DATA_RAW_DIR: Path = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"
RAW_DATA_FILE: Path = DATA_RAW_DIR / "flood.csv"
PROCESSED_DATA_FILE: Path = DATA_PROCESSED_DIR / "features.parquet"
PROCESSED_CSV_FILE: Path = DATA_PROCESSED_DIR / "features.csv"

# Artifact paths
ARTIFACTS_DIR: Path = BASE_DIR / "ml" / "artifacts"
MODEL_FILE: Path = ARTIFACTS_DIR / "model.joblib"
RAW_MODEL_FILE: Path = ARTIFACTS_DIR / "model_raw.joblib"
BASELINE_MODEL_FILE: Path = ARTIFACTS_DIR / "baseline_model.joblib"
METADATA_FILE: Path = ARTIFACTS_DIR / "metadata.json"
METRICS_FILE: Path = ARTIFACTS_DIR / "metrics.json"
PLOTS_DIR: Path = ARTIFACTS_DIR / "plots"

# Live Model Artifacts (no history features)
LIVE_MODEL_FILE: Path = ARTIFACTS_DIR / "model_live.joblib"
LIVE_RAW_MODEL_FILE: Path = ARTIFACTS_DIR / "model_live_raw.joblib"
LIVE_METADATA_FILE: Path = ARTIFACTS_DIR / "metadata_live.json"
LIVE_METRICS_FILE: Path = ARTIFACTS_DIR / "metrics_live.json"

# Ensure runtime directories exist
for path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, ARTIFACTS_DIR, PLOTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Geographic bounding box for Kerala (~8.2 - 12.8 N, 74.8 - 77.4 E)
KERALA_LAT_MIN: float = 8.18
KERALA_LAT_MAX: float = 12.85
KERALA_LON_MIN: float = 74.80
KERALA_LON_MAX: float = 77.45

# Spatial block discretization size (~0.05 degrees ~= 5.5 km)
SPATIAL_GRID_SIZE: float = 0.05

# Categorical Flood Zone mapping (Ordinal encoding)
FLOOD_ZONE_MAP: Dict[str, int] = {
    "low": 0,
    "med": 1,
    "medium": 1,
    "high": 2,
    "extreme": 3,
    "very_high": 3,
}

# Risk Bands
RISK_LOW_THRESHOLD: float = 0.30
RISK_HIGH_THRESHOLD: float = 0.60

def get_risk_level(probability: float) -> str:
    """Return risk band category for a given flood probability."""
    if probability < RISK_LOW_THRESHOLD:
        return "LOW"
    elif probability <= RISK_HIGH_THRESHOLD:
        return "MEDIUM"
    return "HIGH"

# Target variable
TARGET_COLUMN: str = "flood_occurred"

# Raw feature columns expected in dataset / API input
RAW_FEATURE_COLUMNS: List[str] = [
    "latitude",
    "longitude",
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "elevation",
    "historical_flood_frequency",
    "flood_zone",
]

# Engineered feature columns
ENGINEERED_FEATURE_COLUMNS: List[str] = [
    "rain_intensity_ratio",
    "rain_6h_share",
    "rain_x_freq",
    "low_elev_rain",
    "flood_zone_encoded",
]

# Final ordered features fed to the ML estimator (Full Model)
MODEL_FEATURE_COLUMNS: List[str] = [
    "latitude",
    "longitude",
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "elevation",
    "historical_flood_frequency",
    "rain_intensity_ratio",
    "rain_6h_share",
    "rain_x_freq",
    "low_elev_rain",
    "flood_zone_encoded",
]

# Monotone constraints for XGBoost (+1: increasing, -1: decreasing, 0: unconstrained)
MONOTONE_CONSTRAINTS: Dict[str, int] = {
    "latitude": 0,
    "longitude": 0,
    "rainfall_1h": 1,
    "rainfall_6h": 1,
    "rainfall_24h": 1,
    "elevation": -1,
    "historical_flood_frequency": 1,
    "rain_intensity_ratio": 1,
    "rain_6h_share": 1,
    "rain_x_freq": 1,
    "low_elev_rain": 1,
    "flood_zone_encoded": 1,
}

# Live features (drops historical_flood_frequency, flood_zone, rain_x_freq)
MODEL_FEATURE_COLUMNS_LIVE: List[str] = [
    "latitude",
    "longitude",
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "elevation",
    "rain_intensity_ratio",
    "rain_6h_share",
    "low_elev_rain",
]

MONOTONE_CONSTRAINTS_LIVE: Dict[str, int] = {
    "latitude": 0,
    "longitude": 0,
    "rainfall_1h": 1,
    "rainfall_6h": 1,
    "rainfall_24h": 1,
    "elevation": -1,
    "rain_intensity_ratio": 1,
    "rain_6h_share": 1,
    "low_elev_rain": 1,
}

# Random seed
RANDOM_SEED: int = 42
