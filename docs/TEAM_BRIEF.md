# SafeHaul Kerala: Team Brief for Builders

**Read this first.** You are an AI coding agent (IBM Bob) working inside a team of five (four builders A-D plus a human coordinator E). You have no prior knowledge of this project. This document is your complete briefing.

**How to use it**
1. Read **Part 1 (shared background)** fully. It is the same for everyone.
2. Read **your own section in Part 2** (A, B, C or D) and skim the others so you know what your teammates produce and consume.
3. Work only in the files you own (see ownership table). If you need a change in someone else's area, write it in `docs/QUESTIONS.md` and continue with a mock or stub.
4. Keep `docs/STATUS.md` updated so other agents can see what is done.

---

# PART 1: SHARED BACKGROUND

## 1.1 The event and the challenge

- **Event:** IBM x Kerala Government Hackathon 2026.
- **Challenge 5: Flood-Aware Logistics Planner for Kerala.**
- **Official brief:** Kerala's monsoon causes flooding, waterlogging, landslides and road closures. Small transport operators and logistics companies often learn about disruptions only after vehicles have already started the journey. Build a route-planning and logistics-visibility tool that helps operators identify potential disruptions and find alternative routes.
- **Official target users:** logistics companies, lorry operators, FMCG distributors, agricultural traders.
- **Official suggested features:** route visualisation, weather alerts, flood-risk mapping, alternate route suggestions, delivery ETA estimation.
- **Official example scenario:** a truck carrying vegetables from Palakkad to Kochi finds part of the route flooded. The system should recommend alternative transportation options.
- **Official impact goal:** improve delivery reliability and reduce transportation losses.

Our product name (placeholder): **SafeHaul Kerala**.
Our tagline: *"We don't just reroute the truck. We protect the cargo, the driver and the community."*

## 1.2 The real problem (why this matters)

The roads are not the main problem. **Late, fragmented information** is.

- Operators learn about a blockage from a phone call, a WhatsApp forward, or by reaching the blocked point. By then the truck is committed; turning back wastes fuel and driver hours.
- For perishable cargo (vegetables, fish, dairy), delay directly means spoilage and financial loss.
- Generic navigation apps (e.g. Google Maps) show traffic, **not flood risk**, and they ignore truck constraints (height, weight, wading ability) and cargo constraints (shelf life).
- When a truck breaks down or is stranded there is no quick way to move its cargo onto another vehicle.
- In flood or landslide zones mobile networks can fail, so drivers cannot call for help.
- Existing risk scores, where they exist, are unexplained, so drivers do not trust them.

We aim to move operators from **reactive** ("I'm stuck") to **proactive** ("this stretch will likely flood in 3 hours; leave now by this alternative, or wait, or divert to a cold store").

## 1.3 Users

| User | Need |
|---|---|
| Lorry operators / owner-drivers | Know route risk before and during the trip; have a safe alternative; call for help even offline |
| Logistics companies / fleet dispatchers | See many vehicles at once; decide which loads go, wait or divert |
| FMCG distributors | Reliable delivery times, updated ETAs |
| Agricultural traders / farmer collectives | Protect perishables; reduce spoilage |
| Receivers (markets, retailers) | Accurate, automatically updated arrival times |
| Police / fire / rescue stations | Receive structured emergency signals |

## 1.4 Solution summary: four pillars

**Pillar 1: Predict.** Segment-level flood-risk scoring (static factors like elevation, river proximity, flood history, underpasses + dynamic factors like rainfall, river level, forecasts, official closures + crowd reports). **Every score is explainable** ("High: 92 mm rain in 24 h, river at 85% of danger level, this underpass flooded in 2018"), with a confidence level and data timestamp. We **ingest** weather data (Open-Meteo / IMD) and translate rainfall into road-segment consequences. **We do NOT build our own weather model.** "Segment flood memory" records the rainfall level at which each segment has flooded before.

**Pillar 2: Protect.** Routing uses **hard filters first** (safety, then cargo shelf life, then vehicle limits). Only after that do we optimise cost and time. The driver is shown **2-3 labelled options with trade-offs** (e.g. Reroute / Wait / Divert-and-store). **Nothing is decided silently.** ETA is shown as a **range with a reason** and auto-updates when conditions change.

**Pillar 3: Stay connected.** Offline sliding-window corridor map (download ahead, keep a "retreat buffer" behind because turning back is the most common flood response). Emergency signalling ladder with graceful degradation: app data, then SMS, then LoRa radio mesh, then Morse via torch/horn as a last resort. Compact emergency code table. A flood-aware service map (hospitals, fuel, repair, police, safe halt points, cold stores) that ranks places by **safe reachable time**, not straight-line distance.

**Pillar 4: Help each other.** "Load Relay" (a stranded truck hands its cargo to a nearby truck with spare capacity) and "Spare Capacity Pool" (warehouses post stock for trucks with space). **Communication and matching only; no payment handling.** Also: trucks as passive sensors, a truck-relative water-depth scale, and a voice-first Malayalam WhatsApp interface (watsonx.ai). **These are mostly designed and mocked, not fully built, for the hackathon.**

## 1.5 Scope: what we build, simulate, mock or skip

| Category | Items |
|---|---|
| **P0: Build, must work flawlessly** | Route map; segment risk score with explanation, confidence and timestamp; flood-simulation toggle; risk-aware route options (hard filters); ETA range with reason; cargo shelf-life check; service points ranked by safe reachable time (hospital, fuel, repair, police, safe halt) |
| **P1: Build, demo highlights** | **LoRa SOS hardware demo** (the "wow factor"); station dashboard receiving SOS with the internet off; offline sliding-window simulation; emergency-mode map; English/Malayalam UI toggle; simple dispatcher fleet view |
| **P2: Design / partially build / mock and clearly label** | Safe-harbor cold-store comparison (mock availability); Load Relay and Spare Capacity Pool (UI mock); segment flood memory (simple); WhatsApp/Malayalam voice (mock flow); trucks-as-sensors and depth reporting (simple UI); disruption certificate; 2018 flood replay |
| **Do NOT build** | Our own weather model; payment processing; real police/rescue integration; anything we cannot demo reliably |

