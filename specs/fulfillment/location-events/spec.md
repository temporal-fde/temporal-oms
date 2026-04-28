# Location Events Activity Specification

**Feature Name:** `get_location_events` — Supply Chain Risk via Weather + Major Events
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-28
**Updated:** 2026-04-28

---

## Overview

### Executive Summary

The `get_location_events` activity provides supply chain risk data for a geographic location,
consumed by `ShippingAgent` to inform shipping recommendation outcomes (`MARGIN_SPIKE`,
`SLA_BREACH`, etc.). It was originally designed to call PredictHQ, which is no longer available.

This spec replaces PredictHQ with two free, simple public APIs: **Open-Meteo** for weather
disruption signals and **Ticketmaster Discovery** for major local events (traffic congestion risk).
Both APIs are lat/lng-native, require no credit card, and return data that workshop participants
can immediately reason about. The activity merges results from both sources into the same
`LocationRiskSummary` + `[LocationEvent]` response shape that `ShippingAgent` already expects —
no downstream changes required.

An optional **scenario override** mechanism lets workshop facilitators inject a specific risk
level for a coordinate without touching real APIs, enabling reliable demo scenarios regardless of
what weather or events happen to be occurring on the day.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Replace PredictHQ with free, zero-friction APIs that work in a workshop Codespace
  without billing setup
- Goal 2: Preserve the existing `GetLocationEventsRequest/Response` proto contract so
  `ShippingAgent` requires no changes
- Goal 3: Produce plausible, real-world risk signals that drive interesting LLM reasoning
  (not always LOW, occasionally MEDIUM/HIGH without hardcoding)
- Goal 4: Provide a workshop override layer so facilitators can force a HIGH/MEDIUM risk scenario
  on demand for exercises

### Acceptance Criteria

- [ ] Activity receives `Coordinate` (lat/lng) + `within_km` + date range and returns
      `LocationRiskSummary` with `risk_level` + `[LocationEvent]`
- [ ] Open-Meteo is called for weather; precipitation, wind, and snowfall thresholds map to
      `WEATHER_DISRUPTION` events at MEDIUM or HIGH risk
- [ ] Ticketmaster is called for local events; events at large-capacity venues within the radius
      map to `MAJOR_EVENT` events at MEDIUM or HIGH risk
- [ ] Both upstream calls execute concurrently within the activity
- [ ] `risk_level` on `LocationRiskSummary` reflects the highest risk level across all events
- [ ] If no events exceed LOW threshold, `risk_level` is `LOW` and `events` is empty
- [ ] A `LOCATION_EVENTS_OVERRIDE` environment variable (JSON map of `"lat,lng" → RiskLevel`)
      bypasses real API calls for that coordinate — used by workshop facilitators only
- [ ] Activity is registered on the existing `fulfillment` task queue — no separate queue needed
- [ ] Open-Meteo calls require no API key; Ticketmaster calls use `TICKETMASTER_API_KEY` env var
- [ ] If Ticketmaster key is absent, the activity logs a warning and returns weather-only results
      (graceful degradation — workshop participants without a key still get weather risk)

---

## Current State (As-Is)

### What Exists Today

- `GetLocationEventsRequest` / `GetLocationEventsResponse` protos defined in
  `proto/acme/fulfillment/domain/v1/shipping_agent.proto`
- `LocationEvent`, `LocationRiskSummary`, `RiskLevel` defined in
  `proto/acme/common/v1/values.proto`
- Activity stub at `python/fulfillment/src/agents/activities/location_events.py` — the
  function signature and Temporal decorator exist but the body calls PredictHQ
- Activity is registered on the fulfillment worker and `ShippingAgent` calls it via tool dispatch

### Pain Points / Gaps

- PredictHQ requires a paid account not available for this workshop
- PredictHQ's API is more complex than needed (categories, labels, phq_attendance scoring)
- No fallback when the API is unavailable — any error propagates to the LLM as a tool failure
- No way for workshop facilitators to force a specific risk scenario for exercises

---

## Desired State (To-Be)

### Architecture Overview

