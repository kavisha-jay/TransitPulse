"""Transit Data Ingestion API Client for MBTA GTFS / GTFS-Realtime Feeds."""

from datetime import datetime, timezone
import logging
import os
from typing import Dict, Any, Optional, List
import pandas as pd
import requests

logger = logging.getLogger("TransitPulse.Ingestion.TransitClient")


class TransitAPIClient:
    """API client for fetching MBTA vehicle positions and trip updates telemetry."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 15
    ):
        self.base_url = base_url or os.getenv("TRANSIT_API_BASE_URL", "https://api-v3.mbta.com")
        self.api_key = api_key or os.getenv("TRANSIT_API_KEY", "")
        self.timeout = timeout

        self.headers = {"Accept": "application/vnd.api+json"}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def fetch_vehicle_positions(self) -> pd.DataFrame:
        """
        Fetch real-time vehicle positions from MBTA API.
        Returns normalized pandas DataFrame.
        """
        endpoint = f"{self.base_url}/vehicles"
        logger.info(f"Fetching vehicle positions from: {endpoint}")

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()

            data_items = payload.get("data", [])
            if not isinstance(data_items, list):
                data_items = []

            records = []

            for item in data_items:
                if not isinstance(item, dict):
                    continue

                attr = item.get("attributes") or {}
                rel = item.get("relationships") or {}

                vehicle_id = item.get("id")

                trip_rel = rel.get("trip") or {}
                trip_data = trip_rel.get("data") or {}
                trip_id = trip_data.get("id") if isinstance(trip_data, dict) else None

                route_rel = rel.get("route") or {}
                route_data = route_rel.get("data") or {}
                route_id = route_data.get("id") if isinstance(route_data, dict) else None

                stop_rel = rel.get("stop") or {}
                stop_data = stop_rel.get("data") or {}
                stop_id = stop_data.get("id") if isinstance(stop_data, dict) else None

                lat = attr.get("latitude")
                lon = attr.get("longitude")

                records.append({
                    "vehicle_id": vehicle_id,
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "latitude": lat,
                    "longitude": lon,
                    "bearing": attr.get("bearing"),
                    "speed": attr.get("speed"),
                    "current_status": attr.get("current_status"),
                    "current_stop_sequence": attr.get("current_stop_sequence"),
                    "updated_at": attr.get("updated_at") or datetime.now(timezone.utc).isoformat(),
                    "lat_grid": round(lat, 2) if lat is not None else None,
                    "lon_grid": round(lon, 2) if lon is not None else None
                })

            df = pd.DataFrame(records)
            logger.info(f"Successfully fetched {len(df)} vehicle position records.")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch vehicle positions: {e}")
            raise

    def fetch_trip_updates(self) -> pd.DataFrame:
        """
        Fetch real-time predictions / trip updates from MBTA feed or enhanced GTFS-RT JSON.
        Returns normalized pandas DataFrame.
        """
        cdn_endpoint = "https://cdn.mbta.com/realtime/TripUpdates_enhanced.json"
        v3_endpoint = f"{self.base_url}/predictions"

        logger.info(f"Fetching trip updates from: {cdn_endpoint}")

        try:
            response = requests.get(cdn_endpoint, timeout=self.timeout)
            if response.status_code == 200:
                payload = response.json()
                entities = payload.get("entity", [])
                records = []

                for ent in entities:
                    if not isinstance(ent, dict):
                        continue

                    tu = ent.get("trip_update") or {}
                    trip = tu.get("trip") or {}
                    vehicle = tu.get("vehicle") or {}

                    trip_id = trip.get("trip_id")
                    route_id = trip.get("route_id")
                    vehicle_id = vehicle.get("id")

                    stop_time_updates = tu.get("stop_time_update") or []
                    for stu in stop_time_updates:
                        if not isinstance(stu, dict):
                            continue
                        stop_id = stu.get("stop_id")
                        stop_seq = stu.get("stop_sequence")
                        arr = stu.get("arrival") or {}
                        dep = stu.get("departure") or {}

                        arr_delay = arr.get("delay", 0) if isinstance(arr, dict) else 0
                        arr_time = datetime.fromtimestamp(arr.get("time", 0), timezone.utc).isoformat() if isinstance(arr, dict) and arr.get("time") else None

                        dep_delay = dep.get("delay", 0) if isinstance(dep, dict) else 0
                        dep_time = datetime.fromtimestamp(dep.get("time", 0), timezone.utc).isoformat() if isinstance(dep, dict) and dep.get("time") else None

                        update_id = f"{trip_id}_{stop_id}_{stop_seq}"

                        records.append({
                            "update_id": update_id,
                            "trip_id": trip_id,
                            "route_id": route_id,
                            "stop_id": stop_id,
                            "vehicle_id": vehicle_id,
                            "stop_sequence": stop_seq,
                            "arrival_time_utc": arr_time,
                            "departure_time_utc": dep_time,
                            "arrival_delay_seconds": arr_delay,
                            "departure_delay_seconds": dep_delay,
                            "schedule_relationship": trip.get("schedule_relationship", "SCHEDULED")
                        })

                df = pd.DataFrame(records)
                logger.info(f"Successfully fetched {len(df)} trip update records from CDN.")
                return df
            else:
                response = requests.get(v3_endpoint, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                data_items = payload.get("data") or []
                records = []

                for item in data_items:
                    if not isinstance(item, dict):
                        continue
                    attr = item.get("attributes") or {}
                    rel = item.get("relationships") or {}

                    trip_rel = rel.get("trip") or {}
                    trip_data = trip_rel.get("data") or {}

                    route_rel = rel.get("route") or {}
                    route_data = route_rel.get("data") or {}

                    stop_rel = rel.get("stop") or {}
                    stop_data = stop_rel.get("data") or {}

                    vehicle_rel = rel.get("vehicle") or {}
                    vehicle_data = vehicle_rel.get("data") or {}

                    records.append({
                        "update_id": item.get("id"),
                        "trip_id": trip_data.get("id") if isinstance(trip_data, dict) else None,
                        "route_id": route_data.get("id") if isinstance(route_data, dict) else None,
                        "stop_id": stop_data.get("id") if isinstance(stop_data, dict) else None,
                        "vehicle_id": vehicle_data.get("id") if isinstance(vehicle_data, dict) else None,
                        "stop_sequence": attr.get("stop_sequence"),
                        "arrival_time_utc": attr.get("arrival_time"),
                        "departure_time_utc": attr.get("departure_time"),
                        "arrival_delay_seconds": attr.get("delay") or 0,
                        "departure_delay_seconds": attr.get("delay") or 0,
                        "schedule_relationship": attr.get("schedule_relationship", "SCHEDULED")
                    })

                df = pd.DataFrame(records)
                logger.info(f"Successfully fetched {len(df)} trip update records from V3 API.")
                return df

        except Exception as e:
            logger.error(f"Failed to fetch trip updates: {e}")
            raise