**Rule:** finish P0 end to end before touching P1/P2. A polished core beats many half-working features.

## 1.6 The demo scenario (everything must serve this)

> A truck carries **5,000 kg of vegetables** from **Palakkad to Kochi**. Cargo shelf-life window: **8 hours**. Vehicle: **LCV**. Departure 6:00 AM.

1. **Normal scenario:** main route (via Thrissur, Chalakudy, Angamaly, Aluva) is mostly green. Option shown: "Proceed on main route", ETA e.g. 4h 30m to 5h 05m, cargo window OK.
2. **Presenter clicks "Simulate flood".** Rainfall and river levels jump. Segments near Chalakudy and Aluva turn red with explanations. The main route is **excluded** by the safety filter.
3. **Options appear:** (a) Reroute via an alternate inland/state-road route with a longer ETA range; (b) Wait N hours (forecast clears) if still inside the cargo window; (c) Divert-and-store at a cold store/ice plant (mock availability).
4. **ETA updates automatically** with a reason ("+55 min: detour via Kodungallur, 2 medium-risk segments"), and a "receiver notified" message is shown.
5. **Service map:** the "nearest hospital" jumps from the closest one to a farther one that is actually reachable.
6. **SOS (hardware):** with the internet switched off, pressing the button on a LoRa device in the "truck" makes the code appear on the "police station" dashboard, which sends back an acknowledgement.
7. **Stretch screens (mock):** Load Relay match, WhatsApp Malayalam voice reply, disruption certificate.

All place names and numbers for the corridor are **illustrative and must be verified** against real map data before the demo (see Member C).

## 1.7 Non-negotiable design principles

1. **Safety is a hard filter, not a weighted score.** Unsafe routes are excluded, not just penalised.
2. **Shelf life is a second hard filter.** A safe route that spoils the cargo is rejected.
3. **Never decide silently.** Show 2-3 labelled options with trade-offs.
4. **Explainability.** Every risk score carries reasons, a confidence level and a data timestamp.
5. **Honesty about data.** Every data item carries `data_source`: `"live"`, `"simulated"` or `"historical"`. The UI shows a visible "SIMULATED DATA" label when simulated data is in use. Stale data always shows its age.
6. **Conservative warnings.** A false "safe" is worse than a false "caution". When unsure, warn.
7. **Ranges, not false precision.** ETA is a range with a reason.
8. **Mock first, live later.** Everything must work from local mock data. Live APIs are an enhancement with automatic fallback to mock. The demo must never depend on a live feed.
9. **Mobile-first, low-bandwidth, Malayalam-friendly.** Large touch targets, readable in a moving vehicle, small payloads.
10. **No payments.** We are a communication/matching medium only. Do not add payment code.

## 1.8 Technical decisions (and deliberate deviations from the PRD)

| Topic | Decision | Why |
|---|---|---|
| Backend | Python, **Django + Django REST Framework** | Team decision, matches PRD |
| Database | **SQLite** for the MVP (geometry stored as JSON lists of `[lat, lng]`). PostGIS only if time remains | Removes setup risk; PRD mentions PostGIS as the long-term option |
| Frontend | **Served by Django** (templates + static JS + CSS), **Leaflet** map, no Node build step. Leaflet and fonts bundled locally, not CDN-only | One deployable unit; works offline for the PWA |
| Routing | **Precomputed candidate routes** stored as ordered lists of segment IDs in `data/`. The backend evaluates risk, filters and ETA on these. Live OSRM is an optional stretch | A reliable demo; avoids depending on a routing server |
| Weather | **Open-Meteo** (no key needed) for rainfall, behind a function with automatic fallback to mock | Verify parameters in its docs |
| Risk engine | Rule-based, weighted, explainable (formulas in 1.11). No ML for the MVP | We have too little real data to train honestly |
| Hardware | **ESP32 + LoRa (SX127x) + GPS** boards; a gateway board on USB serial feeding a Python bridge | Two boards enable an offline demo |
| Offline server | The Django server runs on a local laptop, so "internet off" still works over localhost/LAN | The hardware demo needs this |
| watsonx.ai | Optional, for parsing messy text and generating Malayalam advisories. Verify access first; otherwise mock | Not P0 |
| Tests | `pytest` or Django `TestCase` for the risk engine, filters and ETA | Judges will probe this logic |

## 1.9 Repository layout and ownership

```
safehaul/
├── AGENTS.md                 # E (from Appendix A); every agent reads it
├── README.md                 # E
├── docs/
│   ├── PRD.md                # E
│   ├── TEAM_BRIEF.md         # this file
│   ├── CONTRACT.md           # A (API contract; mirrors 1.10)
│   ├── STATUS.md             # everyone (own section only)
│   ├── QUESTIONS.md          # everyone (append only); E answers
│   └── DEMO_SCRIPT.md        # E
├── data/                     # C owns all files here
│   ├── segments.json
│   ├── routes.json
│   ├── scenarios.json
│   ├── service_points.json
│   ├── flood_history.json
│   ├── vehicles.json
│   ├── fleet.json
│   └── emergency_codes.json
├── backend/                  # Django project
│   ├── manage.py
│   ├── safehaul/             # settings, urls, config.py  (A)
│   ├── risk/                 # A: scoring, explanations
│   ├── routing/              # A: options, filters, ETA
│   ├── servicepoints/        # A: reachability ranking
│   ├── weather/              # C: Open-Meteo client + fallback
│   ├── emergency/            # D: models, API, station dashboard
│   └── tests/                # A (core), D (emergency), C (data/weather)
├── frontend/                 # B owns (templates + static)
│   ├── templates/
│   └── static/ (js, css, i18n, sw.js, manifest.json, vendor/leaflet)
└── hardware/                 # D owns
    ├── firmware/
    └── gateway/              # Python serial-to-API bridge
```

**Ownership rule:** each agent edits only its own files. A creates the Django skeleton (including empty stub apps for `weather` and `emergency`) in the first phase and merges it to `main` so everyone can branch from it.

## 1.10 Shared data and API contract

A owns `docs/CONTRACT.md`; it must match this section. Do not change field names without writing to `docs/QUESTIONS.md` and getting E's approval. Additive fields are allowed.

