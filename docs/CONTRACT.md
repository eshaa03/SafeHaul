# SafeHaul Kerala — API Contract

**Owner:** Member A  
**Source of truth:** `docs/TEAM_BRIEF.md` §1.10  
**Rule:** do not change field names without E's approval. Additive fields are OK.  
**Last updated:** 2026-10-08

---

## Common Conventions

| Convention | Value |
|---|---|
| Timestamps | ISO 8601 with timezone, e.g. `2026-10-07T14:30:00+05:30` |
| Coordinates | `[lat, lng]` |
| `scenario` param | `"normal"` or `"flood"`. Every endpoint accepts `?scenario=`; otherwise uses the server-wide default set via `POST /api/scenario/` |
| `risk_level` | `"low" \| "medium" \| "high" \| "closed"` |
| `confidence` | `"high" \| "moderate" \| "low"` |
| `data_source` | `"live" \| "simulated" \| "historical"` |

---

## Endpoints

| Method + Path | Purpose | Built by |
|---|---|---|
| `GET /api/scenario/` | Return current server-wide scenario | A |
| `POST /api/scenario/` | Switch scenario (demo toggle) | A |
| `GET /api/routes/` | Candidate routes (id, name, distance, ordered segment IDs) | A |
| `GET /api/segments/?scenario=` | All segments with computed risk | A |
| `POST /api/trip/options/` | Trip form in → 2–3 labelled options out | A |
| `GET /api/service-points/?mode=normal\|emergency&position_segment_id=&vehicle_type=&scenario=` | Service points ranked by safe reachable time | A |
| `GET /api/fleet/?scenario=` | Simulated fleet with risk, ETA, go/hold/divert (stretch A6) | A |
| `GET /api/rainfall/?lat=&lng=` | Rainfall (24 h past, 3 h forecast) with source | C (in `weather/`) |
| `POST /api/emergency/` | Submit an emergency packet | D |
| `GET /api/emergency/?since=` | List emergency events (station dashboard polls this) | D |
| `POST /api/emergency/<id>/ack/` | Station acknowledges an event | D |

---

## `GET /api/scenario/`

**Response**
```json
{"scenario": "normal"}
```

---

## `POST /api/scenario/`

**Request body**
```json
{"scenario": "flood"}
```

**Response**
```json
{"scenario": "flood"}
```

**Error (400)**
```json
{"error": "Invalid scenario 'xyz'. Choose from: ['flood', 'normal']."}
```

---

## `GET /api/routes/`

**Response** — array of route metadata objects.

```json
[
  {
    "route_id": "main",
    "name": "Main route via Thrissur–Chalakudy (illustrative)",
    "segment_ids": ["M-01", "M-02", "M-07", "M-11"],
    "distance_km": 140.0,
    "data_source": "simulated"
  }
]
```

---

## `GET /api/segments/?scenario=`

**Query params**
- `scenario` (optional): `"normal"` or `"flood"`. Defaults to server-wide scenario.

**Response** — array of **segment risk objects**.

### Segment risk object schema

```json
{
  "segment_id": "M-07",
  "name": "Chalakudy river crossing (illustrative)",
  "route_ids": ["main"],
  "geometry": [[10.3066, 76.3318], [10.3010, 76.3350]],
  "length_km": 4.2,
  "road_class": "highway",
  "risk_level": "high",
  "risk_score": 0.73,
  "reasons": [
    "92 mm rain in the last 24 h",
    "River level at 85% of danger mark",
    "Flooded 2 times in past events at this rain level (flood memory: trigger about 80 mm)"
  ],
  "factors": {"static": 0.80, "dynamic": 0.90, "crowd": 0.0},
  "confidence": "moderate",
  "data_source": "simulated",
  "data_timestamp": "2026-10-07T14:30:00+05:30",
  "flood_memory": {"trigger_mm": 80, "events": 2},
  "clears_in_hours": 5
}
```

**Field definitions**

