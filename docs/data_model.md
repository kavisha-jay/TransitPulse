# TransitPulse Data Model Specification

> **Data Lakehouse Schemas & Contract Documentation**: Bronze Landing, Silver Cleansed, and Gold Star Schema Marts.

---

## 1. Overview & Data Conventions

- **Timezone Standard**: All timestamps across Bronze, Silver, and Gold layers are normalized to **UTC ISO-8601** format (`YYYY-MM-DDTHH:MM:SSZ` or epoch milliseconds).
- **Coordinate Standard**: All geographic points are stored in standard **WGS84** coordinates (`latitude` -90 to +90, `longitude` -180 to +180).
- **Spatial Grid Binning**: For spatiotemporal joining between transit telemetry and weather observations, coordinates are binned to 2 decimal places ($\approx 1.1\text{ km}$ grid resolution):
  ```python
  lat_grid = round(latitude, 2)
  lon_grid = round(longitude, 2)
  ```

---

## 2. Bronze Layer (Raw Ingestion Storage)

Raw landed data is saved as snappy-compressed Parquet files and raw JSON manifests.

### 2.1 Vehicle Positions (`bronze/transit/vehicle_positions/YYYY-MM-DD/`)
| Field Name | Type | Critical/Nullable | Description |
| :--- | :--- | :--- | :--- |
| `vehicle_id` | STRING | **Critical (Non-null)** | Unique identifier for the transit vehicle |
| `trip_id` | STRING | Nullable | Active trip identifier from static GTFS |
| `route_id` | STRING | Nullable | Route identifier (e.g., `Red`, `Orange`, `Bus_1`) |
| `stop_id` | STRING | Nullable | Current or next stop ID |
| `latitude` | DOUBLE | **Critical (Non-null)** | WGS84 vehicle latitude |
| `longitude` | DOUBLE | **Critical (Non-null)** | WGS84 vehicle longitude |
| `bearing` | DOUBLE | Nullable | Compass heading in degrees (0–360) |
| `speed` | DOUBLE | Nullable | Vehicle speed in meters per second |
| `current_status` | STRING | Nullable | Transit status: `IN_TRANSIT_TO`, `STOPPED_AT`, `INCOMING_AT` |
| `current_stop_sequence`| INT | Nullable | Sequence index of the stop on the trip |
| `updated_at` | STRING | **Critical (Non-null)** | Timestamp of vehicle update from feed |
| `lat_grid` | DOUBLE | **Critical (Non-null)** | Binned latitude (2 decimal places) |
| `lon_grid` | DOUBLE | **Critical (Non-null)** | Binned longitude (2 decimal places) |
| `_ingested_at` | STRING | Metadata | System ingestion UTC timestamp |
| `_source` | STRING | Metadata | Feed source identifier (`MBTA_V3_API`) |
| `_version` | STRING | Metadata | Schema version (`1.0`) |

### 2.2 Trip Updates (`bronze/transit/trip_updates/YYYY-MM-DD/`)
| Field Name | Type | Critical/Nullable | Description |
| :--- | :--- | :--- | :--- |
| `update_id` | STRING | **Critical (Non-null)** | Unique update hash/ID |
| `trip_id` | STRING | **Critical (Non-null)** | Associated GTFS trip ID |
| `route_id` | STRING | Nullable | Associated GTFS route ID |
| `stop_id` | STRING | Nullable | Target stop ID |
| `vehicle_id` | STRING | Nullable | Vehicle performing the trip |
| `stop_sequence` | INT | Nullable | Sequence position of the stop |
| `arrival_time_utc` | STRING | Nullable | Predicted arrival timestamp in UTC |
| `departure_time_utc`| STRING | Nullable | Predicted departure timestamp in UTC |
| `arrival_delay_seconds`| INT | Nullable | Delay relative to schedule in seconds |
| `departure_delay_seconds`| INT | Nullable | Departure delay in seconds |
| `schedule_relationship`| STRING | Nullable | `SCHEDULED`, `ADDED`, `UNSCHEDULED`, `CANCELED` |
| `_ingested_at` | STRING | Metadata | System ingestion UTC timestamp |

### 2.3 Weather Observations (`bronze/weather/weather_observations/YYYY-MM-DD/`)
| Field Name | Type | Critical/Nullable | Description |
| :--- | :--- | :--- | :--- |
| `lat_grid` | DOUBLE | **Critical (Non-null)** | Binned latitude cell key |
| `lon_grid` | DOUBLE | **Critical (Non-null)** | Binned longitude cell key |
| `latitude` | DOUBLE | Non-null | Exact weather query latitude |
| `longitude` | DOUBLE | Non-null | Exact weather query longitude |
| `timestamp_hour_utc` | STRING | **Critical (Non-null)** | Top of the hour timestamp (UTC) |
| `temperature_celsius`| DOUBLE | Nullable | Air temperature at 2 meters (°C) |
| `relative_humidity_pct`| DOUBLE | Nullable | Relative humidity percentage |
| `precipitation_mm` | DOUBLE | Nullable | Total precipitation in mm |
| `rain_mm` | DOUBLE | Nullable | Liquid rain in mm |
| `snowfall_cm` | DOUBLE | Nullable | Snowfall in cm |
| `weather_code` | INT | Nullable | WMO weather condition code |
| `wind_speed_kmh` | DOUBLE | Nullable | Wind speed at 10m in km/h |
| `visibility_meters` | DOUBLE | Nullable | Atmospheric visibility in meters |
| `_ingested_at` | STRING | Metadata | System ingestion UTC timestamp |

---

## 3. Data Quality & Validation Policies

1. **Required Columns Check**: Every incoming batch is verified against required column schemas. If any required column is missing, ingestion halts for that feed and logs a `SchemaValidationError`.
2. **Critical Null Dropping**: Rows missing primary identifiers (`vehicle_id`, `update_id`, `lat_grid`, `lon_grid`) are dropped and logged to `metrics["dropped_nulls"]`.
3. **Deduplication**: Records sharing identical primary key combinations are deduplicated, keeping the latest record.
4. **Execution Manifests**: Every run generates a JSON manifest recording `raw_row_count`, `clean_row_count`, `dropped_nulls`, `duplicates_removed`, `local_file_path`, and `s3_uri`.