### Common conventions
- Timestamps: ISO 8601 with timezone, e.g. `2026-10-07T14:30:00+05:30`.
- Coordinates: `[lat, lng]`.
- `scenario`: `"normal"` or `"flood"`. Every endpoint accepts `?scenario=`; otherwise it uses the server-wide default set via `/api/scenario/`.
- `risk_level`: `"low" | "medium" | "high" | "closed"`.
- `confidence`: `"high" | "moderate" | "low"`.
- `data_source`: `"live" | "simulated" | "historical"`.

### Endpoints

| Method + path | Purpose | Built by |
|---|---|---|
| `GET /api/scenario/` | Current server scenario | A |
| `POST /api/scenario/` body `{"scenario":"flood"}` | Switch scenario (the demo toggle) | A |
| `GET /api/routes/` | Candidate routes (id, name, distance, ordered segment IDs) | A |
| `GET /api/segments/?scenario=` | All segments with computed risk | A |
| `POST /api/trip/options/` | Trip form in; 2-3 labelled options out | A |
| `GET /api/service-points/?mode=normal\|emergency&position_segment_id=&vehicle_type=&scenario=` | Service points ranked by safe reachable time | A |
| `GET /api/fleet/?scenario=` | Simulated fleet with risk, ETA, go/hold/divert (stretch) | A |
| `GET /api/rainfall/?lat=&lng=` | Rainfall (24h past, 3h forecast) with source | C (in `weather/`) |
| `POST /api/emergency/` | Submit an emergency packet | D |
| `GET /api/emergency/?since=` | List events (the station dashboard polls this) | D |
| `POST /api/emergency/<id>/ack/` | Station acknowledges | D |

### Segment risk object (`/api/segments/`)
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

### Trip options request and response (`POST /api/trip/options/`)
Request:
```json
{
  "origin": "Palakkad",
  "destination": "Kochi",
  "depart_at": "2026-10-08T06:00:00+05:30",
  "vehicle_type": "lcv",
  "cargo": {"type": "vegetables", "weight_kg": 5000, "shelf_life_hours": 8, "value_inr": 250000, "hours_already_elapsed": 0},
  "current_segment_id": null,
  "scenario": "flood"
}
```
Response:
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
      "eta": {"earliest": "2026-10-08T11:20:00+05:30", "latest": "2026-10-08T12:30:00+05:30",
              "reason": "+55 min vs normal: detour via Kodungallur (+18 km), 2 medium-risk segments"},
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
`option.type` is one of `"proceed" | "reroute" | "wait" | "divert_store"`. If no option is viable, `options` is empty and `message` explains (e.g. "No safe option within the cargo window. Contact dispatcher; consider SOS").

### Service point object (`/api/service-points/`)
```json
{
  "id": "H-03", "name": "Taluk Hospital (illustrative)", "category": "hospital",
  "lat": 10.31, "lng": 76.33,
  "attach_segment_id": "M-06", "detour_minutes": 6,
  "reachable": true, "reachable_minutes": 38,
  "reason": null,
  "risk_level": "low", "last_verified": "2026-10-01", "data_source": "historical"
}
```
`category` is one of: `hospital, fuel, repair, towing, police, fire, safe_halt, cold_store, food, toilet`. In `mode=emergency` only `hospital, police, fire, safe_halt` are returned. If a point is behind a high/closed segment, `reachable=false` and `reason` explains.

### Emergency packet (API form, `POST /api/emergency/`)
```json
{"code": "03", "vehicle_id": 17, "seq": 4, "lat": 10.3066, "lng": 76.3318, "device_ts": "2026-10-07T14:30:00+05:30", "via": "lora", "station_id": 1}
```
Event object adds `id`, `received_at`, `status` (`"new" | "acked"`), `acked_by`, `acked_at`.

### Emergency code table (`data/emergency_codes.json`)
`01` SOS, `02` landslide ahead, `03` flood ahead, `04` rescue needed, `05` need load transfer, `06` spare capacity offered, `07` all clear. Each entry has `en` and `ml` (Malayalam text to be filled and reviewed by a native speaker, E arranges).

## 1.11 Shared rules for risk, routing and ETA

These defaults live in **one file**: `backend/safehaul/config.py` (owned by A). Everyone else reads them from the spec below; never hard-code them elsewhere.

### Segment inputs (from `data/segments.json` and `data/scenarios.json`)
Static: `elevation_m`, `river_distance_m`, `historical_flood_count`, `hazard_type` (`none | underpass | low_bridge | landslide_prone`), `clearance_m` (optional, for underpasses).
Dynamic (per scenario): `rain_24h_mm`, `forecast_3h_mm`, `river_level_pct`, `official_closure` (bool), `crowd_reports` (count of recent reports), `reported_depth_level` (0-4), `clears_in_hours` (optional).

### Risk score (all weights are config)
```
elev      = clamp(1 - elevation_m / 60)
river_prox= clamp(1 - river_distance_m / 2000)
hist      = clamp(historical_flood_count / 3)      # set to 1.0 if flood memory is triggered
structure = 1.0 if hazard_type != "none" else 0.0
static    = 0.30*elev + 0.25*river_prox + 0.25*hist + 0.20*structure

dynamic   = 0.40*clamp(rain_24h_mm/120) + 0.35*clamp(river_level_pct/100) + 0.25*clamp(forecast_3h_mm/40)
crowd     = clamp(crowd_reports / 3)

risk_score = 0.35*static + 0.50*dynamic + 0.15*crowd
```
Levels: `< 0.30` low; `0.30-0.55` medium; `0.55-0.80` high; `>= 0.80` closed.
**Overrides:** `official_closure = true` forces `closed`. `reported_depth_level >= vehicle max depth level` forces `closed` for that vehicle.

### Reasons
Generate one human-readable reason for each factor that contributes meaningfully (e.g. rain above 50 mm, river above 60%, historical floods, hazard type, closure, reports). Order reasons by contribution. If flood memory is triggered, add a reason referencing its trigger.

### Confidence
`high` only if all dynamic inputs are live and under 1 h old; `moderate` if any input is simulated or older than 3 h; `low` if a key input is missing. Simulated scenario data is therefore at most `moderate`.

