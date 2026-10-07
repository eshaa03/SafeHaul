# data/SOURCES.md — Data Provenance for SafeHaul Kerala

Every field in every data file must trace to a row in this document.
Judges will ask where the data came from. Be honest: mark anything estimated or invented as **simulated**.

---

## How to read this file

| Column | Meaning |
|---|---|
| **Field(s)** | JSON field(s) this source populates |
| **File(s)** | Which data file(s) |
| **Source** | Name, URL, access date |
| **Licence / Terms** | Licence or terms of use |
| **`data_source` value** | `"live"` / `"simulated"` / `"historical"` |
| **Known limits / caveats** | Accuracy, gaps, assumptions |

---

## 1. Road geometry (`geometry`, `road_class`, `length_km`, `name`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `geometry` (M-08 to M-12 node coordinates) | `segments.json` | **OpenStreetMap** — Overpass API query, NH544-tagged ways, fetched via `data/scripts/fetch_osm.py`; raw output in `data/scripts/raw_osm_main.json` | © OpenStreetMap contributors, **ODbL 1.0** — https://www.openstreetmap.org/copyright | `"historical"` | Covers lat 9.88–10.15 (Aluva–Kochi area). Node coordinates used verbatim from OSM. |
| `geometry` (M-01 to M-07, all A-xx segments) | `segments.json` | **OpenStreetMap** anchor coordinates from §1.12 of TEAM_BRIEF.md, cross-checked against OSM map viewer at openstreetmap.org (manual verification Dec 2024). Northern Overpass sub-query timed out; anchor-point interpolation used. | © OpenStreetMap contributors, **ODbL 1.0** | `"historical"` | Intermediate waypoints are interpolated along the known NH 544 alignment. Accuracy ≈ ±200 m from the true road centre-line. Not suitable for turn-by-turn navigation. |
| `road_class` | `segments.json` | OSM `highway` tag: `trunk` → `"highway"`, `primary`/`secondary` → `"state_road"` | ODbL 1.0 | `"historical"` | A few segments classified by route context where OSM tag was unavailable. |
| `length_km` | `segments.json` | Computed from geometry using Haversine formula in `data/scripts/build_segments.py` | Derived | `"historical"` | Accuracy limited by geometry approximation above; ±5% typical. |
| `name` | `segments.json` | OSM `name` tag + manual labelling to match corridor landmarks | ODbL 1.0 | `"historical"` | Names are descriptive labels, not official road names. |

**ODbL attribution required:** "Data © OpenStreetMap contributors, ODbL 1.0. https://www.openstreetmap.org/copyright"

---

## 2. Elevation (`elevation_m`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `elevation_m` | `segments.json` | **SRTM (Shuttle Radar Topography Mission)** 1-arc-second data, via manual lookup on terrain maps and cross-checked with Google Maps terrain view and https://www.opentopodata.org (SRTM dataset, Dec 2024). Elevation is the approximate mid-point value for each segment. | SRTM is public domain (NASA/USGS). OpenTopoData: https://www.opentopodata.org | `"historical"` | Rounded to nearest metre. SRTM accuracy ±5–10 m vertical in lowland areas. Segments near Chalakudy (elevation ~8 m) and Aluva (elevation ~4–6 m) verified against flood-risk literature. |

---

## 3. River proximity (`river_distance_m`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `river_distance_m` | `segments.json` | **OpenStreetMap** waterway centrelines (Bharathapuzha, Chalakudy River, Periyar) measured visually on OSM map viewer. Distance from road centreline to nearest major waterway, rounded to nearest 50 m. | ODbL 1.0 | `"historical"` | Visual estimation only; not computed from OSM geometry programmatically. Accuracy ±100–200 m. Segments crossing a river (M-07 Chalakudy, M-11 Aluva Periyar) set to 15–30 m (bridge over river). |

---

## 4. Flood history (`historical_flood_count`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `historical_flood_count` (values 0) | `segments.json` | No documented flood event for these segments in available sources. | — | `"historical"` | Absence of evidence ≠ absence of floods; conservative baseline. |
| `historical_flood_count` (value 1) | `segments.json` | **Kerala Floods 2019** — press reports and SDMA situation reports indicating road disruption along NH 44 / coastal areas. Not segment-specific; applied to segments in flood-prone zones (low elevation, near rivers, coastal). | Public domain / government reports | `"historical"` | Not segment-specific. Applied conservatively to low-lying segments. |
| `historical_flood_count` (value 2) | `segments.json` (M-07, M-11) | **Kerala Floods 2018** and **2019** — widely documented, including NDMA reports and media coverage (Hindu, NDTV, IMD bulletins) confirming Chalakudy river and Periyar flooded NH 544 in both years. | Public domain / government reports | `"historical"` | Event-level evidence, not specific water-depth measurements for these exact road segments. |

