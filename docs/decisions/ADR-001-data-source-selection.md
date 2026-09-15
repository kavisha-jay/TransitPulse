# ADR-001: Data Source Selection & Integration Strategy

## Status
**Accepted**

## Context
TransitPulse requires high-frequency real-time transit telemetry, comprehensive static GTFS schedule metadata, and aligned weather observations to calculate on-time performance (OTP), headway adherence, and delay root-cause correlations. 

To determine the production data foundation for TransitPulse, we evaluated seven candidate transit and weather feeds across key criteria: field availability (delays, trip/stop granularity), update frequency, API authentication, rate limits, licensing, and schema standardization.

## Decision Drivers
1. **Native GTFS & GTFS-Realtime (GTFS-RT) Standard**: Preference for feeds adhering strictly to `gtfs-realtime.proto` (VehiclePositions, TripUpdates).
2. **Delay & Granularity**: Mandatory presence of `arrival.delay`, `departure.delay`, `vehicle.id`, `trip.id`, `stop_id`, and geo-coordinates (`latitude`, `longitude`).
3. **Ingestion Efficiency**: Low rate-limiting barriers allowing 15–30 second polling intervals.
4. **Joinability with Weather**: Spatiotemporal alignment via UTC timestamps and WGS84 coordinates.
5. **Open Licensing**: Non-restrictive public domain or CC-BY licensing suitable for lakehouse pipeline execution.

## Evaluated Options

| Option | Type | Format | Key Strengths | Limitations | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MBTA V3 & GTFS-RT** | Transit | GTFS Static ZIP + GTFS-RT Protobuf/JSON | Real-time delays, vehicle telemetry, HTTP 304 caching, free API key (1,000 req/min) | Regional focus (Boston metro) | **SELECTED (Primary Transit Source)** |
| **NYC MTA GTFS-RT** | Transit | GTFS-RT Protobuf + NYCT Extensions | High volume subway & rail telemetry, no API key required for subway feeds | Requires custom NYCT Protobuf extensions (`nyct-subway.proto`) | **SELECTED (Secondary Transit Source)** |
| **Open-Meteo Weather API**| Weather | JSON REST API | Global hourly forecast & historical reanalysis (back to 1940), lat/lon querying | Hourly resolution (requires window join) | **SELECTED (Primary Weather Source)** |
| **511 SF Bay Area** | Transit | GTFS-RT Protobuf | Consolidated regional feeds for 30+ Bay Area operators | Strict free rate limit (60 req/hour) insufficient for 15s streaming | **REJECTED** |
| **TfL Unified API** | Transit | Custom JSON / SIRI-VM | Comprehensive London transit network data | Non-GTFS native schema; requires TransXChange/SIRI parsers | **REJECTED** |
| **Transitland v2 API** | Aggregator | REST / GeoJSON | Global static GTFS aggregator | Free tier rate limits; best for metadata lookup rather than streaming | **REJECTED (Metadata Only)** |
| **NWS (weather.gov)** | Weather | REST JSON-LD | Official US government weather data, free without API key | US-only coverage; complex grid point lookup protocol | **REJECTED (Secondary Backup)** |

## Selected Data Architecture & Join Strategy

### Primary Transit Feed: MBTA GTFS & GTFS-RT
- **Static GTFS**: Daily download of `MBTA_GTFS.zip` containing `routes.txt`, `trips.txt`, `stops.txt`, `stop_times.txt`.
- **GTFS-RT VehiclePositions**: Polled every 15s from `https://cdn.mbta.com/realtime/VehiclePositions_enhanced.json` (or Protobuf).
- **GTFS-RT TripUpdates**: Polled every 15s from `https://cdn.mbta.com/realtime/TripUpdates_enhanced.json` (or Protobuf).

### Primary Weather Feed: Open-Meteo Hourly API
- **Endpoint**: `https://api.open-meteo.com/v1/forecast` and `https://archive-api.open-meteo.com/v1/archive`
- **Parameters**: `latitude`, `longitude`, `hourly=temperature_2m,precipitation,wind_speed_10m,weather_code,visibility`

### Spatiotemporal Join Methodology
- **Spatial Join**: Map vehicle/stop coordinates (`stop_lat`, `stop_lon`) to weather grid points using bounding boxes or spatial nearest-neighbor logic (rounded to 2 decimal places ~1.1km grid).
- **Temporal Join**: Truncate transit event timestamps (`UTC ISO-8601`) to the top of the hour (`date_trunc('hour', timestamp)`) to join with Open-Meteo hourly weather metrics.

## Consequences
- **Positive**: High fidelity real-time delay tracking, robust free tier rate limits, seamless PySpark window joins.
- **Negative**: Need to maintain NYCT Protobuf schemas if expanding to NYC MTA; hourly weather resolution requires smoothing for micro-burst storms.
