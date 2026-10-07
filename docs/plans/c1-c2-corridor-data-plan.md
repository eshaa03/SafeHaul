# Plan: C1 + C2 — Corridor Segments, Routes, and Scenarios

**Member:** C  
**Branch:** `c/data`  
**Files produced:** `data/segments.json`, `data/routes.json`, `data/scenarios.json`, `data/SOURCES.md` (started)

---

## Top-Level Overview

Build the three foundational data files that every other member depends on.
Member A cannot test the risk engine without segments and scenarios.
Member B cannot draw the map without route geometry.

The approach is:

1. Source real road geometry from OpenStreetMap for the NH 544 Palakkad → Kochi corridor and one verified alternate.
2. Split each route into hand-curated segments at the right topographic break-points.
3. Fill every static attribute using OSM tags and publicly available elevation/river data.
4. Write two scenario blocks (normal, flood) whose dynamic values are chosen so the §1.11 formulas
   produce exactly the intended risk levels — verified by running the formula in a small validation script.
5. Record every source and its licence in `data/SOURCES.md`.

No live API is called at runtime; all geometry and static data are stored as JSON.

---

## Sub-Task C1a — Obtain road geometry from OpenStreetMap

**Intent**  
Get the actual polyline coordinates for (a) the main NH 544 corridor and (b) the alternate
Thrissur → Irinjalakuda → Kodungallur → North Paravur → Kochi route so segment geometry
is real, not invented.

**Approach**  
Use the public Overpass API (`https://overpass-api.de/api/interpreter`) with a one-off query —
or the `overpy` Python library in a standalone script (`data/scripts/fetch_osm.py`) that is run once
and whose output is committed.  The script is never called at demo time.

Two Overpass queries needed:
- NH 544 (relation or way tagged `ref=NH 544` or `highway=trunk` between corridor anchors)
- Alternate state roads: SH 15 / MDR between Thrissur, Irinjalakuda, Kodungallur, North Paravur,
  and the Kochi bypass

**What to store from OSM**  
- Ordered `[lat, lng]` coordinate list for each way
- OSM `highway` tag → maps to our `road_class` (`trunk`/`primary` → `"highway"`;
  `secondary`/`tertiary` → `"state_road"`)
- OSM `maxheight` tag where present → populates `clearance_m`

**Verify drivability of the alternate**  
Check that the alternate ways are not `access=no`, `motor_vehicle=no`, or `tunnel=yes` with
a height that blocks HGVs.  Record result in `data/SOURCES.md`.

**Expected Outcomes**  
- A saved geometry file (e.g. `data/scripts/raw_osm_ways.json`) or inline coordinates used directly
- Confirmed that the alternate is truck-drivable from OSM tags

**Relevant Context**  
- Corridor anchors (§1.12): Palakkad (10.787, 76.655) → Vadakkencherry → Thrissur (10.528, 76.214)
  → Chalakudy (10.307, 76.332) → Angamaly (10.196, 76.387) → Aluva (10.100, 76.357) → Kochi (9.931, 76.267)
- Alternate: Thrissur → Irinjalakuda (~10.34, 76.21) → Kodungallur (~10.23, 76.21) →
  North Paravur (~10.15, 76.22) → Kochi (9.931, 76.267)
- `road_class` values used in ETA formula: `"highway"` = 45 km/h, `"state_road"` = 30 km/h

**Todo List**  
- [ ] Write `data/scripts/fetch_osm.py` with Overpass queries for main and alternate routes
- [ ] Run the script once; save the raw output to `data/scripts/raw_osm_ways.json`
- [ ] Verify alternate way tags (access, motor_vehicle, maxheight)
- [ ] Add OSM attribution and Overpass API terms note to `data/SOURCES.md`

**Status:** `[x] done`

---

## Sub-Task C1b — Split routes into segments and fill static attributes

**Intent**  
Produce `data/segments.json` and `data/routes.json` conforming exactly to §1.12.
Segment boundaries are chosen at meaningful physical break-points so the demo's
flood-risk story is credible.

**Segment count targets**  
- Main route (`main`): ~12 segments
- Alternate route (`alt1`): ~8 segments

