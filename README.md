# TransitPulse - Real-Time & Batch Transit Lakehouse & Analytics Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Apache Spark 3.5](https://img.shields.io/badge/spark-3.5-orange.svg)](https://spark.apache.org/)
[![Delta Lake 3.1](https://img.shields.io/badge/delta_lake-3.1-blue.svg)](https://delta.io/)
[![dbt 1.7+](https://img.shields.io/badge/dbt-1.7+-red.svg)](https://www.getdbt.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

TransitPulse is an enterprise-grade real-time and batch public transit analytics platform built with Python, PySpark, Delta Lake, PostgreSQL, LocalStack/MinIO, and Airflow. It ingests static GTFS schedules, dynamic GTFS-Realtime (Protobuf) telemetry, and Open-Meteo weather data to produce actionable transit performance diagnostics and dashboards.

---

## 🏗️ Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                 BRONZE LAYER                                      |
| Raw landed GTFS static ZIP feeds, GTFS-RT Protobuf streams & Open-Meteo JSON      |
| Storage: MinIO / LocalStack S3 (Partitioned by date/hour)                         |
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
|                         POWER BI / SUPERSET / POSTGRES BI                         |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.9+ or Python 3.11+
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/kavisha-jay/TransitPulse.git
cd TransitPulse

# Copy environment template
cp .env.example .env

# Start local infrastructure stack (PostgreSQL, LocalStack, Airflow, Jupyter)
docker-compose up -d
```

### 3. Local Python Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -e .[dev]
```

### 4. Run Test Suite
```bash
pytest
```

---

## 📂 Repository Structure

```
TransitPulse/
├── .agents/               # AI agent definitions & skill guidance
├── airflow/               # Apache Airflow DAGs & plugins
├── data/                  # Data storage landing (git-ignored)
│   ├── sample/            # Sample GTFS reference files
│   ├── raw/               # Raw landing zone
│   └── processed/         # Cleansed & processed outputs
├── dbt/                   # dbt analytics transformation project
├── docs/                  # System documentation & ADRs
├── ingestion/             # API connectors & ingestors
├── spark/                 # PySpark batch & streaming ETL scripts
├── src/                   # Core Python application modules
├── tests/                 # Comprehensive test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── spark/             # PySpark job tests
│   └── data_quality/      # Data contract & quality tests
├── warehouse/             # Database initialization schemas & DDLs
├── docker-compose.yml     # Local dev infrastructure stack
├── pyproject.toml         # Build system & dependency specifications
├── pytest.ini             # Pytest test runner configuration
└── README.md              # Project overview & guide
```

---

## 📄 Documentation Links
- [Master Project Context](docs/PROJECT_CONTEXT.md)
- [Agent Workflow Guide](docs/agent_workflow.md)
- [Architecture Specification](docs/architecture.md)
- [Data Sources & Ingestion Catalog](docs/data_sources.md)
- [ADR-001 Data Source Selection](docs/decisions/ADR-001-data-source-selection.md)

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
