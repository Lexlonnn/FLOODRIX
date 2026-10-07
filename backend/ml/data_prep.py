"""Data ingestion, validation, and deterministic feature engineering.

Shared across offline ML training, calibration, evaluation, and live FastAPI serving.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ml.config import (
    FLOOD_ZONE_MAP,
    KERALA_LAT_MAX,
    KERALA_LAT_MIN,
    KERALA_LON_MAX,
    KERALA_LON_MIN,
    MODEL_FEATURE_COLUMNS,
    RAW_DATA_FILE,
    RAW_FEATURE_COLUMNS,
    TARGET_COLUMN,
)


class DataValidationError(ValueError):
    """Raised when data fails physical or schema validation checks."""
    pass


def load_raw_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """Load raw dataset from CSV file."""
    path = file_path or RAW_DATA_FILE
    df = pd.read_csv(path)
    # Standardize column names to lowercase snake_case
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def validate_data(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """Validate data against geographic, physical, and domain rules.

    Checks:
    - Required columns present
    - No null values
    - Latitude/Longitude within Kerala bounds
    - Non-negative rainfall and elevation
    - Rainfall monotonicity: 1h <= 6h <= 24h
    - Target column is binary 0/1 (if training)
    """
    df = df.copy()

    # Column case normalization
    df.columns = [c.strip().lower() for c in df.columns]

    # Required columns check
    required_cols = list(RAW_FEATURE_COLUMNS)
    if is_training:
        required_cols.append(TARGET_COLUMN)

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")

    # Nulls and duplicates check
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        raise DataValidationError(f"Null values detected in columns: {null_counts[null_counts > 0].to_dict()}")

    if is_training:
        df = df.drop_duplicates(subset=RAW_FEATURE_COLUMNS)

    # Kerala bounds validation
    invalid_lat = (df["latitude"] < KERALA_LAT_MIN) | (df["latitude"] > KERALA_LAT_MAX)
    invalid_lon = (df["longitude"] < KERALA_LON_MIN) | (df["longitude"] > KERALA_LON_MAX)
    if invalid_lat.any() or invalid_lon.any():
        bad_count = (invalid_lat | invalid_lon).sum()
        raise DataValidationError(
            f"{bad_count} rows fall outside Kerala geographic bounds "
            f"([{KERALA_LAT_MIN}, {KERALA_LAT_MAX}], [{KERALA_LON_MIN}, {KERALA_LON_MAX}])."
        )

    # Non-negative check
    for col in ["rainfall_1h", "rainfall_6h", "rainfall_24h"]:
        if (df[col] < 0).any():
            raise DataValidationError(f"Negative values detected in rainfall column '{col}'.")

    # Rainfall monotonicity: 1h <= 6h <= 24h (allow tiny floating point tolerance)
    tol = 1e-4
    violates_1_6 = df["rainfall_1h"] > (df["rainfall_6h"] + tol)
    violates_6_24 = df["rainfall_6h"] > (df["rainfall_24h"] + tol)
    if violates_1_6.any() or violates_6_24.any():
        bad_rows = (violates_1_6 | violates_6_24).sum()
        raise DataValidationError(
            f"Rainfall monotonicity violated in {bad_rows} rows: must satisfy rainfall_1h <= rainfall_6h <= rainfall_24h."
        )

    # Elevation check (lowest land in Kerala is Kuttanad at approx -2.2m below sea level)
    if (df["elevation"] < -5.0).any():
        raise DataValidationError("Elevation below -5.0m detected.")

    # Target check for training
    if is_training:
        unique_targets = set(df[TARGET_COLUMN].unique())
        if not unique_targets.issubset({0, 1}):
            raise DataValidationError(f"Target '{TARGET_COLUMN}' must be binary 0 or 1. Found: {unique_targets}")

    return df


def encode_flood_zone(zone_series: pd.Series) -> pd.Series:
    """Map flood zone categorical labels to ordinal integers."""
    return zone_series.astype(str).str.lower().str.strip().map(
        lambda z: FLOOD_ZONE_MAP.get(z, FLOOD_ZONE_MAP["low"])
    ).astype(int)


def build_features(
    data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
    return_target: bool = False,
    feature_set: str = "full",
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.Series]]:
    """Deterministically engineer features for both training and real-time inference.

    Features generated:
    1. rain_intensity_ratio = rainfall_1h / (rainfall_24h + eps)
    2. rain_6h_share        = rainfall_6h / (rainfall_24h + eps)
    3. rain_x_freq          = rainfall_24h * historical_flood_frequency (full mode only)
    4. low_elev_rain        = rainfall_24h / (max(elevation, 0.0) + 1.0)
    5. flood_zone_encoded   = ordinal integer map (full mode only)

    feature_set:
    - 'full': uses all features including history & static zone (MODEL_FEATURE_COLUMNS)
    - 'live': drops historical_flood_frequency, flood_zone, and rain_x_freq (MODEL_FEATURE_COLUMNS_LIVE)
    """
    from ml.config import MODEL_FEATURE_COLUMNS_LIVE

    eps = 1e-5

    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError(f"Unsupported data type for build_features: {type(data)}")

    # Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Convert numeric fields
    for col in ["latitude", "longitude", "rainfall_1h", "rainfall_6h", "rainfall_24h", "elevation"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 1. Intensity ratio
    df["rain_intensity_ratio"] = df["rainfall_1h"] / (df["rainfall_24h"] + eps)

    # 2. 6h rainfall share
    df["rain_6h_share"] = df["rainfall_6h"] / (df["rainfall_24h"] + eps)

    # 3. Low elevation rainfall vulnerability
    effective_elevation = np.maximum(df["elevation"].values, 0.0)
    df["low_elev_rain"] = df["rainfall_24h"] / (effective_elevation + 1.0)

    if feature_set == "live":
        target_columns = MODEL_FEATURE_COLUMNS_LIVE
    else:
        target_columns = MODEL_FEATURE_COLUMNS
        if "historical_flood_frequency" in df.columns:
            df["historical_flood_frequency"] = pd.to_numeric(df["historical_flood_frequency"], errors="coerce").fillna(0.0)
        else:
            df["historical_flood_frequency"] = 0.0

        # Rainfall x Historical flood frequency interaction
        df["rain_x_freq"] = df["rainfall_24h"] * df["historical_flood_frequency"]

        # Flood zone ordinal encoding
        if "flood_zone" in df.columns:
            df["flood_zone_encoded"] = encode_flood_zone(df["flood_zone"])
        else:
            df["flood_zone_encoded"] = 0

    # Ensure all target model features exist
    for col in target_columns:
        if col not in df.columns:
            raise KeyError(f"Feature '{col}' missing after feature engineering for feature_set='{feature_set}'.")

    # Reorder columns strictly
    X = df[target_columns].copy()

    if return_target:
        if TARGET_COLUMN not in df.columns:
            raise KeyError(f"Target column '{TARGET_COLUMN}' not present in provided data.")
        y = df[TARGET_COLUMN].astype(int)
        return X, y

    return X


def calculate_class_balance(y: pd.Series) -> Dict[str, Any]:
    """Compute class imbalance metrics for scale_pos_weight calculation."""
    num_pos = int((y == 1).sum())
    num_neg = int((y == 0).sum())
    total = len(y)
    pos_rate = float(num_pos / total) if total > 0 else 0.0
    scale_pos_weight = float(num_neg / num_pos) if num_pos > 0 else 1.0

    return {
        "total_samples": total,
        "positive_count": num_pos,
        "negative_count": num_neg,
        "positive_rate": round(pos_rate, 4),
        "scale_pos_weight": round(scale_pos_weight, 4),
    }
