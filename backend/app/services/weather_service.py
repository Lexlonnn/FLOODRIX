"""Weather service supplying current and forecast rainfall observations across Kerala coordinates."""

from datetime import datetime, timezone
from typing import Dict, List
import requests

from app.schemas import HourlyForecastItem, WeatherCurrentResponse, WeatherForecastResponse

class WeatherService:
    """Provides current and short-term forecast rainfall data for road segments."""

    @staticmethod
    def get_current_weather(latitude: float, longitude: float) -> WeatherCurrentResponse:
        """Fetch current rainfall conditions from Open-Meteo."""
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,precipitation,weather_code&hourly=precipitation&past_days=1"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            temp = data.get("current", {}).get("temperature_2m", 28.0)
            r1 = data.get("current", {}).get("precipitation", 0.0)
            
            # calculate past 24h and 6h rainfall
            hourly_precip = data.get("hourly", {}).get("precipitation", [])
            r24 = sum(hourly_precip[-24:]) if len(hourly_precip) >= 24 else r1 * 24
            r6 = sum(hourly_precip[-6:]) if len(hourly_precip) >= 6 else r1 * 6

            condition = "Heavy Monsoon Rain" if r1 > 5.0 else ("Moderate Rain" if r1 > 1.0 else "Clear/Overcast")

            return WeatherCurrentResponse(
                latitude=latitude,
                longitude=longitude,
                rainfall_1h=round(float(r1), 2),
                rainfall_6h=round(float(r6), 2),
                rainfall_24h=round(float(r24), 2),
                temperature_c=round(float(temp), 1),
                condition=condition,
            )
        except Exception as e:
            # Fallback
            return WeatherCurrentResponse(
                latitude=latitude, longitude=longitude,
                rainfall_1h=0.0, rainfall_6h=0.0, rainfall_24h=0.0,
                temperature_c=28.0, condition="Unknown"
            )

    @staticmethod
    def get_forecast(latitude: float, longitude: float) -> WeatherForecastResponse:
        """Return future hourly rainfall forecast."""
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=precipitation&forecast_days=2"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            hourly_times = data.get("hourly", {}).get("time", [])
            hourly_precip = data.get("hourly", {}).get("precipitation", [])
            
            now_iso = datetime.now(timezone.utc).isoformat()
            
            forecast_items: List[HourlyForecastItem] = []
            
            # Find closest future time
            started = False
            count = 0
            for t, p in zip(hourly_times, hourly_precip):
                if t > now_iso or started:
                    started = True
                    dt = datetime.fromisoformat(t)
                    rain = float(p)
                    
                    if rain > 10.0:
                        risk = "HIGH"
                    elif rain > 2.0:
                        risk = "MODERATE"
                    else:
                        risk = "LOW"
                        
                    forecast_items.append(HourlyForecastItem(
                        time=f"{dt.hour:02d}:00",
                        rainfall=round(rain, 1),
                        risk_indicator=risk
                    ))
                    count += 1
                    if count >= 6:
                        break

            return WeatherForecastResponse(
                latitude=latitude,
                longitude=longitude,
                forecast=forecast_items,
            )
        except Exception:
            return WeatherForecastResponse(latitude=latitude, longitude=longitude, forecast=[])
