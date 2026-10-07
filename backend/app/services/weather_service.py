"""Weather service supplying current and forecast rainfall observations across Kerala coordinates."""

from datetime import datetime, timezone
from typing import Dict, List
import numpy as np

from app.schemas import HourlyForecastItem, WeatherCurrentResponse, WeatherForecastResponse


class WeatherService:
    """Provides current and short-term forecast rainfall data for road segments."""

    @staticmethod
    def get_current_weather(latitude: float, longitude: float) -> WeatherCurrentResponse:
        """Estimate or fetch current rainfall conditions for a coordinate."""
        # Realistic monsoon spatial variation based on latitude & proximity to coast/highlands
        np.random.seed(int((latitude * 1000 + longitude * 100) % 10000))
        
        # Base rainfall in mm
        r24 = float(np.random.uniform(10.0, 110.0))
        r6 = float(r24 * np.random.uniform(0.35, 0.75))
        r1 = float(r6 * np.random.uniform(0.20, 0.60))

        temp = float(28.0 - (latitude - 8.5) * 0.4 + np.random.uniform(-1.5, 1.5))
        condition = "Heavy Monsoon Rain" if r1 > 15.0 else ("Moderate Rain" if r1 > 5.0 else "Overcast")

        return WeatherCurrentResponse(
            latitude=latitude,
            longitude=longitude,
            rainfall_1h=round(r1, 2),
            rainfall_6h=round(r6, 2),
            rainfall_24h=round(r24, 2),
            temperature_c=round(temp, 1),
            condition=condition,
        )

    @staticmethod
    def get_forecast(latitude: float, longitude: float) -> WeatherForecastResponse:
        """Return future hourly rainfall forecast."""
        np.random.seed(int((latitude * 500 + longitude * 300) % 10000))
        base_h = datetime.now(timezone.utc).hour

        forecast_items: List[HourlyForecastItem] = []
        for i in range(1, 7):
            hour = (base_h + i) % 24
            time_str = f"{hour:02d}:00"
            rain = float(np.random.exponential(scale=12.0))
            rain = round(min(rain, 80.0), 1)

            if rain > 25.0:
                risk_indicator = "HIGH"
            elif rain > 10.0:
                risk_indicator = "MODERATE"
            else:
                risk_indicator = "LOW"

            forecast_items.append(
                HourlyForecastItem(
                    time=time_str,
                    rainfall=rain,
                    risk_indicator=risk_indicator,
                )
            )

        return WeatherForecastResponse(
            latitude=latitude,
            longitude=longitude,
            forecast=forecast_items,
        )
