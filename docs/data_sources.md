# Data Sources Research & Ingestion Catalog

> **Phase 1 Complete**: Evaluated Transit & Weather Feeds, Field Mappings & Ingestion Policies

---

## 1. Selected Production Data Sources

### 1.1 Primary Transit Feed: MBTA GTFS & GTFS-Realtime (Boston, MA)
- **Agency Name**: Massachusetts Bay Transportation Authority (MBTA)
- **Static GTFS Feed**: `https://cdn.mbta.com/MBTA_GTFS.zip` (Daily update)
- **GTFS-RT VehiclePositions**: `https://cdn.mbta.com/realtime/VehiclePositions_enhanced.json` or Protobuf (`https://api-v3.mbta.com/gtfs/realtime/v3/vehicle-positions`)
- **GTFS-RT TripUpdates**: `https://cdn.mbta.com/realtime/TripUpdates_enhanced.json` or Protobuf (`https://api-v3.mbta.com/gtfs/realtime/v3/trip-updates`)
- **GTFS-RT ServiceAlerts**: `https://cdn.mbta.com/realtime/Alerts_enhanced.json`
- **Authentication**: Optional API Key via `x-api-key` header (Free key increases rate limit from 20 to 1,000 req/min).
- **Update Frequency**: Real-time streaming every 10–15 seconds.
- **Licensing**: CC0 1.0 Universal / Public Domain.
- **Raw Landing Path**: `data/raw_landing/mbta/{feed_type}/YYYY-MM-DD/HH/`

### 1.2 Secondary Transit Feed: NYC MTA GTFS-Realtime (New York, NY)
- **Agency Name**: New York City Transit (MTA)
- **Feed Endpoints**: `https://api-endpoint.mta.info/Dataservice/mtagtfsotb/nyct%2Fgtfs` (Subway Lines 1-7, ACE, BDFM, NQRW, L, SIR)
- **Format**: Protocol Buffers with NYCT extension (`nyct-subway.proto`).
- **Authentication**: No API Key required for subway feeds.
- **Update Frequency**: Every 30 seconds.
- **Licensing**: MTA Open Data License.
- **Raw Landing Path**: `data/raw_landing/mta_subway/YYYY-MM-DD/HH/`

### 1.3 Primary Weather Feed: Open-Meteo Weather API
- **Provider**: Open-Meteo (Global Reanalysis & Forecast)
- **Endpoints**: `https://api.open-meteo.com/v1/forecast` and `https://archive-api.open-meteo.com/v1/archive`
- **Parameters**: `latitude`, `longitude`, `hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,wind_speed_10m,visibility`
- **Authentication**: None required for non-commercial tier (<10,000 calls/day).
- **Update Frequency**: Hourly updates.
- **Licensing**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Raw Landing Path**: `data/raw_landing/weather/YYYY-MM-DD/HH/`

---

## 2. Rejected Data Sources & Evaluation Rationale

| Source Name | Category | Reason for Rejection |
| :--- | :--- | :--- |
| **511 SF Bay Area GTFS-RT** | Transit | Strict default rate limit of 60 req/hour per free API key; insufficient for 15s streaming ingestion. |
| **Transitland v2 API** | Aggregator | Secondary aggregator introducing latency; strict free tier rate limits. Kept for static metadata lookup only. |
| **Transport for London (TfL)** | Transit | Non-GTFS native schema (uses NaPTAN IDs & SIRI format), requiring complex proprietary wrappers. |
| **National Weather Service (NWS)**| Weather | US-only coverage, complex grid-point lookup protocol; retained as secondary fallback for US stations. |
| **OpenWeatherMap API** | Weather | Free tier capped at 1,000 requests/day, making spatial grid sampling expensive. |

---

## 3. Detailed Data Field Contracts

### 3.1 GTFS Static Reference Tables (`routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`)
- `route_id`, `route_short_name`, `route_long_name`, `route_type` (0=Tram, 1=Subway, 2=Rail, 3=Bus)
- `stop_id`, `stop_name`, `stop_lat`, `stop_lon`, `zone_id`
- `trip_id`, `service_id`, `shape_id`
- `arrival_time`, `departure_time`, `stop_sequence`

### 3.2 GTFS-RT Telemetry Fields (`VehiclePositions`, `TripUpdates`)
- `vehicle.id`, `trip.trip_id`, `trip.route_id`
- `position.latitude`, `position.longitude`, `position.bearing`, `position.speed`
- `stop_time_update.stop_id`, `stop_time_update.stop_sequence`
- `stop_time_update.arrival.delay`, `stop_time_update.departure.delay` (Delay seconds)

### 3.3 Open-Meteo Weather Fields
- `lat_grid`, `lon_grid` (Rounded to 2 decimal places ~1.1km cell)
- `timestamp_hour_utc` (Truncated ISO-8601 string)
- `temperature_celsius`, `precipitation_mm`, `snowfall_cm`, `wind_speed_kmh`, `visibility_meters`, `weather_code`

---

## 4. API Validation Checklist
- [x] Endpoint accessible over HTTPS without basic auth blocks
- [x] Protobuf & JSON streams parsed without binary decoding errors
- [x] Timestamps converted to UTC ISO-8601 strings (`YYYY-MM-DDTHH:MM:SSZ`)
- [x] Latitude/Longitude coordinates validated within WGS84 geographic bounding boxes
- [x] Vehicle IDs and Trip IDs validated against GTFS static reference tables
- [x] Weather spatial coordinates binned to 1.1km grid cells for PySpark window joins