```
ShippingAgent (LLM tool dispatch)
        │
        ▼
get_location_events(coordinate, within_km, date_range)
        │
        ├─── [concurrent] ──────────────────────────────────────────────────┐
        │                                                                   │
        ▼                                                                   ▼
Open-Meteo Forecast API                                     Ticketmaster Discovery API
GET /v1/forecast?latitude=...                               GET /discovery/v2/events?
  &hourly=precipitation,windspeed,snowfall                    latlong=lat,lng&radius=...
  &timezone=...                                               &startDateTime=...&endDateTime=...
  &start_date=...&end_date=...
        │                                                                   │
        ▼                                                                   ▼
  map conditions → [LocationEvent]                      map events → [LocationEvent]
  type: WEATHER_DISRUPTION                              type: MAJOR_EVENT
  risk: threshold-based                                 risk: venue capacity-based
        │                                                                   │
        └──────────────────────┬────────────────────────────────────────────┘
                               ▼
                   merge + derive LocationRiskSummary
                   (risk_level = max across all events)
                               │
                               ▼
                    GetLocationEventsResponse
```

If `LOCATION_EVENTS_OVERRIDE` env var is set and contains an entry for this coordinate, skip
both upstream calls and return a synthetic response directly.

### Key Capabilities

- **Weather risk signals**: real precipitation, wind, and snow data from Open-Meteo for the
  delivery date window — no API key required
- **Event congestion signals**: local concerts, sports, and festivals from Ticketmaster that
  cause traffic congestion near origin or destination
- **Graceful degradation**: Ticketmaster absent → weather-only; both fail → LOW risk with a
  logged warning (LLM can still reason, just without risk data)
- **Workshop override**: facilitators set an env var to inject HIGH risk for any coordinate,
  enabling reliable demo scenarios

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Open-Meteo for weather | No API key, no rate limits for demo scale, lat/lng native, JSON | OpenWeatherMap free tier lacks alerts; NWS is US-only |
| Ticketmaster for events | Free developer key, lat/lng+radius search built in, relatable to participants | GDELT (complex query model, noisy); SeatGeek (less known) |
| Concurrent upstream calls | Matches ShippingAgent's concurrency pattern; neither call depends on the other | Sequential would add ~500ms per location lookup |
| Separate `TICKETMASTER_API_KEY` env var | Ticketmaster requires an account; not everyone may have one | Bundling a single key risks rate limits across all workshop participants |
| Override via env var (not workflow signal) | Facilitator sets it once at worker startup; no per-call instrumentation needed | Signal-based override would require ShippingAgent changes |
| Stay on existing `fulfillment` task queue | Both APIs respond in <500ms; no throughput concern at workshop scale | Separate queue added complexity without benefit after removing PredictHQ's 50 rps limit |
| risk_level = max across events | Simple, conservative, matches how ShippingAgent uses it downstream | Weighted average would be more nuanced but harder to explain in workshop |

### Component Design

#### `get_location_events` Activity

- **Purpose:** Translate a geographic coordinate + time window into structured risk signals
- **Responsibilities:** Call Open-Meteo and Ticketmaster concurrently, map raw responses to
  `LocationEvent` protos, derive `LocationRiskSummary`, handle override injection
- **Interfaces:**
  - Input: `GetLocationEventsRequest` (coordinate, within_km, start_date, end_date, timezone)
  - Output: `GetLocationEventsResponse` (risk_summary: LocationRiskSummary, events: [LocationEvent])
  - Env vars: `TICKETMASTER_API_KEY`, `LOCATION_EVENTS_OVERRIDE`

#### Open-Meteo Client

- **Purpose:** Fetch hourly weather forecast for a coordinate + date range
- **Responsibilities:** Build request URL, parse hourly arrays, apply thresholds to emit events
- **Risk mapping:**

  | Condition | Threshold | Risk Level |
  |-----------|-----------|------------|
  | `precipitation_sum` (mm/day) | > 20 | HIGH |
  | `precipitation_sum` (mm/day) | 8–20 | MEDIUM |
  | `windspeed_10m_max` (km/h) | > 70 | HIGH |
  | `windspeed_10m_max` (km/h) | 45–70 | MEDIUM |
  | `snowfall_sum` (cm/day) | > 5 | HIGH |
  | `snowfall_sum` (cm/day) | 1–5 | MEDIUM |

  One `LocationEvent` per triggered condition per day. Event `description` is human-readable
  (e.g. "Heavy precipitation forecast: 28mm on 2026-04-30") so the LLM can cite it in reasoning.

#### Ticketmaster Discovery Client

- **Purpose:** Find major public events near a coordinate within the delivery date window
- **Responsibilities:** Build request with lat/lng, radius (within_km), date range; parse
  embedded venues for capacity; emit events above capacity threshold
