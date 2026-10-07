# Member A — Backend Plan (A1 through A5)

## Top-Level Overview

**Goal:** Build the entire Django backend for SafeHaul Kerala, from the project skeleton to
all P0 API endpoints, so that the frontend (B), data layer (C) and hardware bridge (D) have
a stable, tested surface to integrate against.

**Scope:** Tasks A1–A5 as defined in docs/TEAM_BRIEF.md §Part 2 Member A.
- A1: Django project skeleton + config.py + data loader + scenario endpoints → merged to main first
- A2: Risk engine + /api/segments/ + /api/routes/
- A3: ETA calculator
- A4: Route options with hard filters + /api/trip/options/
- A5: Service-point reachability ranking + /api/service-points/

**Out of scope for this plan:** A6 stretch items (fleet, clearance filter, disruption certificate),
weather client (C), emergency app (D), frontend (B).

**Guiding constraints (from AGENTS.md and TEAM_BRIEF.md §1.7/1.8/1.11):**
- Every tunable constant lives ONLY in backend/safehaul/config.py.
- Safety and shelf life are hard filters, not weighted scores.
- Every risk object carries reasons, confidence, data_source, data_timestamp.
- Mock data first; stand-in fixture until data/ files arrive from C.
- No ML, no direct weather API calls, no payment code.
- Tests for every P0 function (risk boundaries, filters, ETA, flood memory, service-point reachability).

---

## Repository layout produced by this plan

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── safehaul/                     # Django project package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   ├── config.py                 # ALL tunable constants
│   └── data_loader.py            # reads data/*.json; falls back to fixture
├── risk/
│   ├── apps.py
│   ├── engine.py                 # score_segment()
│   └── views.py                  # /api/segments/, /api/routes/, /api/scenario/
├── routing/
│   ├── apps.py
│   ├── eta.py                    # compute_eta()
│   ├── options.py                # build_options() — hard filters + option types
│   └── views.py                  # /api/trip/options/
├── servicepoints/
│   ├── apps.py
│   ├── ranking.py                # rank_service_points()
│   └── views.py                  # /api/service-points/
├── weather/                      # STUB only — owned by C
│   ├── apps.py
│   └── client.py                 # get_rainfall(lat, lng, scenario) — returns mock
├── emergency/                    # STUB only — owned by D
│   └── apps.py
└── tests/
    ├── fixtures/
    │   ├── segments.json         # 5-segment stand-in (main route only)
    │   ├── routes.json           # 1 main route + 1 alternate
    │   ├── scenarios.json        # normal + flood
    │   ├── service_points.json   # 6 points (2 hospitals, fuel, repair, police, cold_store)
    │   ├── vehicles.json
    │   └── fleet.json
    ├── test_risk.py
    ├── test_eta.py
    ├── test_options.py
    └── test_servicepoints.py
