"""Static hazard lookup providing historical_flood_frequency and flood_zone with static_missing flagging."""

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from engine.config import STATIC_LOOKUP_FILE

KM_PER_LAT = 110.8
KM_PER_LON = 109.4


class StaticLookupService:
    """Queries precomputed 0.01 degree grid for historical flood frequency and flood zone."""

    def __init__(self, lookup_path: Path = STATIC_LOOKUP_FILE, max_distance_km: float = 5.0):
        self.lookup_path = lookup_path
        self.max_dist_km = max_distance_km
        self.tree: Optional[KDTree] = None
        self.freqs: np.ndarray = np.array([])
        self.zones: np.ndarray = np.array([])
        self._load()

    def _load(self):
        if not self.lookup_path.exists():
            print(f"Notice: Static lookup file not found at '{self.lookup_path}'. All queries will be flagged static_missing.")
            return

        try:
            df = pd.read_parquet(self.lookup_path)
            if df.empty:
                return

            coords_km = np.column_stack([
                df["grid_lat"].values * KM_PER_LAT,
                df["grid_lon"].values * KM_PER_LON,
            ])
            self.tree = KDTree(coords_km)
            self.freqs = df["historical_flood_frequency"].values
            self.zones = df["flood_zone"].values
        except Exception as e:
            print(f"Warning: Failed to load static lookup from {self.lookup_path}: {e}")

    def lookup(self, lat: float, lon: float) -> Tuple[float, float, bool]:
        """Look up historical flood metrics for coordinate.

        Returns:
        (historical_flood_frequency, flood_zone, static_missing)
        """
        if self.tree is None:
            return 0.0, 0.0, True

        query_km = np.array([[lat * KM_PER_LAT, lon * KM_PER_LON]])
        dist, idx = self.tree.query(query_km, k=1)
        dist_km = float(dist[0])

        if dist_km <= self.max_dist_km:
            idx_match = int(idx[0])
            freq = float(self.freqs[idx_match])
            zone = float(self.zones[idx_match])
            return freq, zone, False

        # No static station within 5 km: default low zone/freq 0 with static_missing=True
        return 0.0, 0.0, True


static_lookup_service = StaticLookupService()


def query_static_lookup(lat: float, lon: float) -> Tuple[float, float, bool]:
    """Helper function to query the global static lookup service."""
    return static_lookup_service.lookup(lat, lon)

