---
name: api-integration-patterns
description: Guidelines for connecting to external transit APIs, parsing GTFS-Realtime Protobuf feeds, handling rate limits, retries, and ingestion resilience.
---

# Skill: API Integration Patterns

## Transit Data Source Types

### 1. Static GTFS (General Transit Feed Specification)
- **Format**: Zip archive containing standardized CSV files (`routes.txt`, `trips.txt`, `stop_times.txt`, `stops.txt`, `calendar.txt`).
- **Ingestion Strategy**: Scheduled daily or weekly HTTP download, extraction, validation, and loading into Silver reference tables.

### 2. GTFS Realtime (GTFS-RT)
- **Format**: Protocol Buffers (Protobuf) binary streams (`gtfs-realtime.proto`).
- **Sub-feeds**:
  - `FeedMessage.FeedEntity.vehicle`: Real-time location, bearing, speed, occupancy status.
  - `FeedMessage.FeedEntity.trip_update`: Real-time arrival/departure delay predictions per stop.
  - `FeedMessage.FeedEntity.alert`: Service disruptions and announcements.
- **Ingestion Strategy**: Polling at regular intervals (e.g. every 15-30 seconds) or consuming streaming feeds.

## API Resilience & Reliability Patterns
- **Exponential Backoff & Retry**: Wrap external HTTP requests with retries using jitter and backoff.
- **Circuit Breakers**: Gracefully handle downstream API failures without crashing the pipeline.
- **Rate Limit Compliance**: Respect HTTP `429 Too Many Requests` headers and configure query delays per API client.
- **Raw Payload Persistence**: Always persist the raw byte stream / JSON payload to Bronze landing BEFORE processing, ensuring full replay capability.
