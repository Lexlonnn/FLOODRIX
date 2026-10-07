"""Time-aware rainfall aggregation: calculates 1h, 6h, 24h cumulative rainfall ending at arrival hour."""

from datetime import datetime
from typing import Dict, Tuple

from engine.config import RAIN_SAFETY_FACTOR


def calculate_time_aware_rainfall(
    hourly_precip: Dict[int, float],
    arrival_dt: datetime,
    safety_factor: float = RAIN_SAFETY_FACTOR,
) -> Tuple[float, float, float]:
    """Calculate cumulative rainfall ending at arrival_dt hour and enforce physical monotonicity.

    Returns:
    (rainfall_1h, rainfall_6h, rainfall_24h) in mm, satisfying 0 <= 1h <= 6h <= 24h.
    """
    arrival_epoch_hour = int(arrival_dt.timestamp()) // 3600

    # 1. 1-hour rainfall ending at arrival hour
    r1 = float(hourly_precip.get(arrival_epoch_hour, 0.0)) * safety_factor

    # 2. 6-hour cumulative rainfall window [arrival - 5, arrival]
    r6 = sum(float(hourly_precip.get(h, 0.0)) for h in range(arrival_epoch_hour - 5, arrival_epoch_hour + 1)) * safety_factor

    # 3. 24-hour cumulative rainfall window [arrival - 23, arrival]
    r24 = sum(float(hourly_precip.get(h, 0.0)) for h in range(arrival_epoch_hour - 23, arrival_epoch_hour + 1)) * safety_factor

    # Ensure non-negativity
    r1 = max(0.0, r1)
    r6 = max(0.0, r6)
    r24 = max(0.0, r24)

    # Strictly enforce physical monotonicity: 1h <= 6h <= 24h
    r6 = max(r6, r1)
    r24 = max(r24, r6)

    return round(r1, 2), round(r6, 2), round(r24, 2)
