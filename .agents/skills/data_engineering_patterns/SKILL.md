---
name: data-engineering-patterns
description: Core standards for schema design, Delta Lake medallion architecture, PySpark transformations, and data quality testing.
---

# Skill: Data Engineering Patterns

## Medallion Data Architecture Standards

### Bronze Layer (Landing Zone)
- **Format**: Original feed formats (Raw JSON, GTFS CSV, Binary Protobuf).
- **Partitioning**: Partition by `ingest_date=YYYY-MM-DD/ingest_hour=HH`.
- **Metadata Fields**: Append `_ingested_at` (timestamp) and `_source_file` (string).

### Silver Layer (Cleansed & Enriched)
- **Format**: Delta Lake (`.delta`).
- **Cleaning Rules**:
  - Cast types explicitly using PySpark `StructType`.
  - Filter out invalid timestamps (e.g. Unix epoch 0 or future timestamps beyond buffer).
  - Deduplicate records based on primary key combinations (e.g. `vehicle_id` + `timestamp`).
  - Standardize coordinate bounds (Latitude -90 to 90, Longitude -180 to 180).

### Gold Layer (Business & Dimensional Analytics)
- **Format**: Delta Lake / Data Warehouse tables.
- **Modeling**: Kimball Star Schema.
  - Dimension Tables: `dim_routes`, `dim_stops`, `dim_agencies`, `dim_dates`.
  - Fact Tables: `fact_vehicle_positions`, `fact_trip_updates`, `fact_daily_stop_performance`.
- **Optimization**: Z-ORDER on high-cardinality join fields (`route_id`, `stop_id`).

## PySpark Transformation Patterns
- **Pure Functions**: Write PySpark functions that accept DataFrames and return DataFrames.
- **Explicit Schema Enforcement**: Never rely on `inferSchema=True` for production ingest.
- **Idempotency**: Use Delta `MERGE INTO` or overwrite partition strategies to guarantee repeatable runs.

## Data Quality & Validation
- Implement Great Expectations or dbt test validations:
  - Null check on primary keys.
  - Range checks on delays (e.g. -3600s to +86400s).
  - Foreign key referential checks (all `trip_id` values match static GTFS trips where available).
