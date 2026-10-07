"""Road closure and traffic disruption registry."""

from typing import List, Optional
import numpy as np
from app.schemas import RoadClosure

# Known recurrent monsoon disruption hotspots in Kerala
INITIAL_CLOSURES = [
    RoadClosure(
        id="CL001",
        latitude=9.985,
        longitude=76.289,
        road_name="NH 66 Edappally Bypass Underpass",
        district="Ernakulam",
        reason="Severe waterlogging, water depth > 45cm",
        is_active=True,
    ),
    RoadClosure(
        id="CL002",
        latitude=9.442,
        longitude=76.438,
        road_name="Alappuzha-Changanassery (AC) Road Km 12",
        district="Alappuzha",
        reason="Pampa river overflow, road submerged",
        is_active=True,
    ),
    RoadClosure(
        id="CL003",
        latitude=10.518,
        longitude=76.195,
        road_name="Thrissur Kole Wetland Crossing",
        district="Thrissur",
        reason="Agricultural bund breach",
        is_active=True,
    ),
    RoadClosure(
        id="CL004",
        latitude=11.512,
        longitude=76.012,
        road_name="Thamarassery Churam 7th Hairpin",
        district="Wayanad",
        reason="Precautionary closure due to mudslide risk",
        is_active=True,
    ),
]


class ClosureService:
    """Manages active road closures and spatial proximity checks."""

    def __init__(self):
        self._closures = list(INITIAL_CLOSURES)

    def get_active_closures(self) -> List[RoadClosure]:
        return [c for c in self._closures if c.is_active]

    def add_closure(self, closure: RoadClosure) -> None:
        self._closures.append(closure)

    def is_near_closure(self, lat: float, lon: float, threshold_km: float = 1.0) -> Optional[RoadClosure]:
        """Check if a coordinate is within threshold distance of an active road closure."""
        # Approx distance: 1 deg lat ~= 111 km, 1 deg lon ~= 108 km in Kerala
        for c in self.get_active_closures():
            d_lat = (lat - c.latitude) * 111.0
            d_lon = (lon - c.longitude) * 108.0
            dist_km = float(np.sqrt(d_lat**2 + d_lon**2))
            if dist_km <= threshold_km:
                return c
        return None