docs/
└── CONTRACT.md                   # written by A; mirrors TEAM_BRIEF §1.10
```

---

## Sub-Tasks

---

### A1 — Project Skeleton

**Status:** [ ] pending

**Intent:**
Stand up a working Django + DRF project with the full app structure, all constants in one
place, a data loader with stand-in fixture fallback, and the two scenario endpoints.
This is the gate that unblocks B (frontend templates), C (data files landing in data/),
and D (empty emergency stub to extend). Merge to main as soon as it passes.

**Expected Outcomes:**
- `pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`
  starts with no errors.
- `GET /api/scenario/` returns `{"scenario": "normal"}`.
- `POST /api/scenario/` with `{"scenario": "flood"}` returns `{"scenario": "flood"}` and
  subsequent GETs reflect the change.
- `GET /api/routes/` returns the stand-in fixture routes (at least main + alt1).
- Django serves templates from frontend/templates/ and static from frontend/static/.
- docs/CONTRACT.md exists and matches TEAM_BRIEF §1.10 field names exactly.
- Branch merged to main via PR.

**Todo List:**
1. Create backend/requirements.txt (django, djangorestframework, python-dotenv, pytest-django).
2. Run `django-admin startproject safehaul backend/` (or write manage.py and safehaul/ package
   manually to keep the layout clean).
3. Create apps: risk, routing, servicepoints, weather (stub), emergency (stub) each with
   apps.py and an __init__.py.
4. Write backend/safehaul/settings.py:
   - SECRET_KEY from env; DEBUG from env (default True for dev).
   - INSTALLED_APPS includes all five apps plus rest_framework.
   - TEMPLATES dirs points to frontend/templates/.
   - STATICFILES_DIRS points to frontend/static/.
   - DATABASES: SQLite at backend/db.sqlite3.
5. Write backend/safehaul/config.py with every constant from TEAM_BRIEF §1.11:
   - Risk weights (WEIGHT_STATIC, WEIGHT_DYNAMIC, WEIGHT_CROWD and their sub-weights).
   - Risk level thresholds (LOW_THRESHOLD=0.30, MEDIUM_THRESHOLD=0.55, HIGH_THRESHOLD=0.80).
   - Base speeds by road_class (highway: 45, state_road: 30 km/h).
   - ETA multipliers (low: 1.0, medium: 0.75, high: 0.4).
   - Peak-hour windows and multiplier (1.2).
   - Rest rule (30 min after every 4.5 h driving).
   - ETA range factors (EARLIEST_FACTOR=0.92, LATEST_BASE=1.10, LATEST_PER_MEDIUM=0.05).
   - Fuel cost per km by vehicle type (LCV: 14 INR/km; others as placeholders).
   - Confidence thresholds (live+fresh -> high; simulated/stale -> moderate; missing -> low).
   - Depth-level max by vehicle type (mini_truck:1, lcv:2, heavy_truck:3, tipper:3).
   - Spoilage value heuristic constant (for divert_store estimate; labelled mock).
6. Write backend/safehaul/data_loader.py:
   - `load_data()`: tries to read each file from data/; if absent falls back to
     backend/tests/fixtures/ equivalent. Caches result in a module-level dict.
   - `get_segments()`, `get_routes()`, `get_scenarios()`, `get_service_points()`,
     `get_vehicles()`, `get_fleet()`, `get_emergency_codes()` helpers.
   - Call load_data() in AppConfig.ready() of the safehaul app (or on first call).
7. Create backend/tests/fixtures/ with minimal stand-in JSON files:
   - segments.json: 5 segments (3 on main, 2 on alt1) with all static fields from §1.12.
   - routes.json: main (3 segments) and alt1 (2 segments + 1 shared).
   - scenarios.json: normal (all low) and flood (segment S-02 → high, S-03 → medium,
     clears_in_hours: 5 on S-02).
   - service_points.json: 6 points (2 hospitals, 1 fuel, 1 repair, 1 police, 1 cold_store).
   - vehicles.json: 4 vehicle types from §1.11.
   - fleet.json: 3 simulated vehicles.
8. Write risk/views.py: GET /api/scenario/ and POST /api/scenario/ (store state in
   Django cache or a module-level variable; default "normal").
   Also wire GET /api/routes/ here (simple pass-through from data loader).
9. Wire backend/safehaul/urls.py to include risk.urls, routing.urls, servicepoints.urls.
10. Write backend/.env.example with SECRET_KEY, DEBUG, DATA_DIR placeholders.
11. Write docs/CONTRACT.md reproducing every endpoint, field name and example from §1.10.
12. Smoke-test manually; commit; open PR to main with message "A: project skeleton".

**Relevant Context:**
- TEAM_BRIEF §1.8 (tech decisions), §1.9 (repo layout), §1.10 (contract), §1.11 (constants).
- frontend/ tree already exists (B scaffolded templates/ and static/).
- data/ is empty; stand-in fixture must cover every loader call used by A2–A5.

---

### A2 — Risk Engine and Segment/Route Endpoints

**Status:** [ ] pending

**Intent:**
Implement the risk scoring formula from §1.11 exactly, including flood memory, confidence
rules, reason generation, and vehicle overrides. Expose it through /api/segments/ and make
/api/routes/ return route metadata. This is the first feature B can visualise on the map.

**Expected Outcomes:**
- `GET /api/segments/?scenario=flood` returns all segments with risk_score, risk_level,
  reasons (at least 2 per high-risk segment), confidence, data_source, data_timestamp.
- Switching scenario from normal to flood changes at least 2 fixture segments from low to
  high/closed and adds readable reasons.
- `official_closure=true` forces risk_level to "closed" regardless of score.
- A segment with reported_depth_level >= vehicle max depth level is "closed" for that vehicle.
- Flood memory: if rain_24h_mm >= trigger_mm, history factor becomes 1.0 and a reason is added.
- Confidence is "moderate" (not "high") for any simulated scenario data.
- All test cases in test_risk.py pass.

**Todo List:**
1. Write risk/engine.py with function `score_segment(segment, dynamic, vehicle, now)`:
   a. Compute static sub-score: elev, river_prox, hist, structure factors; apply weights.
   b. Check flood memory: if flood_history data exists and rain >= trigger_mm, override
      hist factor to 1.0 and record a flood-memory reason.
   c. Compute dynamic sub-score: rain, river_level, forecast; apply weights.
   d. Compute crowd sub-score.
   e. Compute overall risk_score = 0.35*static + 0.50*dynamic + 0.15*crowd.
   f. Apply level thresholds from config.py.
   g. Apply overrides in order: official_closure -> closed; depth_level >= vehicle max -> closed.
   h. Build reasons list: one human-readable string per factor that contributes meaningfully
      (threshold: contributing factor > 0.1 of its sub-score weight); order by contribution desc.
   i. Determine confidence: all live + under 1h -> high; any simulated or >3h old -> moderate;
      key input missing -> low.
   j. Return dict matching the segment risk object schema from §1.10.
2. Write risk/views.py: SegmentsView (GET /api/segments/?scenario=) that:
   - Resolves scenario (query param overrides server state).
   - Loads segments and their dynamic inputs for the scenario.
   - Calls score_segment() for each segment (pass vehicle=None for default LCV).
   - Returns list of scored segment objects.
3. Extend risk/views.py: RoutesView (GET /api/routes/) returns routes from data loader
   (id, name, distance_km, segment_ids).
4. Write backend/tests/test_risk.py covering:
   - low/medium/high/closed score boundaries (exact threshold values).
   - official_closure override.
   - depth_level override for mini_truck vs heavy_truck.
   - Flood memory trigger (rain >= trigger -> hist=1.0, reason present).
   - Flood memory NOT triggered (rain < trigger -> normal hist).
   - Confidence is "moderate" for simulated data, "low" for missing dynamic key.
   - Reasons list is non-empty, ordered by contribution (highest first).
   - Reasons list uses plain English (no raw numbers without context).
5. Add flood_history data to the stand-in fixture (at least one segment with
   flood_memory: {trigger_mm: 80, events: 2}).

**Relevant Context:**
- All formula weights and thresholds come from config.py (never hard-coded here).
- data_loader.get_segments(), get_scenarios() provide inputs.
- Confidence rule: simulated scenario -> at most "moderate" (TEAM_BRIEF §1.11).
- Reasons must reference real values (e.g. "92 mm rain in last 24 h") not just labels.

---

### A3 — ETA Calculator

**Status:** [ ] pending

**Intent:**
Implement the ETA formula from §1.11 producing earliest/latest range and a human-readable
reason string. This is consumed by A4 (options) and displayed directly by B.

**Expected Outcomes:**
- `compute_eta(route, scored_segments, vehicle, depart_at)` returns
  `{expected_seconds, earliest: ISO string, latest: ISO string, reason: str}`.
- earliest = expected * 0.92; latest = expected * (1.10 + 0.05 * n_medium_segments),
  rounded to the nearest 5 minutes.
- Peak-hour multiplier (1.2) applied when any driving falls in 08:00–10:00 or 17:00–19:00.
- Rest break of 30 min added after every 4.5 h of accumulated driving.
- Reason string names the largest contributors to the deviation vs. the normal baseline
  (detour km, medium-risk segments, rest breaks, wait time).
- All test cases in test_eta.py pass.

**Todo List:**
1. Write routing/eta.py with `compute_eta(route, scored_segments, vehicle, depart_at, scenario="normal")`:
   a. For each segment in route, compute segment_time = length_km / base_speed(road_class)
      from config.py.
   b. Apply risk multiplier from config.py based on that segment's risk_level.
   c. Apply peak-hour multiplier if any part of the segment's time window falls in peak hours.
   d. Accumulate driving time; insert 30-min rest whenever 4.5 h of driving is reached.
   e. Compute expected total seconds.
   f. Compute earliest = expected * EARLIEST_FACTOR.
   g. Compute latest = expected * (LATEST_BASE + LATEST_PER_MEDIUM * n_medium_segments),
      rounded up to nearest 5 min.
   h. Build reason string: list the top contributors vs the normal-scenario same route,
      ordered by minutes added (detour extra km, each medium-risk segment, rest breaks, waits).
   i. Return the dict.
2. Write backend/tests/test_eta.py covering:
   - earliest < expected < latest always holds.
   - Adding a medium-risk segment widens latest correctly.
   - A route exceeding 4.5 h driving gets a rest break in total time.
   - Peak-hour departure increases expected time.
   - Reason string mentions the biggest contributor (e.g. "detour via Kodungallur +18 km").
   - Round-to-5-min rule applied on latest.

**Relevant Context:**
- All speed constants and multipliers from config.py.
- scored_segments passed in from the risk engine (A2), not re-scored here.
- depart_at is an ISO 8601 string with timezone (from the trip request).

---

### A4 — Route Options with Hard Filters

**Status:** [ ] pending

**Intent:**
Implement the core P0 feature: evaluate every candidate route, apply hard filters in order,
generate up to 3 labelled options (proceed, reroute, wait, divert_store), mark one
recommended, list excluded routes with reasons. Expose as POST /api/trip/options/.
The demo scenario in §1.6 (Palakkad→Kochi, vegetables, 5000 kg, 8 h, LCV, flood) must work
end-to-end through this endpoint.

**Expected Outcomes:**
- Normal scenario: options contains "proceed" on main route with ETA and cargo_window.ok=true.
- Flood scenario: main route excluded (reason cites high-risk segment IDs); options contains
  reroute and/or wait and/or divert_store.
- A route whose latest ETA exceeds shelf_life_hours is excluded with a shelf-life reason.
- wait option computed only when clears_in_hours exists; excluded if delayed ETA still exceeds
  cargo window.
- divert_store option uses nearest reachable cold_store from service points; includes
  estimated_value_saved_inr labelled as a mock estimate.
- Exactly one option has recommended=true (safest viable, then fastest).
- If no viable option exists, options=[] and message explains why.
- excluded_routes lists every filtered route with the first failing filter as reason.
- All test cases in test_options.py pass.

**Todo List:**
1. Write routing/options.py with `build_options(trip_request, scored_routes, vehicle, service_points, now)`:
   a. HARD FILTER 1 — Safety: exclude any route containing a segment with risk_level
      "high" or "closed" for the given vehicle. Record reason citing the failing segment IDs.
   b. HARD FILTER 2 — Clearance (P1 placeholder): if any segment clearance_m <
      vehicle.height_m, exclude. Log a TODO comment; skip if clearance_m is absent.
   c. HARD FILTER 3 — Shelf life: call compute_eta(); if
      eta_latest_hours + hours_already_elapsed > shelf_life_hours, exclude.
      Record reason citing ETA and remaining window.
   d. From surviving routes, build option objects:
      - proceed: main route (if it survived).
      - reroute: each surviving alternate (max 2).
      - wait: if any excluded route has clears_in_hours on its blocking segment(s), compute
        delayed departure; re-run filters; if now viable and cargo window allows, add wait option.
      - divert_store: find nearest reachable cold_store (rank_service_points with cold_store
        filter); build option with estimated_value_saved_inr from config heuristic.
   e. Cap at 3 options. Mark recommended=true: prefer safest (lowest max_risk_level),
      then fastest (earliest eta.latest). Only one recommended flag.
   f. If options is empty, set message = clear explanation.
   g. Stamp response with generated_at, scenario, data_source.
2. Write routing/views.py: TripOptionsView (POST /api/trip/options/) that:
   - Deserialises the request body (validate required fields; 400 on bad input).
   - Resolves vehicle from vehicles.json by vehicle_type.
   - Calls score_segment() on all segments for the resolved scenario.
   - Calls build_options().
   - Returns the response object from §1.10.
3. Write backend/tests/test_options.py covering:
   - Normal scenario -> proceed option present.
   - Flood scenario -> main excluded, reason cites high-risk segments.
   - Shelf-life too short -> safe alt also excluded; message explains.
   - mini_truck depth_level override excludes a route that LCV could take.
   - wait option present when clears_in_hours exists and cargo window allows.
   - wait option absent when delayed ETA exceeds cargo window.
   - divert_store option present and includes estimated_value_saved_inr.
   - No viable option -> options=[] with non-empty message.
   - Exactly one recommended=true across all options.
4. Extend stand-in fixture: add cold_store to service_points.json with attach_segment_id;
   ensure at least one main-route segment in flood fixture has clears_in_hours.

**Relevant Context:**
- Hard filters applied in exactly the order stated (safety first, then clearance, then shelf life).
- build_options depends on A2 (score_segment) and A3 (compute_eta); implement after both pass.
- Trip request and response shapes are locked in CONTRACT.md and §1.10; do not change field names.
- estimated_value_saved_inr must be labelled a mock estimate in trade_offs.

---

### A5 — Service-Point Reachability Ranking

**Status:** [ ] pending

**Intent:**
Implement the reachability check and ranking for /api/service-points/ so that the "nearest
hospital flips" demo moment works: in the flood scenario, the closest hospital is behind a
high-risk segment and becomes reachable=false, while the farther one ranks first.

**Expected Outcomes:**
- GET /api/service-points/?scenario=flood returns all points with reachable correctly set.
- A point whose attach_segment is downstream of a high/closed segment is reachable=false
  with reason naming the blocking segment.
- reachable_minutes = along-route ETA to attach segment + detour_minutes.
- Results sorted: reachable=true first, then by reachable_minutes ascending.
- mode=emergency returns only hospital, police, fire, safe_halt categories.
- position_segment_id param moves the "current position" forward on the route.
- All test cases in test_servicepoints.py pass.

**Todo List:**
1. Write servicepoints/ranking.py with
   `rank_service_points(points, route, scored_segments, vehicle, position_segment_id, mode, scenario)`:
   a. Determine the sub-list of segments between position_segment_id and each point's
      attach_segment_id (in route order).
   b. If any segment in that sub-list has risk_level "high" or "closed", mark reachable=false
      and set reason to "blocked by segment <id> (<risk_level>)".
   c. Compute reachable_minutes: sum of segment ETAs (base speed, no risk multiplier for
      service-point ranking — conservative: use actual risk-adjusted ETA) + detour_minutes.
   d. If mode=emergency, filter to only hospital, police, fire, safe_halt.
   e. Sort: reachable=True first, then reachable_minutes ascending.
   f. Return list of service point objects matching §1.10 schema.
2. Write servicepoints/views.py: ServicePointsView (GET /api/service-points/):
   - Accept query params: mode, position_segment_id, vehicle_type, scenario.
   - Resolve scenario, vehicle, route (default: first route in routes.json that covers
     position_segment_id, or the main route).
   - Call rank_service_points().
   - Return list.
3. Write backend/tests/test_servicepoints.py covering:
   - Hospital behind high-risk segment -> reachable=false, reason present.
   - Hospital NOT behind high-risk segment -> reachable=true, correct reachable_minutes.
   - Nearest reachable hospital ranks before an unreachable closer one.
   - mode=emergency excludes fuel/repair/food/toilet categories.
   - position_segment_id shifts the window (points before the position are not returned or
     are marked out-of-path).
4. Ensure stand-in fixture has 2 hospitals: one before the flood segment (reachable in flood),
   one after it (unreachable in flood) — so the ranking flip is demonstrable.

**Relevant Context:**
- Depends on A2 (scored segments) and A3 (ETA per segment for reachable_minutes).
- attach_segment_id and detour_minutes come from service_points fixture.
- The "nearest reachable hospital flips" moment is a P0 demo requirement (§1.6 step 5).

---

## Implementation Order and Dependencies

```
A1 (skeleton + config + data loader + scenario endpoints)
  └── A2 (risk engine uses config + data loader)
        └── A3 (ETA uses config + scored segments from A2)
              └── A4 (options uses A2 + A3; needs cold_store in fixture)
                    └── A5 (service points uses A2 + A3; needs 2-hospital fixture)
