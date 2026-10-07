"""Build static lookup grid (0.01 deg resolution) using Inverse Distance Weighting (IDW max 5 km)."""

import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from engine.config import STATIC_LOOKUP_FILE
from ml.config import (
    KERALA_LAT_MAX,
    KERALA_LAT_MIN,
    KERALA_LON_MAX,
    KERALA_LON_MIN,
)


def build_static_lookup(
    source_csv: Path,
    output_parquet: Path = STATIC_LOOKUP_FILE,
    grid_res: float = 0.01,
    max_radius_km: float = 5.0,
):
    """Interpolate historical_flood_frequency and flood_zone onto a 0.01 deg grid."""
    print(f"Reading source data from '{source_csv}'...")
    df = pd.read_csv(source_csv)

    # Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Clean and aggregate per unique location
    grouped = df.groupby(["latitude", "longitude"]).agg({
        "historical_flood_frequency": "mean",
        "flood_zone": lambda s: pd.to_numeric(s, errors="coerce").fillna(0).mean(),
    }).reset_index()

    station_lats = grouped["latitude"].values
    station_lons = grouped["longitude"].values
    station_freqs = grouped["historical_flood_frequency"].values
    station_zones = grouped["flood_zone"].values

    print(f"Aggregated {len(grouped)} distinct station locations.")

    # Convert lat/lon to approximate planar coordinates in km for fast KDTree search
    # Center around Kerala mid-latitude ~ 10.5 N (1 deg lat ~= 110.8 km, 1 deg lon ~= 109.4 km)
    KM_PER_LAT = 110.8
    KM_PER_LON = 109.4

    station_coords_km = np.column_stack([
        station_lats * KM_PER_LAT,
        station_lons * KM_PER_LON,
    ])
    tree = KDTree(station_coords_km)

    # Generate grid covering Kerala bounds with margin
    grid_lats = np.arange(KERALA_LAT_MIN, KERALA_LAT_MAX, grid_res)
    grid_lons = np.arange(KERALA_LON_MIN, KERALA_LON_MAX, grid_res)

    mesh_lats, mesh_lons = np.meshgrid(grid_lats, grid_lons)
    flat_lats = mesh_lats.ravel()
    flat_lons = mesh_lons.ravel()

    grid_coords_km = np.column_stack([
        flat_lats * KM_PER_LAT,
        flat_lons * KM_PER_LON,
    ])

    print(f"Querying KDTree for {len(flat_lats)} candidate grid points within {max_radius_km} km radius...")
    # Find all stations within max_radius_km for each grid point
    neighbor_indices = tree.query_ball_point(grid_coords_km, r=max_radius_km)

    valid_records = []
    for idx, neighbors in enumerate(neighbor_indices):
        if not neighbors:
            continue  # Outside 5km radius of any station -> will be treated as static_missing

        g_lat = round(float(flat_lats[idx]), 4)
        g_lon = round(float(flat_lons[idx]), 4)
        g_pt = grid_coords_km[idx]

        # IDW interpolation
        dists = np.linalg.norm(station_coords_km[neighbors] - g_pt, axis=1)
        # Avoid division by zero
        dists = np.maximum(dists, 0.05)
        weights = 1.0 / (dists ** 2)
        total_w = np.sum(weights)

        freq_val = float(np.sum(weights * station_freqs[neighbors]) / total_w)
        zone_val = float(np.sum(weights * station_zones[neighbors]) / total_w)

        valid_records.append({
            "grid_lat": g_lat,
            "grid_lon": g_lon,
            "historical_flood_frequency": round(freq_val, 2),
            "flood_zone": round(zone_val, 1),
        })

    out_df = pd.DataFrame(valid_records)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(output_parquet, index=False)
    print(f"Saved {len(out_df)} interpolated grid cells to '{output_parquet}'.")


if __name__ == "__main__":
    src = Path("features.csv")
    if not src.exists():
        src = Path("data/raw/flood.csv")
    build_static_lookup(src)
