"""Spatial block splitting to prevent geographic data leakage between train, calibration, and test splits."""

from typing import Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from ml.config import RANDOM_SEED, SPATIAL_GRID_SIZE, TARGET_COLUMN


def create_spatial_groups(
    df: pd.DataFrame,
    grid_size: float = SPATIAL_GRID_SIZE,
) -> pd.Series:
    """Discretize latitude/longitude into spatial grid blocks (~5 km cells).

    Points inside the same cell share a spatial group ID.
    """
    lat_indices = np.round(df["latitude"].values / grid_size).astype(int)
    lon_indices = np.round(df["longitude"].values / grid_size).astype(int)
    group_ids = [f"cell_{lat}_{lon}" for lat, lon in zip(lat_indices, lon_indices)]
    return pd.Series(group_ids, index=df.index, name="group_id")


def spatial_train_cal_test_split(
    df: pd.DataFrame,
    test_size: float = 0.20,
    cal_size: float = 0.25,  # 0.25 of 80% train_cal = 20% of total
    random_seed: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Perform leak-free spatial group-based splitting into train (60%), cal (20%), and test (20%).

    Guarantees that neighboring points within the same spatial grid block never leak
    across the train, calibration, or test sets.

    Returns:
    - (train_df, cal_df, test_df)
    """
    df = df.copy()
    if "group_id" not in df.columns:
        df["group_id"] = create_spatial_groups(df)

    groups = df["group_id"]

    # 1. Outer split: Hold out spatial test set (approx 20%)
    outer_splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_seed)
    train_cal_idx, test_idx = next(outer_splitter.split(df, groups=groups))

    train_cal_df = df.iloc[train_cal_idx].copy()
    test_df = df.iloc[test_idx].copy()

    # 2. Inner split: Divide remaining 80% into train (75% -> 60% total) and calibration (25% -> 20% total)
    inner_splitter = GroupShuffleSplit(n_splits=1, test_size=cal_size, random_state=random_seed)
    train_idx, cal_idx = next(inner_splitter.split(train_cal_df, groups=train_cal_df["group_id"]))

    train_df = train_cal_df.iloc[train_idx].copy()
    cal_df = train_cal_df.iloc[cal_idx].copy()

    # 3. Verify zero group overlap between all three splits
    train_groups = set(train_df["group_id"])
    cal_groups = set(cal_df["group_id"])
    test_groups = set(test_df["group_id"])

    overlap_train_test = train_groups & test_groups
    overlap_train_cal = train_groups & cal_groups
    overlap_cal_test = cal_groups & test_groups

    if overlap_train_test or overlap_train_cal or overlap_cal_test:
        raise ValueError(
            f"Spatial group leakage detected! "
            f"train/test: {len(overlap_train_test)}, "
            f"train/cal: {len(overlap_train_cal)}, "
            f"cal/test: {len(overlap_cal_test)}"
        )

    print("=== Spatial Group Split Summary ===")
    print(f"Total dataset: {len(df)} rows across {df['group_id'].nunique()} spatial cells")
    print(
        f"Train split:       {len(train_df):5d} rows ({len(train_df)/len(df):.1%}) | "
        f"{len(train_groups):3d} cells | Pos rate: {train_df[TARGET_COLUMN].mean():.2%}"
    )
    print(
        f"Calibration split: {len(cal_df):5d} rows ({len(cal_df)/len(df):.1%}) | "
        f"{len(cal_groups):3d} cells | Pos rate: {cal_df[TARGET_COLUMN].mean():.2%}"
    )
    print(
        f"Test split:        {len(test_df):5d} rows ({len(test_df)/len(df):.1%}) | "
        f"{len(test_groups):3d} cells | Pos rate: {test_df[TARGET_COLUMN].mean():.2%}"
    )

    return train_df, cal_df, test_df