| Field | Type | Description |
|---|---|---|
| `segment_id` | string | Unique identifier |
| `name` | string | Human-readable name (labelled illustrative where not verified) |
| `route_ids` | string[] | Routes this segment belongs to |
| `geometry` | [lat,lng][] | Ordered list of coordinates |
| `length_km` | float | Segment length |
| `road_class` | string | `highway \| state_road \| district_road \| urban` |
| `risk_level` | string | `low \| medium \| high \| closed` |
| `risk_score` | float | 0.0–1.0 composite score |
| `reasons` | string[] | Human-readable explanations, ordered by contribution |
| `factors` | object | Sub-scores: `static`, `dynamic`, `crowd` (each 0.0–1.0) |
| `confidence` | string | `high \| moderate \| low` |
| `data_source` | string | `live \| simulated \| historical` |
| `data_timestamp` | ISO string | Timestamp of the most recent dynamic input used |
| `flood_memory` | object \| null | `{trigger_mm, events}` if available |
| `clears_in_hours` | int \| null | Estimated hours until blockage clears (if known) |

---

## `POST /api/trip/options/`

### Request body

```json
{
  "origin": "Palakkad",
  "destination": "Kochi",
  "depart_at": "2026-10-08T06:00:00+05:30",
  "vehicle_type": "lcv",
  "cargo": {
    "type": "vegetables",
    "weight_kg": 5000,
    "shelf_life_hours": 8,
    "value_inr": 250000,
    "hours_already_elapsed": 0
  },
  "current_segment_id": null,
  "scenario": "flood"
}
```

**Required fields:** `origin`, `destination`, `depart_at`, `vehicle_type`, `cargo.type`,
`cargo.weight_kg`. `scenario` overrides the server-wide default if supplied.

### Response body

```json
{
  "generated_at": "2026-10-07T14:30:05+05:30",
  "scenario": "flood",
  "data_source": "simulated",
  "options": [
    {
      "option_id": "opt-1",
      "type": "reroute",
      "label": "Reroute via Kodungallur",
      "route_id": "alt1",
      "summary": "Avoids flooded Chalakudy and Aluva stretches.",
      "depart_at": "2026-10-08T06:00:00+05:30",
      "eta": {
        "earliest": "2026-10-08T11:20:00+05:30",
        "latest": "2026-10-08T12:30:00+05:30",
        "reason": "+55 min vs normal: detour via Kodungallur (+18 km), 2 medium-risk segments"
      },
      "distance_km": 142,
      "fuel_cost_inr": 2900,
      "max_risk_level": "medium",
      "cargo_window": {"ok": true, "remaining_hours_at_latest_eta": 1.5},
      "trade_offs": ["Longer by 18 km", "Two medium-risk segments; re-check before leaving"],
      "recommended": true
    }
  ],
  "excluded_routes": [
    {"route_id": "main", "reason": "Contains high-risk segments M-07 and M-11 (flood risk)"}
  ],
  "warnings": ["Using simulated data"],
  "message": null
}
```

**`option.type` values:** `"proceed" | "reroute" | "wait" | "divert_store"`

**No viable option:** `options` is empty and `message` explains (e.g. `"No safe option within the cargo window. Contact dispatcher; consider SOS"`).

### Option field definitions

| Field | Type | Description |
|---|---|---|
| `option_id` | string | e.g. `"opt-1"` |
| `type` | string | `proceed \| reroute \| wait \| divert_store` |
| `label` | string | Short human label |
| `route_id` | string \| null | Route used (null for wait/divert_store) |
| `summary` | string | One-sentence description |
| `depart_at` | ISO string | Recommended departure (may differ from request for wait option) |
| `eta.earliest` | ISO string | Optimistic arrival |
| `eta.latest` | ISO string | Pessimistic arrival (rounded to 5 min) |
| `eta.reason` | string | Largest contributors to deviation from normal |
| `distance_km` | float | Total route distance |
| `fuel_cost_inr` | float | Estimated fuel cost |
| `max_risk_level` | string | Highest risk level across all segments on this option |
| `cargo_window.ok` | bool | True if latest ETA + hours_already_elapsed ≤ shelf_life_hours |
| `cargo_window.remaining_hours_at_latest_eta` | float | Hours of shelf life remaining at latest ETA |
| `trade_offs` | string[] | Human-readable trade-off bullets |
| `recommended` | bool | Exactly one option has this set to true |