- **Risk mapping:**

  | Venue Capacity | Risk Level |
  |----------------|------------|
  | > 50,000 | HIGH |
  | 10,000–50,000 | MEDIUM |
  | < 10,000 | (skip — not material to delivery risk) |

  If Ticketmaster does not return capacity, default to MEDIUM for any event returned.
  Event `description` includes event name, venue, and date.

#### Workshop Override

- **Purpose:** Allow facilitators to force a specific risk level for a coordinate
- **Format:** `LOCATION_EVENTS_OVERRIDE={"40.7128,-74.0060":"HIGH","34.0522,-118.2437":"MEDIUM"}`
- **Behavior:** If coordinate matches (within 0.01° tolerance), return a synthetic
  `LocationRiskSummary` with one synthetic event of the specified type; skip all upstream calls
- **Scope:** Workshop / local env only — never set in staging or production

### Data Model / Schemas

No proto changes required. All types already exist:

```protobuf
// proto/acme/common/v1/values.proto  (existing)
enum RiskLevel {
  RISK_LEVEL_UNSPECIFIED = 0;
  LOW = 1;
  MEDIUM = 2;
  HIGH = 3;
}

message LocationEvent {
  string event_type = 1;   // "WEATHER_DISRUPTION" | "MAJOR_EVENT"
  string description = 2;  // human-readable, cited by LLM
  RiskLevel risk_level = 3;
  string date = 4;         // ISO 8601 date
}

message LocationRiskSummary {
  RiskLevel risk_level = 1;  // max across all LocationEvents
  string summary = 2;         // e.g. "1 weather disruption, 1 major event"
}
```

```protobuf
// proto/acme/fulfillment/domain/v1/shipping_agent.proto  (existing)
message GetLocationEventsRequest {
  Coordinate coordinate = 1;
  int32 within_km = 2;
  string start_date = 3;
  string end_date = 4;
  string timezone = 5;
}

message GetLocationEventsResponse {
  LocationRiskSummary risk_summary = 1;
  repeated LocationEvent events = 2;
}
```

### Configuration / Deployment

| Variable | Required | Description |
|----------|----------|-------------|
| `TICKETMASTER_API_KEY` | Optional | Ticketmaster Discovery API key. If absent, Ticketmaster lookups are skipped. |
| `LOCATION_EVENTS_OVERRIDE` | Optional | JSON map of `"lat,lng" → RiskLevel string` for workshop scenario injection. |

Open-Meteo requires no configuration.

Worker deployment: activity runs on the existing `fulfillment` task queue worker. No new
worker or task queue needed.

---

## Implementation Strategy

### Phases

**Phase 1: Open-Meteo Integration**
- Implement `open_meteo.py` client — fetch daily aggregates for date range, apply thresholds,
  return `[LocationEvent]`
- Update `location_events.py` activity body to call Open-Meteo and return weather-only results
- Verify with a real coordinate + date (should produce deterministic results for past dates)

**Phase 2: Ticketmaster Integration**
- Implement `ticketmaster.py` client — search events by lat/lng + radius + date range,
  map capacity to risk level, return `[LocationEvent]`
- Wire into activity alongside Open-Meteo (concurrent async calls)
- Graceful degradation: if `TICKETMASTER_API_KEY` absent or call fails, log and skip

**Phase 3: Merge + Risk Derivation**
- Combine events from both sources
- Derive `LocationRiskSummary.risk_level` as max across all events
- Build human-readable `summary` string for LLM context
- Return `GetLocationEventsResponse`

**Phase 4: Workshop Override**
- Parse `LOCATION_EVENTS_OVERRIDE` at activity startup
- Add coordinate-match check (0.01° tolerance) before upstream calls
- Return synthetic response with one descriptive event when override matches

### Critical Files

To Modify:
- `python/fulfillment/src/agents/activities/location_events.py` — replace PredictHQ body with
  Open-Meteo + Ticketmaster implementation; add override check

To Create:
- `python/fulfillment/src/agents/activities/clients/open_meteo.py` — Open-Meteo HTTP client
- `python/fulfillment/src/agents/activities/clients/ticketmaster.py` — Ticketmaster HTTP client

---

## Testing Strategy

### Unit Tests

- Weather threshold mapping: verify each threshold boundary produces correct `RiskLevel`
- Ticketmaster capacity mapping: verify capacity ranges map to correct risk levels
- Risk derivation: verify `LocationRiskSummary.risk_level` = max across mixed-risk event list
- Override: verify env var match returns synthetic response and skips HTTP calls
- Graceful degradation: verify missing Ticketmaster key returns weather-only result without error