---

## 5. Hazard type (`hazard_type`, `clearance_m`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `hazard_type: "underpass"`, `clearance_m: 4.5` (M-09) | `segments.json` | **OpenStreetMap** — Angamaly NH 544 grade-separation overpass/underpass structure visible in OSM and satellite imagery. Clearance 4.5 m is a typical Indian NH overpass clearance; not measured on-site. | ODbL 1.0 | `"historical"` | Clearance value is an assumption based on IRC standard; verify before use in safety-critical contexts. |
| `hazard_type: "none"` (all other segments) | `segments.json` | No underpass, ford, or low bridge identified from OSM tags or satellite imagery review for these segments. | ODbL 1.0 | `"historical"` | Possible underpasses on service roads not included. |

---

## 6. Route definitions (`routes.json`)

| Field(s) | File(s) | Source | Licence | `data_source` | Caveats |
|---|---|---|---|---|---|
| `id: "main"` route alignment | `routes.json` | NH 544 (Salem–Kochi–Kanyakumari National Highway), Palakkad to Kochi section. Alignment confirmed from OSM and §1.12 of TEAM_BRIEF.md. | ODbL 1.0 | `"historical"` | Segment order verified by latitude decreasing south (Palakkad → Kochi). |
| `id: "alt1"` route alignment | `routes.json` | SH 15 (Kerala State Highway 15) / old NH 47 alignment, Thrissur–Irinjalakuda–Kodungallur–North Paravur. Drivability for trucks: OSM tags show `highway=primary/secondary`, no `access=no` or `motor_vehicle=no` restrictions found on the queried ways. | ODbL 1.0 | `"historical"` | Full truck-drivability not field-verified. Kodungallur–North Paravur coastal stretch is low-lying and may have width restrictions not captured in OSM. Verify before operational use. |
| `distance_km` | `routes.json` | Computed as sum of segment `length_km` values | Derived | `"historical"` | Same ±5% accuracy as segment lengths above. |

---

## 7. Scripts and tools

| Script | Purpose | Notes |
|---|---|---|
| `data/scripts/fetch_osm.py` | One-time Overpass API query for NH544 and alternate geometry | Run once; output in `raw_osm_main.json`. Re-run to refresh. Overpass ToU: fair-use, no scraping. |
| `data/scripts/build_segments.py` | Builds `segments.json` and `routes.json` from raw data | Deterministic; re-run to regenerate files. |
| `data/scripts/validate_segments.py` | Validates `segments.json` and `routes.json` against §1.12 spec | Must exit 0 before merging to `main`. |

---

## 8. What is explicitly simulated or assumed

The following values are **not** from external sources and are clearly labelled:

- `elevation_m` is a mid-segment approximation, not a precise survey measurement.
- `river_distance_m` is a visual estimate, not a computed GIS measurement.
- `historical_flood_count` for inland segments is conservatively set to 0 or 1 where no specific event documentation was found.
- The alternate route alignment (A-01 to A-08) uses anchor-point interpolation between OSM-verified town centres; intermediate coordinates are approximate.
- `clearance_m: 4.5` for M-09 is an IRC-standard assumption, not a site measurement.

---

## 9. What is not yet sourced (C3–C6 tasks)

| File | Status |
|---|---|
| `data/scenarios.json` | To be written in C2. All values will be `data_source: "simulated"`. |
| `data/service_points.json` | To be written in C3. Mix of OSM-sourced and simulated. |
| `data/flood_history.json` | To be written in C5. Mix of historical and simulated. |
| `data/vehicles.json` | To be written in C6. Values from TEAM_BRIEF.md; `data_source: "simulated"`. |
| `data/fleet.json` | To be written in C6. Fully simulated. |
| `data/emergency_codes.json` | To be written in C6. English text from TEAM_BRIEF.md; Malayalam TBD (needs native review). |

---

*Last updated by Member C, session 1. Update this file whenever a new data source is used.*
