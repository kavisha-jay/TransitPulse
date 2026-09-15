# TransitPulse - Project Context & Master Specification

> **Single Source of Truth** for TransitPulse Architecture, Data Engineering, and Analytics.

---

## 1. Executive Summary
TransitPulse is a modern, enterprise-grade Data Lakehouse and Analytics Platform designed to monitor, analyze, and optimize public transportation networks in real-time and historical contexts. By blending static GTFS schedules with dynamic GTFS-Realtime telemetry and external data (Open-Meteo hourly weather observations), TransitPulse empowers transit agencies and data analysts with real-time tracking, delay diagnostics, headway adherence analysis, and on-time performance (OTP) insights.

---

## 2. Current Project Phase & Status
- **Current Phase**: **Phase 1: Project Discovery & Architecture (COMPLETED)**
- **Next Phase**: **Phase 2: PySpark Processing & Delta Lake Ingestion (READY)**
- **Selected Primary Data Feeds**:
  - **Transit (Primary)**: MBTA (Boston) GTFS Static + GTFS-RT Protobuf (VehiclePositions & TripUpdates)
  - **Transit (Secondary)**: NYC MTA Subway GTFS-RT Feeds
  - **Weather (Primary)**: Open-Meteo Hourly Weather API (Global ERA5 + Forecast)

---

## 3. Core Business Goals & Key Performance Indicators (KPIs)
- **On-Time Performance (OTP)**: Percentage of arrivals/departures within standard SLA window (-60s early to +300s late).
- **Weather-Induced Delay Impact**: Correlation of precipitation (>5mm/hr), snowfall (>2cm), and high winds (>35km/h) against mean arrival delays.
- **Average Delay by Route/Stop**: Real-time delay metrics aggregated by route ID, stop ID, and time of day.
- **Headway Adherence & Bus Bunching**: Measurement of spacing consistency and variance between consecutive vehicles on high-frequency transit lines.
- **Fleet Utilization & Speed Diagnostics**: Tracking active vehicles, speed distributions, and congested bottlenecks.

---

## 4. Technology Stack & Infrastructure
- **Programming Language**: Python 3.11+
- **Data Ingestion & Parsing**: `requests`, `google-transit-protobuf`, `pydantic`
- **Data Processing & ETL**: Apache Spark / PySpark 3.5+, Delta Lake 3.x
- **Data Warehousing & Modeling**: dbt (data build tool), DuckDB / PostgreSQL / TimescaleDB
- **Storage Layer**: MinIO / S3 API compatible object store for Delta Lake tables
- **Orchestration & Containerization**: Docker, Docker Compose
- **Quality & Testing**: `pytest`, `ruff`, dbt-expectations / Great Expectations

---

## 5. Medallion Lakehouse Architecture Overview
```
+-----------------------------------------------------------------------------------+
|                                 BRONZE LAYER                                      |
| Raw landed GTFS static ZIP feeds, GTFS-RT Protobuf streams & Open-Meteo JSON      |
| Storage: MinIO / S3 Object Store (Partitioned by date/hour)                       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v (PySpark Cleanse, Parse & Deduplicate)
+-----------------------------------------------------------------------------------+
|                                 SILVER LAYER                                      |
| Cleansed, validated Delta Lake tables (silver_vehicle_positions, silver_trip_updates, |
| silver_weather_observations, dim_routes, dim_stops, dim_trips)                    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v (PySpark / dbt Aggregations & Star Schema)
+-----------------------------------------------------------------------------------+
|                                  GOLD LAYER                                       |
| Star schema analytics models (fact_trip_updates, fact_daily_otp, fact_vehicle_speed)|
+-----------------------------------------------------------------------------------+
                                          |
                                          v (BI Layer)
+-----------------------------------------------------------------------------------+
|                         POWER BI / SUPERSET / DASHBOARDS                          |
+-----------------------------------------------------------------------------------+
```

---

## 6. Key Decisions & Risks

### Architectural Decisions
- **ADR-001**: Selected MBTA V3 API & GTFS-RT + Open-Meteo Weather API. Standardized spatiotemporal joins using 1.1km lat/lon grid binning and hourly UTC timestamps.

### Identified Risks & Mitigations
- **API Throttling & Network Outages**: Mitigated using exponential backoff retries, jitter, and persistent landing to Bronze prior to processing.
- **Protobuf Extension Schema Drift**: Mitigated using explicit PySpark schema definitions with nullable struct fields.
- **Static vs. Realtime ID Mismatches**: Mitigated using daily static GTFS updates and left-anti quality checks.