**Where to split** (main route, south to north, reversed for Palakkad→Kochi direction)  
Place boundaries at:
- The Bharathapuzha river crossing east of Thrissur (high river-proximity hazard)
- The Chalakudy river crossing south of Chalakudy (demo's primary flood segment)
- The Periyar river crossing near Aluva (demo's secondary flood segment)
- Major junctions (Thrissur bypass, Angamaly interchange)
- Any known underpass or low bridge along NH 544 (mark `hazard_type: "underpass"`)
- Logical "chapters" of road between the above (to reach ~12 total)

For the alternate, split at Irinjalakuda, Kodungallur, and North Paravur junctions, and at
any river crossings visible on OSM.

**Static attribute sources**  
| Attribute | Source |
|---|---|
| `elevation_m` | SRTM 1-arc-second (approx mid-point of segment); use `open-elevation.com` API once offline, or look up on Google Maps terrain; note as `"historical"` |
| `river_distance_m` | Measured from OSM waterway centreline to road; approximate to nearest 100 m; note as `"historical"` |
| `historical_flood_count` | 2018 and 2019 Kerala floods: use only publicly documented road closures; label anything estimated as `"simulated"` |
| `hazard_type` | OSM tags (`tunnel`, `maxheight`, `ford`, `flood_prone`) or manual review of satellite imagery for known underpasses |
| `clearance_m` | OSM `maxheight` tag where present; omit field otherwise |
| `road_class` | Derived from OSM `highway` tag (see C1a) |
| `geometry` | Subset of the OSM polyline for this segment, as `[[lat, lng], ...]` |

**`segment_id` convention**  
- Main route segments: `M-01` through `M-12` (Palakkad end to Kochi end)
- Alternate segments: `A-01` through `A-08`

**`route_ids` field**  
Each segment lists the routes it belongs to, e.g. `["main"]` or `["alt1"]`.
Shared segments (if any junction segment appears on both) list both IDs.

**`routes.json` structure**  
```json
[
  { "id": "main",  "name": "NH 544 Main Corridor",      "segment_ids": ["M-01", ..., "M-12"], "distance_km": 124 },
  { "id": "alt1",  "name": "Alt via Kodungallur",        "segment_ids": ["M-01", ..., "M-04", "A-01", ..., "A-08"], "distance_km": 142 }
]
```
Note: the alternate shares the first few main-route segments (Palakkad to Thrissur) before
diverging; those shared segments carry `"route_ids": ["main", "alt1"]`.

**Expected Outcomes**  
- `data/segments.json` validated: every field from §1.12 present, every segment has at least 2 geometry points
- `data/routes.json` validated: every `segment_id` in each route exists in `segments.json`
- `data/SOURCES.md` lists source and `data_source` value for each attribute

**Todo List**  
- [ ] Define the 12 main-route segment boundaries on a map; record start/end lat-lng
- [ ] Define the 8 alternate-route segment boundaries
- [ ] Extract the geometry sub-polyline for each segment from the OSM data obtained in C1a
- [ ] Look up `elevation_m` for each segment mid-point (SRTM or open-elevation)
- [ ] Estimate `river_distance_m` for each segment
- [ ] Assign `hazard_type` and `historical_flood_count` per segment
- [ ] Write `data/segments.json`
- [ ] Write `data/routes.json`
- [ ] Cross-check: every segment ID in routes.json exists in segments.json
- [ ] Update `data/SOURCES.md` with attribute sources

**Status:** `[x] done`

---

## Sub-Task C2 — Write scenarios.json and validate against the §1.11 formulas

**Intent**  
Produce `data/scenarios.json` with `normal` and `flood` blocks.
Then verify — using the exact §1.11 formula — that the flood scenario achieves:
- At least 2 main-route segments rated `high` or `closed` (forcing hard-filter exclusion)
- At least one alternate segment rated `medium` (not excluded, but visible in trade-offs)
- The `wait` option is viable: `clears_in_hours` on a blocking segment + expected ETA ≤ 8 h shelf life

**Scenario structure (per §1.12)**  
Each scenario entry is a dict keyed by `segment_id`. Each entry contains:
```json
{
  "rain_24h_mm": 95,
  "forecast_3h_mm": 30,
  "river_level_pct": 88,
  "official_closure": false,
  "crowd_reports": 2,
  "reported_depth_level": 0,
  "clears_in_hours": 5,
  "data_source": "simulated",
  "timestamp": "2026-10-08T06:00:00+05:30"
}
```
Segments not needing special values can share a "low" default block.

**Target flood values for the demo story**  
| Segment | Planned level | Key values to drive it |
|---|---|---|
| M-07 Chalakudy river crossing | `high` | rain ~110 mm, river_level ~90%, 2 crowd reports |
| M-09 near Angamaly | `high` | rain ~95 mm, river_level ~85%, hazard=underpass |
| M-11 Aluva Periyar crossing | `high` | rain ~105 mm, river_level ~88%, historical_flood_count 2 |
| A-04 near Kodungallur | `medium` | rain ~55 mm, river_level ~50% |
| All other segments | `low` | rain ~15 mm, river_level ~20% |

One blocking segment (e.g. M-07) should have `clears_in_hours: 5`.

**Validation script (`data/scripts/validate_scenarios.py`)**  
A standalone Python script that:
1. Loads `segments.json` and `scenarios.json` (no Django dependency)
2. Implements the §1.11 formula verbatim
3. Prints each segment's `risk_score` and `risk_level` for both scenarios
4. Asserts: in `flood`, the `main` route contains at least 2 `high`/`closed` segments;
   in `normal`, no segment exceeds `medium`
5. Asserts: the `wait` option fits (clears_in_hours + normal ETA ≤ 8 h)

This script is the "proof of correctness" for C2. Running it with no assertion errors
is the definition of done.

**Normal scenario**  
All main-route segments: low (rain ~10 mm, river_level ~15%).
One segment `M-05` (Thrissur bypass): medium (rain ~45 mm, river_level ~35%) to give
the UI something amber to show even in normal mode.

**Expected Outcomes**  
- `data/scenarios.json` exists and is valid JSON
- `python data/scripts/validate_scenarios.py` exits with no assertion errors
- Flood: main route excluded (2+ high segments), alt1 survives with 1 medium segment
- Normal: proceed option available, one amber segment

**Relevant Context**  
- §1.11 risk formula and level thresholds: `< 0.30` low; `0.30–0.55` medium; `0.55–0.80` high; `>= 0.80` closed
- Hard filter: exclude route if any segment is `high` or `closed`
- **Wait option design — confirmed decision:** use `clears_in_hours: 5` on M-07.
  Delayed ETA = 5 + ~4.5 h = 9.5 h > 8 h shelf life, so the Wait option is also excluded
  by the cargo hard filter. Only Reroute and Divert-and-store survive. This makes the
  shelf-life filter dramatically visible in the demo.
- `clamp(x)` = `max(0, min(1, x))`
- Validation script must assert that `clears_in_hours + main_route_eta_h > shelf_life_h`
  (i.e. 9.5 > 8 → wait NOT viable)

**Todo List**  
- [ ] Write the `normal` scenario block covering all segments
- [ ] Work out the flood values per target segment using the formula to confirm desired level before writing
- [ ] Write the `flood` scenario block
- [ ] Write `data/scripts/validate_scenarios.py`
- [ ] Run the script; iterate values until all assertions pass
- [ ] Confirm that at least one blocking segment has `clears_in_hours` set
- [ ] Label all entries `data_source: "simulated"` and set a plausible fixed timestamp

**Status:** `[x] done`

---

## Sub-Task C1c — Start data/SOURCES.md

**Intent**  
Create `data/SOURCES.md` now (even as a skeleton) so that every attribute in the above files
has a documented provenance. Judges will ask where the data came from.

**What to record per source**  
- Source name and URL
- Date accessed
- Licence or terms (OSM = ODbL; SRTM = public domain; Overpass = ODbL)
- Which fields it populates
- `data_source` value assigned (`"live"` / `"simulated"` / `"historical"`)
- Known limitations or caveats (e.g. "elevation rounded to nearest 5 m")

**Expected Outcomes**  
- `data/SOURCES.md` exists with a row for each data source used so far
- Every static attribute in `segments.json` traces to at least one row in SOURCES.md

**Todo List**  
- [ ] Create `data/SOURCES.md` with section headers (OSM geometry, SRTM elevation, flood history, simulated fields)
- [ ] Fill rows as each attribute source is confirmed during C1b
- [ ] Add a "Simulated / assumptions" section for anything not externally sourced

**Status:** `[x] done`

---

## Dependency and ordering diagram

```
C1a (OSM geometry)
    └─► C1b (segments + routes)
            ├─► C2 (scenarios + validation script)
            └─► C1c (SOURCES.md, filled in parallel with C1b)
```

C2 cannot start until C1b is complete because the validation script needs the
static attributes (`elevation_m`, `river_distance_m`, etc.) to compute static scores.

---

## Definition of "Done" for this plan

- [ ] `data/segments.json` — all fields present, all geometry non-empty, IDs consistent
- [ ] `data/routes.json` — main and alt1, segment IDs resolve
- [ ] `data/scenarios.json` — normal and flood, all segment IDs present
- [ ] `data/scripts/validate_scenarios.py` runs with zero assertion errors
- [ ] `data/SOURCES.md` — every attribute has a source row
- [ ] `data/scripts/raw_osm_ways.json` (or equivalent) committed alongside the scripts
- [ ] No hard-coded constants: dynamic inputs only in scenarios.json, statics only in segments.json
- [ ] All entries carry correct `data_source` value
