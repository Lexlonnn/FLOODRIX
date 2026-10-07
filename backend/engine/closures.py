"""Road closure registry and spatial proximity query service."""

from datetime import datetime, timezone
import threading
from typing import List, Optional
import uuid

from engine.config import CLOSURE_SNAP_M
from engine.geometry import haversine_distance_m
from engine.models import ClosureCreateRequest, ClosureItem


class ClosureStore:
    """Thread-safe store for active road closures."""

    def __init__(self):
        self._lock = threading.Lock()
        self._closures: dict[str, ClosureItem] = {}

    def add_closure(self, req: ClosureCreateRequest) -> ClosureItem:
        closure_id = f"CL-{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()
        item = ClosureItem(
            id=closure_id,
            lat=req.lat,
            lon=req.lon,
            radius_m=req.radius_m,
            reason=req.reason,
            created_at=now_str,
            expires_at=req.expires_at,
            is_active=True,
        )
        with self._lock:
            self._closures[closure_id] = item
        return item

    def delete_closure(self, closure_id: str) -> bool:
        with self._lock:
            if closure_id in self._closures:
                del self._closures[closure_id]
                return True
        return False

    def get_active_closures(
        self,
        bbox: Optional[tuple[float, float, float, float]] = None,
    ) -> List[ClosureItem]:
        """Return active closures, optionally filtered by (min_lat, min_lon, max_lat, max_lon)."""
        now = datetime.now(timezone.utc)
        active: List[ClosureItem] = []

        with self._lock:
            for item in self._closures.values():
                if not item.is_active:
                    continue
                if item.expires_at:
                    try:
                        exp = datetime.fromisoformat(item.expires_at.replace("Z", "+00:00"))
                        if exp < now:
                            continue
                    except Exception:
                        pass

                if bbox:
                    min_lat, min_lon, max_lat, max_lon = bbox
                    if not (min_lat <= item.lat <= max_lat and min_lon <= item.lon <= max_lon):
                        continue

                active.append(item)

        return active

    def is_point_closed(
        self,
        lat: float,
        lon: float,
        snap_distance_m: float = CLOSURE_SNAP_M,
    ) -> tuple[bool, Optional[ClosureItem]]:
        """Check if (lat, lon) is within the closure radius + snap distance of any active closure."""
        closures = self.get_active_closures()
        for c in closures:
            dist = haversine_distance_m(lat, lon, c.lat, c.lon)
            if dist <= (c.radius_m + snap_distance_m):
                return True, c
        return False, None


# Global closure store instance
closure_store = ClosureStore()
