# TransitPulse - Architecture Specification

> **Phase 1 Revised Architecture**: Detailed Lakehouse Data Pipeline & Data Schemas

---

## 1. End-to-End System Architecture

```
                                  Data Sources
  +----------------------------------------------------------------------------------+
  |  MBTA GTFS Static ZIP   |  MBTA GTFS-RT Protobuf Feeds  |  Open-Meteo Weather    |
  |  (daily scheduled zip)  |  (15s Vehicle & Trip Updates) |  (Hourly REST API)     |
  +----------------------------------------------------------------------------------+
                                          |
                                          v (HTTP Ingestors / Resilience Wrappers)
+------------------------------------------------------------------------------------+
|                                BRONZE LANDING ZONE                                 |
|  data/raw_landing/static_gtfs/YYYY-MM-DD/                                         |
|  data/raw_landing/vehicle_positions/YYYY-MM-DD/HH/                                 |
|  data/raw_landing/trip_updates/YYYY-MM-DD/HH/                                      |
|  data/raw_landing/weather/YYYY-MM-DD/HH/                                           |
+------------------------------------------------------------------------------------+
                                          |
                                          v (PySpark Streaming & Batch Cleanse ETL)
+------------------------------------------------------------------------------------+
|                                SILVER DELTA LAKE                                   |
|  dim_routes, dim_stops, dim_trips (Static GTFS reference tables)                   |
|  silver_vehicle_positions (Deduplicated telemetry + lat/lon grid cells)            |
|  silver_trip_updates (Parsed arrival/departure delay seconds)                       |
|  silver_weather_observations (Hourly temperature, precip, wind, visibility)        |
+------------------------------------------------------------------------------------+
                                          |
                                          v (PySpark / dbt Star Schema Transformations)
+------------------------------------------------------------------------------------+
|                                 GOLD DATA MARTS                                    |
|  fact_trip_updates (Enriched delays + weather metrics + static trip lookups)       |
|  fact_daily_stop_performance (Aggregated OTP, average delay, dwell times)          |
|  fact_vehicle_speed (Speed distributions & congestion diagnostics)                 |
+------------------------------------------------------------------------------------+
                                          |
                                          v (Serving Layer)
+------------------------------------------------------------------------------------+
|                          POWER BI / DUCKDB / POSTGRES BI                           |
+------------------------------------------------------------------------------------+
```

---

## 2. Layer Schemas & Storage Design

### 2.1 Bronze Landing Zone
- **Format**: Immutable raw binary Protobuf (`.pb`) for GTFS-RT, raw `.zip` for static GTFS, and raw `.json` for weather observations.
- **Partitioning**: `ingest_date=YYYY-MM-DD/ingest_hour=HH/`
- **Metadata**: Standard `_ingested_at` timestamp and `_source_url` appended to landing manifests.

### 2.2 Silver Layer (Cleansed & Enriched Delta Tables)

#### `silver_vehicle_positions`
- `vehicle_id` (STRING, PK)
- `trip_id` (STRING)
- `route_id` (STRING)
- `latitude` (DOUBLE), `longitude` (DOUBLE)
- `bearing` (DOUBLE), `speed` (DOUBLE)
- `current_status` (STRING: `IN_TRANSIT_TO`, `STOPPED_AT`, `INCOMING_AT`)
- `timestamp_utc` (TIMESTAMP)
- `lat_grid` (DOUBLE), `lon_grid` (DOUBLE) -> Binned to 2 decimal places (~1.1km grid)

#### `silver_trip_updates`
- `update_id` (STRING, PK: Hash of trip_id + stop_id + timestamp)
- `trip_id` (STRING), `route_id` (STRING), `stop_id` (STRING)
- `stop_sequence` (INT)
- `arrival_delay_seconds` (INT), `departure_delay_seconds` (INT)
- `arrival_time_utc` (TIMESTAMP), `departure_time_utc` (TIMESTAMP)
- `schedule_relationship` (STRING: `SCHEDULED`, `ADDED`, `CANCELED`)

#### `silver_weather_observations`
- `lat_grid` (DOUBLE), `lon_grid` (DOUBLE) -> PK component 1
- `timestamp_hour_utc` (TIMESTAMP) -> PK component 2
- `temperature_celsius` (DOUBLE), `precipitation_mm` (DOUBLE)
- `snowfall_cm` (DOUBLE), `wind_speed_kmh` (DOUBLE)
- `visibility_meters` (DOUBLE), `weather_condition` (STRING)

---

## 3. Spatiotemporal Join Strategy

Weather data is joined with transit telemetry using PySpark window joins:
1. **Spatial Join**: Coordinates from `silver_trip_updates` or `silver_vehicle_positions` map to `lat_grid` and `lon_grid`.
2. **Temporal Join**: Telemetry timestamps map to the top of the hour:
   ```sql
   date_trunc('hour', arrival_time_utc) = timestamp_hour_utc
   ```
3. **Execution**: Broadcast join on `silver_weather_observations` since weather grid cardinality is small relative to vehicle update streams.

---

## 4. Scaling & Performance Benchmarks
- **Estimated Ingestion Throughput**: ~10.5 GB raw landed data daily across 15-second polling intervals.
- **Silver Delta Storage Compression**: Snappy-compressed Parquet, Z-ORDER indexed on `(route_id, stop_id)`.
- **Target Gold Query Latency**: < 1.0s for 30-day aggregated OTP dashboard queries in DuckDB/PostgreSQL.