### Vehicles (`data/vehicles.json`, values are assumptions; E verifies)
| vehicle_type | max_depth_level | height_m | notes |
|---|---|---|---|
| mini_truck | 1 | 2.2 | lowest ground clearance |
| lcv | 2 | 2.8 | demo default |
| heavy_truck | 3 | 3.8 | |
| tipper | 3 | 3.5 | higher chassis |

Depth scale: `0` dry, `1` below tyre mid-height, `2` tyre mid-height to wheel hub, `3` wheel hub to floorboard, `4` above floorboard.

### Hard filters (applied in this order, each excludes a whole route)
1. **Safety:** exclude any route containing a segment with `high` or `closed` risk for the selected vehicle.
2. **Clearance:** exclude a route if any segment `clearance_m < vehicle height_m` (P1).
3. **Cargo shelf life:** exclude if `eta_latest_hours + hours_already_elapsed > shelf_life_hours`.
Only the remaining routes are ranked (by `eta.latest`, then fuel cost). `medium` segments are allowed but must appear in the trade-offs.

### Options generated
- `proceed`: if the main route survives the filters.
- `reroute`: each surviving alternate route (max 2 shown).
- `wait`: if blocking segments have `clears_in_hours`, compute the delayed departure and check the cargo window.
- `divert_store`: nearest reachable cold store/ice plant, with `estimated_value_saved_inr` using a simple spoilage heuristic (mock; labelled).
Show at most 3 options; mark exactly one `recommended: true` (safest viable, then fastest).

### ETA
```
segment_time = length_km / base_speed(road_class)         # highway 45 km/h, state_road 30 km/h (config)
speed_multiplier: low 1.0, medium 0.75, high 0.4           # high only used for the wait/compare view
peak-hour multiplier 1.2 for 08:00-10:00 and 17:00-19:00
rest: add 30 min after every 4.5 h of driving
expected = sum(segment_time * multipliers) + rests
earliest = expected * 0.92
latest   = expected * (1.10 + 0.05 * n_medium_segments)    # round to 5 min
reason   = string built from the largest differences vs. the normal main route
```
Fuel cost: `distance_km * 14` INR per km for LCV (config; other vehicles in `vehicles.json`).

### Service-point reachability (by A)
Each service point is attached to a route segment (`attach_segment_id`) with `detour_minutes`. From the truck's current position (a segment ID on the route, default: route start), the point is **reachable** only if no `high`/`closed` segment lies between the position and the attach segment for the selected vehicle. `reachable_minutes` = along-route ETA to that segment + `detour_minutes`. Sort by `reachable` first, then by `reachable_minutes`.

## 1.12 Mock data spec (owned by C, consumed by all)

- **`segments.json`**: about 12 segments for the main route and 8 for each of 1-2 alternates. Fields: `segment_id`, `name`, `route_ids`, `geometry`, `length_km`, `road_class`, `elevation_m`, `river_distance_m`, `historical_flood_count`, `hazard_type`, `clearance_m` (optional), `data_source`.
- **`routes.json`**: `main`, `alt1` (optionally `alt2`), each with `name`, `segment_ids` (ordered), `distance_km`.
- **`scenarios.json`**: `normal` and `flood`. For each: a per-segment map of the dynamic inputs listed in 1.11 plus `data_source` and `timestamp`. **In `flood`:** two or three main-route segments (near the Chalakudy and Aluva crossings) become `high`; one alternate segment becomes `medium`; one segment has `clears_in_hours: 5`. In `normal`, everything is low, perhaps one medium.
- **`service_points.json`**: 25-40 points (hospital, fuel, repair, towing, police, fire, safe_halt, cold_store, food, toilet) along the corridor, with the attach fields from 1.11. At least 2 hospitals so the "nearest reachable" flip demonstrates. Include 2-3 cold stores/ice plants with mock `capacity_status` labelled `simulated`.
- **`flood_history.json`**: per-segment list of `{date, rain_24h_mm, flooded}`. Use real flood-event knowledge only if verified (2018 and 2019 are well-documented); otherwise mark `data_source: "simulated"`.
- **`vehicles.json`**, **`fleet.json`** (5-8 simulated vehicles with `segment_id`, `vehicle_type`, `cargo`, `shelf_life_hours`), **`emergency_codes.json`**.

**Corridor anchors (approximate; C must verify with OpenStreetMap):**
Palakkad (10.787, 76.655), Vadakkencherry (~10.60, 76.48), Thrissur (10.528, 76.214), Chalakudy (10.307, 76.332), Angamaly (10.196, 76.387), Aluva (10.100, 76.357), Kochi (9.931, 76.267).
Main route (illustrative): Palakkad to Thrissur to Chalakudy to Angamaly to Aluva to Kochi (the NH 544 corridor).
Alternate (illustrative, must be validated as drivable): Thrissur to Irinjalakuda to Kodungallur to North Paravur to Kochi.
Do not present any specific road as "known to flood" unless C has confirmed it from a real source; otherwise label it simulated.

## 1.13 Working rules

**Git:** one branch per person (`a/backend`, `b/frontend`, `c/data`, `d/hardware`). Small commits, clear messages. Open a PR to `main`; `main` must always run. Pull from `main` at least every phase.

**Communication between agents** happens through the repo only:
- `docs/STATUS.md`: each agent keeps its own section: *Done / In progress / Blocked / Next*.
- `docs/QUESTIONS.md`: append a line `[from X to Y] question` when you need input. E (human) resolves. Continue with a mock meanwhile.
- `docs/CONTRACT.md`: the API contract.

**Quality:**
- Each P0 function in the risk, routing and ETA code gets tests.
- Handle empty/missing data gracefully (return a clear message, never crash).
- No secrets in the repo; use environment variables.
- Keep UI strings out of code: use the i18n files (B).
- Every new data item states its `data_source`.

**Using Bob effectively:** Use **Plan mode** before each phase, **Code mode** to implement, **Ask mode** to understand. Run `/init` once so Bob generates context, then ensure `AGENTS.md` contains Appendix A. Give Bob small, specific tasks and paste example data into prompts.

