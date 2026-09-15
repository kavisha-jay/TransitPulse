"""Open-Meteo Weather Data Ingestion API Client for TransitPulse."""

from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import requests

logger = logging.getLogger("TransitPulse.Ingestion.WeatherClient")


class WeatherAPIClient:
    """API client for fetching hourly forecast and historical weather observations from Open-Meteo."""

    DEFAULT_LAT = 42.3601  # Boston, MA latitude
    DEFAULT_LON = -71.0589  # Boston, MA longitude
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def fetch_hourly_weather(
        self,
        latitude: float = DEFAULT_LAT,
        longitude: float = DEFAULT_LON,
        forecast_days: int = 1
    ) -> pd.DataFrame:
        """
        Fetch hourly weather variables for given geographic coordinates.
        Returns normalized pandas DataFrame.
        """
        logger.info(f"Fetching weather data for Lat={latitude}, Lon={longitude}")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,wind_speed_10m,visibility",
            "forecast_days": forecast_days,
            "timezone": "UTC"
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()

            hourly_data = payload.get("hourly", {})
            times = hourly_data.get("time", [])

            records = []
            lat_grid = round(latitude, 2)
            lon_grid = round(longitude, 2)

            for i, ts in enumerate(times):
                records.append({
                    "lat_grid": lat_grid,
                    "lon_grid": lon_grid,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp_hour_utc": ts,
                    "temperature_celsius": hourly_data.get("temperature_2m", [])[i],
                    "relative_humidity_pct": hourly_data.get("relative_humidity_2m", [])[i],
                    "precipitation_mm": hourly_data.get("precipitation", [])[i],
                    "rain_mm": hourly_data.get("rain", [])[i],
                    "snowfall_cm": hourly_data.get("snowfall", [])[i],
                    "weather_code": hourly_data.get("weather_code", [])[i],
                    "wind_speed_kmh": hourly_data.get("wind_speed_10m", [])[i],
                    "visibility_meters": hourly_data.get("visibility", [])[i],
                })

            df = pd.DataFrame(records)
            logger.info(f"Successfully fetched {len(df)} hourly weather records.")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            raise
