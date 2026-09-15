---
name: transitpulse-context
description: Project rules, architecture standards, directory layout, and design decisions for TransitPulse.
---

# Skill: TransitPulse Context & System Governance

## Project Mission
TransitPulse is an enterprise-grade real-time and batch public transit analytics platform. It ingests static GTFS and dynamic GTFS-Realtime (Protobuf) feeds, processes them via a PySpark Medallion Data Lakehouse architecture, models data using dbt/dimensional schemas, and renders dashboards for transit performance.

## Architectural Principles
1. **Medallion Lakehouse Pattern**:
   - **Bronze**: Raw landed payloads (JSON/Protobuf/CSV), immutable, partitioned by date/hour.
   - **Silver**: Cleansed, schema-validated, deduplicated, and enriched PySpark Delta tables.
   - **Gold**: Business aggregations, star-schema dimensional models (`dim_*`, `fact_*`) ready for dbt and Power BI.
2. **Modular Code Standard**:
   - Clear separation between Ingestion, Processing, Analytics, and Infrastructure code.
   - Configuration over hardcoding: all parameters managed via environment variables and yaml configs.
3. **Quality & Testability**:
   - All PySpark functions must be modular and covered by unit tests.
   - dbt models must include standard schema tests (`not_null`, `unique`, `relationships`).

## Directory Layout Blueprint
```
TransitPulse/
├── .agents/
│   ├── agents/            # Role definitions for AI collaborators
│   └── skills/            # Architectural and engineering patterns
├── docs/                  # Project specifications and architecture docs
├── data/                  # Local data storage (Git ignored)
│   ├── raw_landing/       # Bronze data landing zone
│   ├── delta_warehouse/   # Silver & Gold Delta tables
│   └── static_gtfs/       # Downloaded static GTFS zips
├── src/                   # Core application source code
│   ├── ingestion/         # API connectors & ingestors
│   ├── processing/        # PySpark ETL transformations
│   ├── analytics/         # dbt models & SQL queries
│   └── utils/             # Shared helpers (logging, config, spark session)
├── tests/                 # Unit and integration test suite
├── docker-compose.yml     # Infrastructure stack
├── pyproject.toml         # Python dependencies & tools config
└── .env.example           # Template environment configuration
```