### Integration Tests

- Real Open-Meteo call for a known past date with known weather (e.g. a hurricane landfall date)
  → assert HIGH risk event returned
- Real Ticketmaster call for a city known to have upcoming events → assert at least one event
  returned when key is present
- Full activity invocation via Temporal test environment with mocked HTTP clients

### Validation Checklist

- [ ] Unit tests pass for all threshold boundaries
- [ ] Activity runs end-to-end in Temporal test environment
- [ ] ShippingAgent workshop demo shows at least one HIGH or MEDIUM risk scenario naturally
- [ ] Override mechanism reliably forces HIGH risk for a New York City coordinate
- [ ] Graceful degradation verified: activity succeeds with no Ticketmaster key set

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Ticketmaster returns no events on demo day | LOW risk always → less interesting LLM reasoning | Medium | Use override for key demo moments; real weather still provides signal |
| Open-Meteo API unavailable | Activity fails; LLM tool call errors | Low | Catch HTTP errors, return LOW risk with logged warning (same as degradation path) |
| Ticketmaster free tier rate limits | Exceeded in workshop with many participants | Low | 5k calls/day on free tier; each participant makes ~2 calls per order |
| Coordinate format mismatch in override | Override never fires | Low | Add tolerance check (0.01°) and log when override coordinates are loaded |
| Workshop participants skip Ticketmaster signup | Weather-only results | Medium | Design exercises around weather signals; Ticketmaster is additive, not required |

---

## Dependencies

### External Dependencies

- **Open-Meteo Forecast API** — no account, no key, free indefinitely
  - Docs: https://open-meteo.com/en/docs
  - Endpoint: `https://api.open-meteo.com/v1/forecast`
- **Ticketmaster Discovery API v2** — free developer account, ~5k calls/day
  - Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
  - Endpoint: `https://app.ticketmaster.com/discovery/v2/events.json`

### Cross-Cutting Concerns

- **ShippingAgent**: consumes this activity unchanged — proto contract preserved, no call-site
  changes needed
- **Workshop spec**: Exercise 02 (observe ShippingAgent) and Exercise 03 (add a new tool) both
  depend on `get_location_events` producing non-trivial output; override mechanism supports this

### Rollout Blockers

- None — this is a drop-in replacement for the PredictHQ activity body. ShippingAgent,
  proto schemas, and worker registration are all already in place.

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [ ] Should Open-Meteo use hourly or daily aggregates? Daily is simpler (one value per day);
      hourly could map to a specific delivery time window but adds complexity.
- [ ] What `within_km` default should Ticketmaster use for the event search radius? The current
      proto default is 50km (from PredictHQ era) — is that appropriate for event congestion, or
      should it be tighter (e.g. 10–15km)?
- [ ] Should the override also support a `"*"` wildcard to force risk level for all coordinates?
      Useful for all-HIGH demo scenarios without enumerating addresses.

### Implementation Notes

- Open-Meteo `daily` endpoint (not `hourly`) is the right call — pass `daily=precipitation_sum,
  windspeed_10m_max,snowfall_sum` and aggregate across the date range. This avoids parsing
  thousands of hourly rows.
- Ticketmaster's lat/lng search uses `latlong=lat,lng` query param with `radius` and `unit=km`.
  The `_embedded.events[].\_embedded.venues[].upcomingEvents._total` field does NOT give capacity;
  use `_embedded.events[].\_embedded.venues[].upcomingEvents` or look for `capacity` in venue
  data. If capacity is absent (common), default to MEDIUM.
- The activity is `async def` — use `asyncio.gather` for concurrent Open-Meteo + Ticketmaster
  calls rather than Temporal's concurrent activity dispatch (we're inside one activity, not
  dispatching two).

---

## References & Links

- [ShippingAgent Spec](../../fulfillment-order/shipping-agent/spec.md) — upstream consumer of this activity
- [Open-Meteo API Docs](https://open-meteo.com/en/docs) — no-auth weather forecast API
- [Ticketmaster Discovery API Docs](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/)
- [values.proto](../../../proto/acme/common/v1/values.proto) — LocationEvent, LocationRiskSummary, RiskLevel definitions
- [shipping_agent.proto](../../../proto/acme/fulfillment/domain/v1/shipping_agent.proto) — GetLocationEventsRequest/Response
