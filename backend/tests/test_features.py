"""Unit tests for data validation and deterministic feature engineering."""

import numpy as np
import pandas as pd
import pytest

from ml.config import (
    FLOOD_ZONE_MAP,
    KERALA_LAT_MAX,
    KERALA_LAT_MIN,
    KERALA_LON_MAX,
    KERALA_LON_MIN,
    MODEL_FEATURE_COLUMNS,
)
from ml.data_prep import (
    DataValidationError,
    build_features,
    calculate_class_balance,
    validate_data,
)


@pytest.fixture
def sample_valid_row():
    return {
        "latitude": 9.9812,
        "longitude": 76.2845,
        "rainfall_1h": 15.0,
        "rainfall_6h": 45.0,
        "rainfall_24h": 110.0,
        "elevation": 4.5,
        "historical_flood_frequency": 3,
        "flood_zone": "high",
        "flood_occurred": 1,
    }


def test_build_features_column_order_and_types(sample_valid_row):
    X = build_features([sample_valid_row])
    assert list(X.columns) == MODEL_FEATURE_COLUMNS
    assert len(X) == 1
    assert not X.isnull().values.any()


def test_build_features_calculations(sample_valid_row):
    X = build_features([sample_valid_row])
    eps = 1e-5

    expected_ratio = 15.0 / (110.0 + eps)
    expected_share = 45.0 / (110.0 + eps)
    expected_freq = 110.0 * 3
    expected_low_elev = 110.0 / (4.5 + 1.0)
    expected_zone = FLOOD_ZONE_MAP["high"]

    assert np.isclose(X["rain_intensity_ratio"].iloc[0], expected_ratio, atol=1e-5)
    assert np.isclose(X["rain_6h_share"].iloc[0], expected_share, atol=1e-5)
    assert np.isclose(X["rain_x_freq"].iloc[0], expected_freq, atol=1e-5)
    assert np.isclose(X["low_elev_rain"].iloc[0], expected_low_elev, atol=1e-5)
    assert X["flood_zone_encoded"].iloc[0] == expected_zone


def test_build_features_zero_values_no_division_by_zero():
    zero_row = {
        "latitude": 10.0,
        "longitude": 76.0,
        "rainfall_1h": 0.0,
        "rainfall_6h": 0.0,
        "rainfall_24h": 0.0,
        "elevation": 0.0,
        "historical_flood_frequency": 0,
        "flood_zone": "low",
    }
    X = build_features([zero_row])
    assert not X.isnull().values.any()
    assert not np.isinf(X.values).any()
    assert X["rain_intensity_ratio"].iloc[0] == 0.0
    assert X["low_elev_rain"].iloc[0] == 0.0


def test_validate_data_rejects_out_of_bounds_kerala(sample_valid_row):
    bad_row = sample_valid_row.copy()
    bad_row["latitude"] = 28.61  # Delhi
    df = pd.DataFrame([bad_row])
    with pytest.raises(DataValidationError, match="outside Kerala geographic bounds"):
        validate_data(df, is_training=True)


def test_validate_data_rejects_non_monotonic_rainfall(sample_valid_row):
    bad_row = sample_valid_row.copy()
    bad_row["rainfall_1h"] = 80.0
    bad_row["rainfall_6h"] = 40.0  # 1h > 6h
    df = pd.DataFrame([bad_row])
    with pytest.raises(DataValidationError, match="Rainfall monotonicity violated"):
        validate_data(df, is_training=True)


def test_validate_data_rejects_negative_rainfall(sample_valid_row):
    bad_row = sample_valid_row.copy()
    bad_row["rainfall_1h"] = -5.0
    df = pd.DataFrame([bad_row])
    with pytest.raises(DataValidationError, match="Negative values detected"):
        validate_data(df, is_training=True)


def test_calculate_class_balance():
    y = pd.Series([1, 0, 0, 0, 1])
    stats = calculate_class_balance(y)
    assert stats["positive_count"] == 2
    assert stats["negative_count"] == 3
    assert stats["positive_rate"] == 0.4
    assert stats["scale_pos_weight"] == 1.5
