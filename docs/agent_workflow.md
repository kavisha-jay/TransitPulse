# Agent Workflow & Operating Protocols

## 1. Overview
This document defines how specialized AI agents collaborate across different development phases of TransitPulse.

## 2. Agent Roster & Key Duties

| Agent Name | Role | Main Output |
| :--- | :--- | :--- |
| **Lead Engineer** | Architecture definition, phase coordination, code reviews, quality gatekeeper | Architecture specs, implementation plans, code approval |
| **Data Researcher** | API investigation, schema profiling, GTFS feed validation | `docs/data_sources.md`, raw data samples, schema contracts |
| **PySpark Engineer** | Bronze-to-Silver PySpark transformations, Delta Lake management | `src/processing/`, PySpark ETL jobs, pytest suites |
| **Analytics Engineer**| Gold-layer star schema modeling, dbt models, Power BI readiness | `src/analytics/`, dbt models, analytics SQL views |

## 3. Workflow Phase Lifecycle

```
[Phase 0: Bootstrap & Infrastructure Setup]
   └── Lead Engineer establishes context, skills, agent definitions & configs.
         │
         v
[Phase 1: Data Ingestion & API Research]
   └── Data Researcher profiles feeds & defines landing specs.
   └── Lead Engineer approves data ingestion schemas.
         │
         v
[Phase 2: PySpark Processing & Delta Lake Ingestion]
   └── PySpark Engineer implements Bronze -> Silver PySpark jobs & unit tests.
   └── Lead Engineer conducts code review & validates idempotency.
         │
         v
[Phase 3: Analytics Engineering & Gold Layer]
   └── Analytics Engineer builds dbt star schema models & Gold layer views.
   └── PySpark / Analytics Engineer tests data quality & constraints.
         │
         v
[Phase 4: Dashboarding & BI Verification]
   └── Analytics Engineer configures BI dataset connectors and dashboards.
```

## 4. Operational Rules for Agents
1. **Always Consult Context**: Before starting a task, agents must read `docs/PROJECT_CONTEXT.md` and check `.agents/skills/`.
2. **Deterministic Changes**: Never introduce breaking schema changes without updating the master schema contract.
3. **Automated Verification**: Every feature implementation must include accompanying unit tests or validation scripts.
