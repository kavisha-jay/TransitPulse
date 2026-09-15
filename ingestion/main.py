"""Main orchestration script for TransitPulse Phase 3 Data Ingestion Pipeline."""

from datetime import datetime, timezone
import logging
import os
import sys
from typing import Dict, Any

from ingestion.transit.api_client import TransitAPIClient
from ingestion.weather.api_client import WeatherAPIClient
from ingestion.common.validators import DataValidator
from ingestion.common.storage import StorageManager

logger = logging.getLogger("TransitPulse.Ingestion.Main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


class IngestionOrchestrator:
    """Orchestrates end-to-end ingestion for transit telemetry and weather feeds."""

    def __init__(self):
        self.transit_client = TransitAPIClient()
        self.weather_client = WeatherAPIClient()
        self.storage = StorageManager()

    def run_transit_vehicle_positions_pipeline(self) -> Dict[str, Any]:
        """Fetch, validate, landing vehicle positions."""
        dataset_name = "vehicle_positions"
        logger.info(f"--- Starting Ingestion: {dataset_name} ---")

        # 1. Fetch
        raw_df = self.transit_client.fetch_vehicle_positions()

        # 2. Validate
        req_cols = ["vehicle_id", "latitude", "longitude"]
        crit_cols = ["vehicle_id", "latitude", "longitude"]
        key_cols = ["vehicle_id", "updated_at"]
        fill_map = {"speed": 0.0, "bearing": 0.0, "current_status": "UNKNOWN"}

        clean_df, metrics = DataValidator.process_and_validate(
            df=raw_df,
            dataset_name=dataset_name,
            required_columns=req_cols,
            critical_columns=crit_cols,
            key_columns=key_cols,
            default_fill_map=fill_map,
            source_name="MBTA_V3_API"
        )

        # 3. Store Parquet & Manifest
        local_path, s3_uri = self.storage.save_parquet(
            df=clean_df,
            category="transit",
            dataset_name=dataset_name
        )

        manifest_path = self.storage.create_manifest(
            category="transit",
            dataset_name=dataset_name,
            metrics=metrics,
            local_file_path=local_path,
            s3_uri=s3_uri
        )

        metrics["local_path"] = local_path
        metrics["s3_uri"] = s3_uri
        metrics["manifest_path"] = manifest_path
        return metrics

    def run_transit_trip_updates_pipeline(self) -> Dict[str, Any]:
        """Fetch, validate, landing trip updates predictions."""
        dataset_name = "trip_updates"
        logger.info(f"--- Starting Ingestion: {dataset_name} ---")

        # 1. Fetch
        raw_df = self.transit_client.fetch_trip_updates()

        # 2. Validate
        req_cols = ["update_id", "trip_id"]
        crit_cols = ["update_id", "trip_id"]
        key_cols = ["update_id"]
        fill_map = {"arrival_delay_seconds": 0, "departure_delay_seconds": 0, "schedule_relationship": "SCHEDULED"}

        clean_df, metrics = DataValidator.process_and_validate(
            df=raw_df,
            dataset_name=dataset_name,
            required_columns=req_cols,
            critical_columns=crit_cols,
            key_columns=key_cols,
            default_fill_map=fill_map,
            source_name="MBTA_V3_API"
        )

        # 3. Store Parquet & Manifest
        local_path, s3_uri = self.storage.save_parquet(
            df=clean_df,
            category="transit",
            dataset_name=dataset_name
        )

        manifest_path = self.storage.create_manifest(
            category="transit",
            dataset_name=dataset_name,
            metrics=metrics,
            local_file_path=local_path,
            s3_uri=s3_uri
        )

        metrics["local_path"] = local_path
        metrics["s3_uri"] = s3_uri
        metrics["manifest_path"] = manifest_path
        return metrics

    def run_weather_pipeline(self) -> Dict[str, Any]:
        """Fetch, validate, landing weather observations."""
        dataset_name = "weather_observations"
        logger.info(f"--- Starting Ingestion: {dataset_name} ---")

        # 1. Fetch
        raw_df = self.weather_client.fetch_hourly_weather()

        # 2. Validate
        req_cols = ["lat_grid", "lon_grid", "timestamp_hour_utc"]
        crit_cols = ["lat_grid", "lon_grid", "timestamp_hour_utc"]
        key_cols = ["lat_grid", "lon_grid", "timestamp_hour_utc"]
        fill_map = {"precipitation_mm": 0.0, "snowfall_cm": 0.0, "wind_speed_kmh": 0.0}

        clean_df, metrics = DataValidator.process_and_validate(
            df=raw_df,
            dataset_name=dataset_name,
            required_columns=req_cols,
            critical_columns=crit_cols,
            key_columns=key_cols,
            default_fill_map=fill_map,
            source_name="Open_Meteo_API"
        )

        # 3. Store Parquet & Manifest
        local_path, s3_uri = self.storage.save_parquet(
            df=clean_df,
            category="weather",
            dataset_name=dataset_name
        )

        manifest_path = self.storage.create_manifest(
            category="weather",
            dataset_name=dataset_name,
            metrics=metrics,
            local_file_path=local_path,
            s3_uri=s3_uri
        )

        metrics["local_path"] = local_path
        metrics["s3_uri"] = s3_uri
        metrics["manifest_path"] = manifest_path
        return metrics

    def run_all(self) -> Dict[str, Any]:
        """Execute all ingestion pipelines and compile summary report."""
        logger.info("==========================================")
        logger.info("Starting TransitPulse Data Ingestion Suite")
        logger.info("==========================================")

        summary = {
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "pipelines": {}
        }

        try:
            summary["pipelines"]["vehicle_positions"] = self.run_transit_vehicle_positions_pipeline()
        except Exception as e:
            logger.error(f"Vehicle positions pipeline failed: {e}")
            summary["pipelines"]["vehicle_positions"] = {"status": "FAILED", "error": str(e)}

        try:
            summary["pipelines"]["trip_updates"] = self.run_transit_trip_updates_pipeline()
        except Exception as e:
            logger.error(f"Trip updates pipeline failed: {e}")
            summary["pipelines"]["trip_updates"] = {"status": "FAILED", "error": str(e)}

        try:
            summary["pipelines"]["weather_observations"] = self.run_weather_pipeline()
        except Exception as e:
            logger.error(f"Weather pipeline failed: {e}")
            summary["pipelines"]["weather_observations"] = {"status": "FAILED", "error": str(e)}

        logger.info("==========================================")
        logger.info("Ingestion Suite Execution Finished")
        logger.info("==========================================")
        return summary


if __name__ == "__main__":
    orchestrator = IngestionOrchestrator()
    results = orchestrator.run_all()
    print(results)