---

## `GET /api/service-points/`

**Query params**

| Param | Required | Description |
|---|---|---|
| `mode` | no | `normal` (default) or `emergency` (returns only hospital, police, fire, safe_halt) |
| `position_segment_id` | no | Current segment ID of the vehicle (default: start of main route) |
| `vehicle_type` | no | Default: `lcv` |
| `scenario` | no | Default: server-wide scenario |

**Response** — array of **service point objects**, sorted: reachable first, then by `reachable_minutes` ascending.

### Service point object schema

```json
{
  "id": "H-03",
  "name": "Taluk Hospital (illustrative)",
  "category": "hospital",
  "lat": 10.31,
  "lng": 76.33,
  "attach_segment_id": "M-06",
  "detour_minutes": 6,
  "reachable": true,
  "reachable_minutes": 38,
  "reason": null,
  "risk_level": "low",
  "last_verified": "2026-10-01",
  "data_source": "historical"
}
```

**`category` values:** `hospital | fuel | repair | towing | police | fire | safe_halt | cold_store | food | toilet`

In `mode=emergency` only `hospital`, `police`, `fire`, `safe_halt` are returned.  
If a point is behind a high/closed segment, `reachable=false` and `reason` names the blocking segment.

---

## `GET /api/rainfall/?lat=&lng=` *(owned by C)*

**Response**
```json
{
  "rain_24h_mm": 92.0,
  "forecast_3h_mm": 18.0,
  "data_source": "live",
  "data_timestamp": "2026-10-07T14:30:00+05:30"
}
```

---

## `POST /api/emergency/` *(owned by D)*

### Request body

```json
{
  "code": "03",
  "vehicle_id": 17,
  "seq": 4,
  "lat": 10.3066,
  "lng": 76.3318,
  "device_ts": "2026-10-07T14:30:00+05:30",
  "via": "lora",
  "station_id": 1
}
```

### Event object (in GET /api/emergency/ responses)

Adds server-side fields to the packet above:

| Field | Type | Description |
|---|---|---|
| `id` | int | Server-assigned event ID |
| `received_at` | ISO string | Server receipt timestamp |
| `status` | string | `"new" \| "acked"` |
| `acked_by` | string \| null | Station identifier that acknowledged |
| `acked_at` | ISO string \| null | Acknowledgement timestamp |

---

## `GET /api/emergency/?since=` *(owned by D)*

**Query params**
- `since` (optional): ISO timestamp; returns only events received after this time.

---

## `POST /api/emergency/<id>/ack/` *(owned by D)*

**Response**
```json
{"id": 4, "status": "acked", "acked_at": "2026-10-07T14:31:00+05:30"}
```

---

## Emergency Code Table

Defined in `data/emergency_codes.json`. Each entry has `code`, `en` (English text), `ml` (Malayalam text).

| Code | English |
|---|---|
| `01` | SOS — need immediate help |
| `02` | Landslide ahead |
| `03` | Flood ahead |
| `04` | Rescue needed |
| `05` | Need load transfer |
| `06` | Spare capacity offered |
| `07` | All clear |

*Malayalam text to be reviewed by a native speaker (E arranges).*

---

## Hard Filter Order (for `POST /api/trip/options/`)

Applied in this exact order; a route failing any filter is excluded entirely:

1. **Safety:** any segment with `risk_level` `high` or `closed` for the given vehicle → route excluded.
2. **Clearance (P1):** any segment where `clearance_m < vehicle.height_m` → route excluded.
3. **Cargo shelf life:** if `eta_latest_hours + hours_already_elapsed > shelf_life_hours` → route excluded.

Only surviving routes are ranked (by `eta.latest`, then fuel cost).