```

A1 must be merged to main before anyone else can branch. A2–A5 can be committed
incrementally on a/backend as each sub-task passes its tests.

---

## Fixture Design (stand-in until C delivers data/)

The stand-in fixture in backend/tests/fixtures/ must cover every code path used by A2–A5.
Minimum viable contents:

| File | Minimum content |
|---|---|
| segments.json | S-01 to S-05; S-03 is high in flood scenario; S-01 and S-04 are on alt1; S-03 has flood_memory trigger_mm=80 |
| routes.json | main (S-01, S-02, S-03), alt1 (S-01, S-04, S-05), distance_km for each |
| scenarios.json | normal: all low; flood: S-03 rain_24h_mm=95, river_level_pct=88, S-03 clears_in_hours=5, S-02 medium |
| service_points.json | H-01 (hospital, attach S-02, before flood segment), H-02 (hospital, attach S-04, on alt1), F-01 (fuel), C-01 (cold_store, attach S-05) |
| vehicles.json | mini_truck, lcv, heavy_truck, tipper with max_depth_level and height_m |
| fleet.json | 3 vehicles with segment_id, vehicle_type, cargo, shelf_life_hours |

All fixture entries carry data_source: "simulated".

---

## Test Coverage Targets

| Module | Tests required (P0) |
|---|---|
| risk/engine.py | score boundaries, overrides, flood memory, confidence, reasons |
| routing/eta.py | range ordering, medium widening, rest rule, peak-hour, reason content |
| routing/options.py | all filter paths, all option types, recommended flag, no-viable-option |
| servicepoints/ranking.py | reachability flip, mode filter, position param, sort order |

---

## Notes for the Implementer

- When data/ files from C exist and differ from the fixture, the data loader switches
  automatically (it tries data/ first). No code change needed.
- The weather stub (weather/client.py) returns mock rainfall for now. A's code calls
  `from weather.client import get_rainfall` but does not own that module.
- The emergency stub (emergency/apps.py) is an empty Django app. D fills it in later.
- All datetime handling uses Python's `datetime` with timezone-aware objects (pytz or
  Python 3.9+ zoneinfo). Timezone for Kerala: Asia/Kolkata (UTC+5:30).
- Never log or print secrets. Use Python's logging module at INFO level.
