"""Integration test for end-to-end fetch -> validate -> storage ingestion pipeline."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from ingestion.transit.api_client import TransitAPIClient
from ingestion.weather.api_client import WeatherAPIClient
from ingestion.common.validators import DataValidator
from ingestion.common.storage import StorageManager


@pytest.mark.integration
@patch("ingestion.transit.api_client.requests.get")
def test_full_transit_ingestion_flow(mock_get, tmp_path):
    """Test full transit vehicle positions ingestion, validation, and storage flow."""
    # 1. Mock API Response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "v101",
                "attributes": {
                    "latitude": 42.3601,
                    "longitude": -71.0589,
                    "speed": 15.0,
                    "current_status": "IN_TRANSIT_TO",
                    "updated_at": "2026-09-15T12:00:00Z"
                },
                "relationships": {
                    "trip": {"data": {"id": "trip_01"}},
                    "route": {"data": {"id": "Orange"}}
                }
            },
            # Invalid record missing vehicle_id
            {
                "id": None,
                "attributes": {
                    "latitude": 42.3601,
                    "longitude": -71.0589
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    # 2. Initialize Components with temporary landing directory
    client = TransitAPIClient(base_url="https://mock-api.example.com")
    storage = StorageManager(local_base_dir=str(tmp_path))

    raw_df = client.fetch_vehicle_positions()
    assert len(raw_df) == 2

    # 3. Validate
    clean_df, metrics = DataValidator.process_and_validate(
        df=raw_df,
        dataset_name="vehicle_positions",
        required_columns=["vehicle_id", "latitude", "longitude"],
        critical_columns=["vehicle_id"],
        key_columns=["vehicle_id", "updated_at"],
        source_name="MOCK_TEST"
    )

    assert len(clean_df) == 1
    assert metrics["dropped_nulls"] == 1

    # 4. Storage & Manifest Creation
    local_path, s3_uri = storage.save_parquet(
        df=clean_df,
        category="transit",
        dataset_name="vehicle_positions"
    )

    manifest_path = storage.create_manifest(
        category="transit",
        dataset_name="vehicle_positions",
        metrics=metrics,
        local_file_path=local_path,
        s3_uri=s3_uri
    )

    assert Path(local_path).exists()
    assert Path(manifest_path).exists()

    # Read back saved Parquet to verify integrity
    read_df = pd.read_parquet(local_path)
    assert len(read_df) == 1
    assert read_df["vehicle_id"].iloc[0] == "v101"
    assert "_ingested_at" in read_df.columns
