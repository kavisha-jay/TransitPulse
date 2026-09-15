"""Unit tests for Transit and Weather API clients using mock HTTP responses."""

from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
from ingestion.transit.api_client import TransitAPIClient
from ingestion.weather.api_client import WeatherAPIClient


@pytest.mark.unit
@patch("ingestion.transit.api_client.requests.get")
def test_fetch_vehicle_positions_mock(mock_get):
    """Verify transit vehicle positions fetching and parsing with mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "v100",
                "attributes": {
                    "latitude": 42.3601,
                    "longitude": -71.0589,
                    "bearing": 180.0,
                    "speed": 12.5,
                    "current_status": "IN_TRANSIT_TO",
                    "current_stop_sequence": 5,
                    "updated_at": "2026-09-15T10:00:00Z"
                },
                "relationships": {
                    "trip": {"data": {"id": "trip_99"}},
                    "route": {"data": {"id": "Red"}}
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    client = TransitAPIClient(base_url="https://mock-api.example.com", api_key="test_key")
    df = client.fetch_vehicle_positions()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df["vehicle_id"].iloc[0] == "v100"
    assert df["trip_id"].iloc[0] == "trip_99"
    assert df["route_id"].iloc[0] == "Red"
    assert df["lat_grid"].iloc[0] == 42.36
    assert df["lon_grid"].iloc[0] == -71.06


@pytest.mark.unit
@patch("ingestion.weather.api_client.requests.get")
def test_fetch_hourly_weather_mock(mock_get):
    """Verify weather fetching and parsing with mock response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "hourly": {
            "time": ["2026-09-15T00:00", "2026-09-15T01:00"],
            "temperature_2m": [18.5, 17.2],
            "relative_humidity_2m": [65, 70],
            "precipitation": [0.0, 1.2],
            "rain": [0.0, 1.2],
            "snowfall": [0.0, 0.0],
            "weather_code": [0, 61],
            "wind_speed_10m": [12.0, 15.5],
            "visibility": [10000, 8000]
        }
    }
    mock_get.return_value = mock_response

    client = WeatherAPIClient()
    df = client.fetch_hourly_weather(latitude=42.3601, longitude=-71.0589, forecast_days=1)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df["lat_grid"].iloc[0] == 42.36
    assert df["lon_grid"].iloc[0] == -71.06
    assert df["temperature_celsius"].iloc[0] == 18.5
    assert df["precipitation_mm"].iloc[1] == 1.2