**Freeze:** stop adding features about 6 hours before the demo; only fix bugs. (E announces the exact time once the event schedule is known.)

## 1.14 Build phases (all agents work in parallel)

| Phase | A | B | C | D | E |
|---|---|---|---|---|---|
| **1. Setup** | Django skeleton, stub apps, config.py, models; merge to `main` | Base template, Leaflet map with hard-coded sample JSON | Corridor segments and routes (verified), `normal` + `flood` scenarios | Verify hardware; first board-to-board message | AGENTS.md, repo, contract sign-off |
| **2. Core** | Risk engine + tests; `/api/segments/`, `/api/routes/`, `/api/scenario/` | Risk overlay, popups with reasons, flood toggle | Service points, vehicles, flood history; weather client | Packet format; gateway bridge; `/api/emergency/` | Demo script v1 |
| **3. Integrate** | Options, hard filters, ETA; `/api/trip/options/`; service-point ranking | Trip form, options cards, ETA display, service map, emergency mode | Flood memory; fleet data; Open-Meteo wiring | ACK flow; station dashboard | End-to-end testing |
| **4. Polish** | Bug fixes, edge cases | Malayalam toggle, PWA/offline simulation, fleet view | 2018 replay data (stretch) | Rehearse offline demo; link SOS pin onto the map | Slides, backup video, Q&A prep |

---

# PART 2: MEMBER TASKS

---

## MEMBER A: Backend and Risk Engine

**Mission:** You are the brain of the system. Build the Django project, the risk engine, the safe-route options logic, the ETA and the service-point ranking, and expose them through the API contract in 1.10.

**You own:** `backend/safehaul/`, `backend/risk/`, `backend/routing/`, `backend/servicepoints/`, `backend/tests/` (core tests), `docs/CONTRACT.md`.
**You consume:** the JSON files in `data/` (from C). Until they exist, create a tiny stand-in (5 segments, 1 route) in `backend/tests/fixtures/` and keep going.
**You produce for:** B (all `/api/*` except weather and emergency), D (project skeleton), E (`CONTRACT.md`).

### Tasks (in order)

**A1. Project skeleton (first, merge fast, others are waiting).**
- Create the Django project with DRF. Add apps: `risk`, `routing`, `servicepoints`, plus empty stubs `weather` (C) and `emergency` (D).
- Create `backend/safehaul/config.py` containing all constants from 1.11 (weights, thresholds, speeds, multipliers, rest rule, fuel cost).
- Add a data loader that reads the files in `data/` (cache in memory; reload on restart).
- Serve templates/static from `frontend/` (settings pointing to it).
- Write `docs/CONTRACT.md` mirroring 1.10.
- **Done when:** `python manage.py runserver` works, `GET /api/scenario/` returns JSON, and the branch is merged to `main`.

**A2. Risk engine (P0).**
- Implement `risk/engine.py`: `score_segment(segment, dynamic_inputs, vehicle, now) -> dict` returning the segment risk object (1.10) with `risk_score`, `risk_level`, `reasons`, `factors`, `confidence`, `data_source`, `data_timestamp`.
- Follow the formulas, overrides, reasons and confidence rules in 1.11 exactly.
- Integrate flood memory: if `flood_memory` data exists for the segment and `rain_24h_mm >= trigger_mm`, set the history factor to 1.0 and add the explanatory reason.
- Endpoints: `GET /api/segments/?scenario=`, `GET /api/routes/`, `GET/POST /api/scenario/`.
- **Tests:** low/medium/high/closed boundaries; official closure override; depth-level override by vehicle; missing inputs lowering confidence; reasons are non-empty and ordered; flood memory trigger.
- **Done when:** switching to `flood` changes at least 3 segments' levels and each has at least 2 readable reasons.

**A3. ETA (P0).**
- Implement `routing/eta.py`: per-route expected time, `earliest`/`latest` range, rests, peak-hour multiplier and a **reason string** (largest differences vs. the normal main route: added km, number of medium-risk segments, rest breaks, waiting).
- **Tests:** range ordering; medium-risk segments widen the range; rest added after 4.5 h; reason mentions the biggest contributor.

**A4. Route options (P0, the core feature).**
- Implement `routing/options.py` per 1.11: evaluate each route in `routes.json`; apply hard filters in order (safety, clearance, cargo shelf life); build `proceed`, `reroute`, `wait`, `divert_store` options; set exactly one `recommended`; list `excluded_routes` with reasons; at most 3 options.
- `wait` option: compute from `clears_in_hours`; check it stays within the cargo window.
- `divert_store`: use cold stores from `service_points.json` that are `reachable`; include `estimated_value_saved_inr` (simple heuristic in `config.py`, labelled as an estimate/mock).
- If nothing viable: empty `options` plus a clear `message`.
- Endpoint: `POST /api/trip/options/` (request/response in 1.10).
- **Tests:** normal scenario gives `proceed`; flood excludes `main` with a reason; shelf-life too short excludes an otherwise safe alternate; mini_truck vs heavy_truck differences with depth reports; no-viable-option message.
- **Done when:** the demo scenario in 1.6 works end to end through the API.

**A5. Service-point ranking (P0).**
- Implement `servicepoints/ranking.py` and `GET /api/service-points/` per 1.10/1.11. Support `mode=emergency` (categories limited).
- **Tests:** a hospital behind a high-risk segment becomes `reachable=false` with a reason, and the nearest *reachable* one ranks first after the flood toggle.

**A6. Stretch (only after A1-A5 are merged and tested).**
- `GET /api/fleet/`: for each simulated vehicle compute risk, ETA, and a go/hold/divert suggestion (perishables first, most at risk first).
- Clearance filter and time-dependent "safe crossing window" using `clears_in_hours`.
- Basic "disruption certificate" endpoint producing a JSON/HTML summary (timestamps, alerts, excluded routes).

