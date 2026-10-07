"""Unit tests for terrain elevation and static hazard lookup."""

from pathlib import Path
import pytest

from engine.static_lookup import StaticLookupService
from engine.terrain import TerrainService


def test_terrain_service():
    service = TerrainService()
    # Kochi coordinates (already cached in elevation_cache.csv)
    points = [(9.092378, 77.122000), (10.013611, 76.957778)]
    elevs = service.get_elevation_batch(points)
    assert len(elevs) == 2
    assert elevs[0] == 73.0
    assert elevs[1] == 572.0


def test_static_lookup_service():
    service = StaticLookupService()
    # Point near Kochi station
    freq, zone, missing = service.lookup(10.0136, 76.9577)
    assert missing is False
    assert freq >= 0.0
    assert zone in [0.0, 1.0, 2.0]

    # Point far out in the Arabian Sea (should be static_missing)
    freq_sea, zone_sea, missing_sea = service.lookup(9.5, 73.5)
    assert missing_sea is True
    assert freq_sea == 0.0
    assert zone_sea == 0.0
