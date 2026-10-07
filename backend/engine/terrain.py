"""Terrain elevation service with disk caching."""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request
import pandas as pd

from engine.config import ELEVATION_CACHE_FILE


class TerrainService:
    """Provides elevation lookups for geographic coordinates with persistent disk caching."""

    def __init__(self, cache_file: Path = ELEVATION_CACHE_FILE):
        self.cache_file = cache_file
        self._cache: Dict[Tuple[float, float], float] = {}
        self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                df = pd.read_csv(self.cache_file)
                lat_col = "latitude" if "latitude" in df.columns else "Latitude"
                lon_col = "longitude" if "longitude" in df.columns else "Longitude"
                elev_col = "elevation" if "elevation" in df.columns else "Elevation"
                for _, row in df.iterrows():
                    key = (round(float(row[lat_col]), 4), round(float(row[lon_col]), 4))
                    self._cache[key] = float(row[elev_col])
            except Exception as e:
                print(f"Warning: Failed to load elevation cache from {self.cache_file}: {e}")

    def _save_cache(self):
        try:
            records = [{"latitude": k[0], "longitude": k[1], "elevation": v} for k, v in self._cache.items()]
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(records).to_csv(self.cache_file, index=False)
        except Exception as e:
            print(f"Warning: Failed to save elevation cache: {e}")

    def get_elevation_batch(self, points: List[Tuple[float, float]]) -> List[float]:
        """Fetch elevation in meters for a batch of coordinates, querying Open-Meteo for uncached points."""
        results: List[float] = []
        missing_indices: List[int] = []
        missing_coords: List[Tuple[float, float]] = []

        for idx, (lat, lon) in enumerate(points):
            key = (round(lat, 4), round(lon, 4))
            if key in self._cache:
                results.append(self._cache[key])
            else:
                results.append(0.0)  # placeholder
                missing_indices.append(idx)
                missing_coords.append((lat, lon))

        if missing_coords:
            # Query Open-Meteo in batches of 100
            for b_start in range(0, len(missing_coords), 100):
                batch = missing_coords[b_start : b_start + 100]
                indices = missing_indices[b_start : b_start + 100]
                lats_str = ",".join(f"{p[0]:.4f}" for p in batch)
                lons_str = ",".join(f"{p[1]:.4f}" for p in batch)
                url = f"https://api.open-meteo.com/v1/elevation?latitude={lats_str}&longitude={lons_str}"

                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "FLOODRIX/1.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        data = json.load(r)
                        elevations = data.get("elevation", [])
                        for target_idx, coord, elev in zip(indices, batch, elevations):
                            e_val = float(elev if elev is not None else 10.0)
                            key = (round(coord[0], 4), round(coord[1], 4))
                            self._cache[key] = e_val
                            results[target_idx] = e_val
                except Exception as e:
                    # Fallback on network failure
                    for target_idx, coord in zip(indices, batch):
                        # Approximate based on distance from coast (Kerala Western Ghats gradient)
                        approx = max(2.0, (coord[1] - 75.8) * 110.0)
                        key = (round(coord[0], 4), round(coord[1], 4))
                        self._cache[key] = approx
                        results[target_idx] = approx

            self._save_cache()

        return results

    get_elevations_batch = get_elevation_batch


terrain_service = TerrainService()