**Do not:** build an ML model, call external APIs directly (use C's `weather` module), or change field names in the contract without approval.

**Kickoff prompt for your Bob (after `/init`):**
> Read docs/TEAM_BRIEF.md (Parts 1 and "Member A") and AGENTS.md. In Plan mode, propose the Django project structure and the order of work for tasks A1-A5. Use data from `data/` with a local stand-in until C delivers. Do not write code yet.

---

## MEMBER B: Frontend and Map

**Mission:** You are the face of the product and the thing judges will see. Build a mobile-first map web app, served by Django, that makes risk, options and ETA instantly understandable to a driver or dispatcher.

**You own:** everything in `frontend/` (templates, static JS/CSS, i18n, service worker, manifest, vendored Leaflet).
**You consume:** the API in 1.10 (from A), plus rainfall and emergency endpoints indirectly. **Until A's endpoints exist, work from sample JSON** that follows the contract exactly (store it in `frontend/static/sample/` and switch to the real API with one config flag).
**You produce for:** E (demo screens), D (a map component the station dashboard may reuse; coordinate through the repo).

### Tasks (in order)

**B1. Base app and map (P0).**
- Django template base with a mobile-first layout, a clear header, a language toggle placeholder and a "SIMULATED DATA" banner that appears whenever `data_source` includes `simulated`.
- Leaflet map centred on the corridor. Bundle Leaflet locally in `static/vendor/` (no CDN dependency). Use OpenStreetMap tiles online; design so the app still shows the route and risk overlay with no tiles.
- Draw routes from `/api/routes/` and segments from `/api/segments/`.

**B2. Risk overlay and explanation (P0).**
- Colour segments by `risk_level` (green, amber, red, dark red/black for closed) **and** add icons/patterns so it is not colour-only.
- Tapping a segment opens a panel showing: level, score, **bulleted reasons**, confidence, **data age** ("updated 12 min ago") and data source.
- A legend, and a persistent data-freshness indicator.

**B3. Flood toggle and trip form (P0).**
- A prominent **"Simulate flood" switch** (calls `POST /api/scenario/`, then refreshes the map and the options). This is the key demo control; make it large and obvious.
- Trip form: origin, destination (dropdown preset to Palakkad/Kochi), departure time, vehicle type, cargo type, weight, shelf-life hours, value. Prefill the demo scenario.

**B4. Options and ETA screens (P0).**
- Call `POST /api/trip/options/`; render **2-3 option cards**: label, type icon, ETA range + the **reason line**, distance, fuel cost, cargo-window status (clear pass/fail with hours remaining), trade-off bullets, and a "Recommended" badge on one card.
- Show `excluded_routes` ("Main route excluded: ...") so the safety filter is visible.
- Selecting an option highlights that route on the map and shows a "Receiver notified of new ETA" confirmation (a mock message panel is fine).
- Handle empty `options` and `message`.

**B5. Service map (P0/P1).**
- Layer for service points with category icons, toggled by filter chips (default 4-5 categories only: hospital, fuel, repair, police, safe halt).
- List view sorted as returned by the API, showing `reachable_minutes`, a "Not reachable (flooded route)" state with the reason, and "last verified".
- **Emergency mode:** a button (and automatic on SOS/alert) switches to `mode=emergency`, showing only hospitals, police, fire, safe halt; the UI turns high-contrast.

**B6. Language and PWA (P1).**
- i18n: `frontend/static/i18n/en.json` and `ml.json`. All UI text through keys. Provide a toggle (English/Malayalam). Write the Malayalam strings with care, **mark them "needs native review"** in a comment/file so E can verify.
- PWA: `manifest.json`, a service worker that caches the app shell and the last API responses, an offline banner, and a visible "risk data is X h old" note when offline.
- **Offline sliding-window simulation:** a slider moves the truck along the route; the UI shows which segments/tiles are "kept" (ahead + a configurable **retreat buffer**, default 25 km) and which are "released". Put the window logic in a pure function `computeWindow(positionKm, segments, retreatBufferKm, aheadKm)` and unit-test it.

**B7. Dispatcher fleet view (P1/P2).** A table/map of simulated vehicles from `/api/fleet/` (when A delivers): position, risk, ETA, go/hold/divert suggestion; perishable loads ranked first.

**B8. Stretch mock screens (P2).** Static, clearly labelled mock-ups: Load Relay request and matched trucks (ranked, with a handover point), Spare Capacity Pool listing, WhatsApp/Malayalam voice reply preview, disruption certificate preview, depth-report buttons (tyre mid-height / wheel hub / floorboard). Coordinate with E, who owns the designs; build only if B1-B6 are solid.

### UI requirements
- Mobile-first, large touch targets (at least 44 px), readable in sunlight and in a moving cab (high contrast, large type).
- Minimal clutter; filters instead of showing everything.
- Always show **timestamps, confidence and data source** near any risk or ETA value.
- Never show a plain "safe". Use wording like "Low risk (moderate confidence)".

**Do not:** invent API fields; hard-code risk results in the UI; depend on a CDN; show precise ETAs without the range.

**Kickoff prompt for your Bob (after `/init`):**
> Read docs/TEAM_BRIEF.md (Part 1 and "Member B") and AGENTS.md. In Plan mode, propose the frontend file structure and the build order for B1-B6, starting with sample JSON that exactly follows the API contract in section 1.10. Do not write code yet.

---

## MEMBER C: Data and Integrations

**Mission:** Your data makes the demo believable. Build the mock dataset (with real geometry where possible), the weather integration with automatic fallback, the service-point list, and the flood-memory logic. **Accuracy and honest labelling matter more than volume.**

**You own:** everything in `data/`, `backend/weather/`, and data-related tests in `backend/tests/`.
**You consume:** nothing from other agents (you are the first dependency).
**You produce for:** A (all `data/*.json`, `weather` module), B (route geometry), D (nothing), E (a data-sources note for the pitch).

### Tasks (in order)

**C1. Corridor and routes (P0, deliver within the first phase; A and B depend on it).**
- Obtain real road geometry for the Palakkad to Kochi main corridor and one or two alternates from OpenStreetMap (Overpass/OSM export, or the public OSRM demo server run once offline to save the geometry). Verify the alternate is actually drivable for trucks.
- Split each route into segments (about 12 for main, 8 per alternate; split at river crossings, underpasses, junctions). Write `data/segments.json` and `data/routes.json` per 1.12.
- Fill static attributes: `elevation_m` (from SRTM/OSM/online elevation data; approximate is fine but note the source), `river_distance_m`, `hazard_type`, `historical_flood_count`.
- **Done when:** the files validate against 1.12, every segment has geometry and all route segment IDs exist.
- Until verified, label any claim like "this road floods" as `simulated`.

**C2. Scenarios (P0).**
- Write `data/scenarios.json` with `normal` and `flood` as specified in 1.12. In `flood`: heavy rain (e.g. 90-130 mm in 24 h), high river levels (80-95%) at the main-route crossings; one alternate segment medium; at least one blocked main segment has `clears_in_hours: 5`; some `crowd_reports` where plausible. Choose values so the formulas in 1.11 produce the intended levels, and **run A's engine (or reimplement the formula in a quick script) to check** the results: main route excluded in `flood`, at least one alternate survives with a longer ETA, the "wait" option fits inside the 8 h shelf life.
- Label everything `data_source: "simulated"`.

**C3. Service points (P0).**
- Write `data/service_points.json`: 25-40 real places along the corridor (hospitals, fuel pumps, repair/tyre, towing where found, police, fire, safe halt/high ground/parking, cold storage/ice plants/dairy chilling centres, food, toilets). Use OSM (Overpass `amenity=hospital`, `amenity=fuel`, etc.) plus manual curation. Include `attach_segment_id` and `detour_minutes` for each.
- At least **2 hospitals** positioned so that the nearest one lies behind a flood-risk segment in the `flood` scenario while another further one stays reachable, so that the "nearest reachable" flip is visible.
- Cold stores: 2-3 with mock `capacity_status` labelled simulated. Record `last_verified` dates honestly (set to the date you checked, or `unverified`).

**C4. Weather module (P1).**
- `backend/weather/client.py`: `get_rainfall(lat, lng) -> {rain_24h_mm, forecast_3h_mm, fetched_at, source}` using **Open-Meteo** (no API key; check its current docs for the hourly `precipitation` variable and the past/forecast-day parameters). Cache results for 15 minutes.
- **Automatic fallback** to the scenario's mock values on any failure or timeout; set `source` accordingly (`"live"` or `"simulated"`).
- Endpoint: `GET /api/rainfall/?lat=&lng=` in `backend/weather/views.py`.
- Add a config flag `USE_LIVE_WEATHER` (default off for the demo) so A can optionally blend live rainfall into the live scenario.
- Tests with a mocked HTTP response and with a forced failure.

**C5. Flood memory (P2).**
- `data/flood_history.json` plus a function `compute_flood_memory(segment_id) -> {trigger_mm, events}` (for example, the lowest `rain_24h_mm` among past events where the segment flooded, requiring at least 2 events; otherwise return none). Provide it as a module A can import (e.g. `backend/weather/flood_memory.py`) and hand A the exact signature.
- Use verified real historical events only if you can cite them; otherwise mark `simulated`. Keep a `data/SOURCES.md` listing every source and its licence/terms.

**C6. Supporting data (P1).**
- `vehicles.json` (1.11 table), `fleet.json` (5-8 simulated vehicles), `emergency_codes.json` (codes 01-07, with English text; leave `ml` empty for E).
- **Stretch:** 2018 flood replay data (real IMD rainfall and reported impacts for the corridor) if sources are accessible.

**C7. Data-sources note (for E).** `data/SOURCES.md`: what is real, what is simulated, where each field came from, and known limits. E will use it to answer judges' questions.

**Do not:** present guessed facts as real; skip `data_source`; make live APIs a hard dependency; scrape sites that forbid it.

**Kickoff prompt for your Bob (after `/init`):**
> Read docs/TEAM_BRIEF.md (Part 1 and "Member C") and AGENTS.md. In Plan mode, propose how to build `data/segments.json`, `routes.json` and `scenarios.json` for the Palakkad-Kochi corridor from OpenStreetMap, and how to validate that the flood scenario excludes the main route under the formulas in section 1.11. Do not write code yet.

---

## MEMBER D: Hardware and Emergency Communication

**Mission:** Build the "wow factor": a working emergency message from a "truck" device to a "police station" dashboard with **no internet**, with acknowledgement. This is the most memorable moment of the demo; prioritise reliability over features.

**You own:** `hardware/` (firmware, gateway bridge), `backend/emergency/` (models, API, station dashboard template/static), emergency tests.
**You consume:** the Django skeleton (A), `data/emergency_codes.json` (C), shared styles (B) if convenient.
**You produce for:** B/E (a station dashboard view and an SOS marker the main map can display), E (demo script steps for the hardware).

### Tasks (in order)

**D1. Check hardware first (do this immediately).**
- List what the team actually has. Target: **2 or more ESP32 + LoRa (SX127x) boards** (such as Heltec/TTGO LoRa32 or similar) with antennas, at least one GPS module (or use fixed demo coordinates if no GPS), and USB cables. If hardware is missing, tell E at once through `docs/QUESTIONS.md` so it can be sourced. **Fallback plan** if hardware cannot be obtained: a laptop-to-laptop simulated mesh script and a clearly labelled simulation.
- Check the LoRa frequency band for India (license-exempt band around 865-867 MHz); set the module and antenna to a legal configuration and note the exact setting in `hardware/README.md` (verify current rules; keep power low for the demo).

**D2. Firmware v1: send and receive (P1).**
- Truck device: a button sends the selected code (cycle through 01-07 with a second button, or a rotary/serial command). It reads GPS (or fixed coordinates) and transmits a **14-byte packet**:
  `code u8 | vehicle_id u16 | seq u8 | lat i32 (deg x 1e5) | lon i32 (deg x 1e5) | minutes_of_day u16`
- **Acknowledgement packet (5 bytes):** `'A' | station_id u8 | vehicle_id u16 | seq u8`.
- Truck repeats the packet every few seconds (with a retry limit) until it receives a matching ACK, then shows "RECEIVED by Station N" on its display/LED/serial.
- Station (gateway) device: receives packets, prints one JSON line per event over USB serial, and transmits an ACK on a command from the laptop (or automatically in the first version).
- **Done when:** pressing the button on device 1 shows the event on device 2's serial output and device 1 gets the ACK, with no Wi-Fi/internet involved.

**D3. Gateway bridge (P1).**
- `hardware/gateway/bridge.py`: reads the serial JSON lines, converts to the API form in 1.10, and `POST`s to `http://localhost:8000/api/emergency/`. Also polls for newly `acked` events and tells the station board to send the ACK, or ACKs on receive in v1.
- Must run with **no internet**, only the local server.

**D4. Backend emergency app (P1).**
- Models: `EmergencyEvent` (code, vehicle_id, seq, lat, lng, device_ts, received_at, via, station_id, status, acked_by, acked_at).
- Endpoints: `POST /api/emergency/`, `GET /api/emergency/?since=`, `POST /api/emergency/<id>/ack/` per 1.10. De-duplicate repeated packets (same vehicle_id + seq).
- Tests: create, duplicate suppression, ack, listing since a timestamp, invalid code rejected.

**D5. Station dashboard (P1).**
- A page at `/station/`: live-updating list (poll every 2 s) of events with code meaning (from `emergency_codes.json`), vehicle, time, location on a small map, status, and an **"Acknowledge"** button that sends the ACK back. New events should be visually and audibly obvious.
- Simple, high-contrast, works with no internet (bundled assets).
- Optional: show the nearest reachable help using `GET /api/service-points/?mode=emergency` and attach it to the event view.

**D6. Peer warning (P1/P2).** A third device or a second truck board receives a broadcast of code `02`/`03` (landslide/flood ahead) directly from a nearby truck (no gateway) and shows it, demonstrating the mesh/peer warning. If you only have two boards, simulate the third in software and label it.

**D7. Fallbacks and Morse (P2).**
- App-side fallback ladder (design the logic and mock UI): app data, SMS, LoRa, Morse. If an SMS gateway is not available, mock it.
- A small "Morse guide" page/function that converts a code into a torch/horn pattern (for example, display the dot/dash sequence for `01` SOS and others). Include in the station dashboard docs. Zero hardware.

**D8. Demo hardening (P1).** Write `hardware/README.md` (wiring, flashing, run steps) and a 1-page **demo runbook**: power-on order, how to turn the internet off, what to press, what the audience should see, and what to do if the radio link fails (backup: pre-recorded video + the simulated script). Rehearse at least 5 times.

**Do not:** claim a range you have not measured (state "a few km in open terrain, less in hills/foliage"); depend on the public internet; use high transmit power; build custom radio protocols beyond what the packet format above needs.

**Kickoff prompt for your Bob (after `/init`):**
> Read docs/TEAM_BRIEF.md (Part 1 and "Member D") and AGENTS.md. In Plan mode, propose the firmware structure for an ESP32+LoRa truck device and gateway using the 14-byte and 5-byte packet formats, the serial-to-API bridge, and the Django `emergency` app with the station dashboard. Ask me which board model I have before choosing libraries. Do not write code yet.

---

## MEMBER E: Product, Pitch and QA (human coordinator, for reference)

E is the human coordinator. Agents should route product questions to E through `docs/QUESTIONS.md`.

E's responsibilities: final PRD (`docs/PRD.md`); `AGENTS.md` and README; the demo script and backup recording; slides; stretch-feature mock-ups (Load Relay, Spare Capacity Pool, WhatsApp/Malayalam flow, disruption certificate); Malayalam text review; verifying vehicle limit assumptions and place names; end-to-end testing as the first "judge"; preparing answers to likely judge questions (data sources, accuracy, legal aspects of relay and permits/e-way bills, radio rules, business model, why not Google Maps).

---

# APPENDIX A: Content for `AGENTS.md` (paste into the repo root)

```
# SafeHaul Kerala: Agent rules
Project: flood-aware logistics planner for Kerala (IBM x Kerala Govt Hackathon 2026, Challenge 5).
Read docs/TEAM_BRIEF.md first (Part 1 + your member section). API contract: docs/CONTRACT.md.

Stack: Python + Django + DRF, SQLite, Leaflet frontend served by Django (no Node build), ESP32+LoRa hardware.

Hard rules:
- Safety is a HARD FILTER. Shelf life is a second HARD FILTER. Never decide silently: present 2-3 labelled options.
- Every risk score has reasons, confidence, data_source and data_timestamp.
- Every data item carries data_source: live | simulated | historical. UI shows a SIMULATED DATA banner when relevant.
- Warnings lean conservative. Never show a bare "safe". ETA is always a range with a reason.
- Mock data first; live APIs always have automatic fallback. Demo must not depend on live feeds.
- No own weather model. No payment code. No external CDN dependencies in the frontend.
- All constants live in backend/safehaul/config.py. Do not hard-code them elsewhere.
- Edit only files you own (see ownership in the brief). Put questions in docs/QUESTIONS.md and update docs/STATUS.md.
- Do not change API field names without approval. Additive fields are OK.
- Write tests for risk, filters, ETA, flood memory, emergency API.
- Use Plan mode before each phase, Code mode to implement, Ask mode to understand.
```

# APPENDIX B: Glossary

- **Segment:** a short stretch of road with its own risk score (the unit of risk).
- **Route:** an ordered list of segments from origin to destination.
- **Hard filter:** a rule that excludes an option entirely (as opposed to a score that merely penalises it).
- **Cargo window / shelf life:** the time the cargo can stay in transit before it spoils.
- **Flood memory:** the rainfall level at which a segment has flooded in past events.
- **Retreat buffer:** the road behind the truck kept in the offline cache, so the driver can turn back.
- **Safe halt point:** an elevated, reachable place to park and wait out a flood.
- **Safe-harbor / divert-and-store:** sending perishable cargo to a nearby cold store or ice plant when the route is blocked.
- **Load Relay:** a stranded truck's cargo is handed over to a nearby truck with spare capacity.
- **Spare Capacity Pool:** warehouses post stock for trucks with spare capacity to deliver.
- **LoRa:** a low-power, long-range radio technology used for the SOS mesh.
- **Gateway:** the station-side LoRa device connected to the dashboard.
- **ACK:** acknowledgement that an emergency message was received.
- **Simulated / historical / live:** the three allowed `data_source` values.
