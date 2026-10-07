# SafeHaul Kerala — Member B: Frontend Build Plan

## Top-Level Overview

**Goal:** Build the complete `frontend/` for SafeHaul Kerala — a mobile-first, Django-served Leaflet map app that makes flood risk, route options and ETAs instantly understandable to a driver or dispatcher. All P0 tasks (B1-B5) must work flawlessly before any P1/P2 work begins.

**Scope:** everything inside `frontend/` (templates, static JS/CSS, i18n JSON, service worker, manifest.json, vendored Leaflet, sample JSON). No backend files are touched; the frontend consumes the API contract from `docs/TEAM_BRIEF.md` section 1.10.

**Approach:** work from sample JSON first. A single config flag (`SAFEHAUL_USE_REAL_API` in `frontend/static/js/config.js`) switches between sample files and the real API when A's endpoints are live. Every sub-task is independently committable to `b/frontend`.

**Key constraints:**
- No external CDN. Leaflet (and any fonts/icons) must be in `static/vendor/`.
- All UI strings in `static/i18n/en.json` and `static/i18n/ml.json`. Never in HTML/JS directly.
- All tunable constants (map centre, default vehicle, sample-JSON paths, etc.) in `static/js/config.js`.
- Never show a plain "safe". Use wording like "Low risk (moderate confidence)".
- ETA always shown as a range with a reason.
- SIMULATED DATA banner appears whenever any `data_source` value equals `"simulated"`.
- Timestamps, confidence and data source appear near every risk or ETA value.
- Touch targets at least 44 px; readable in sunlight; high contrast.

---

## File Structure

```
frontend/
├── templates/
│   └── safehaul/
│       ├── base.html          # shared layout: header, language toggle, SIMULATED banner, footer
│       ├── map.html           # main view (extends base): map + side panels
│       ├── options.html       # trip options cards (can be a partial/include)
│       └── service_map.html   # service points panel (can be a partial/include)
└── static/
    ├── vendor/
    │   └── leaflet/           # leaflet.js, leaflet.css, marker icons (no CDN)
    ├── js/
    │   ├── config.js          # USE_REAL_API flag, map centre, API paths, sample JSON paths
    │   ├── i18n.js            # loads en.json or ml.json; exposes t(key) helper
    │   ├── api.js             # fetch wrappers for every endpoint; falls back to sample JSON
    │   ├── map.js             # Leaflet init, segment overlay, route drawing
    │   ├── risk.js            # colour/icon/pattern for risk levels; popup renderer
    │   ├── trip.js            # trip form logic + call to /api/trip/options/
    │   ├── options.js         # renders option cards, selected-route highlight
    │   ├── service.js         # service-point layer; filter chips; emergency mode
    │   ├── window.js          # pure computeWindow(positionKm, segments, retreatBufferKm, aheadKm) + unit tests
    │   ├── pwa.js             # service-worker registration
    │   └── tests/
    │       └── window.test.js # unit tests for computeWindow (run in browser or with a tiny test harness)
    ├── css/
    │   ├── base.css           # layout, typography, mobile-first, high-contrast tokens
    │   ├── map.css            # map container, overlay styles, risk colours/patterns
    │   └── options.css        # option cards, cargo-window badge, emergency mode
    ├── i18n/
    │   ├── en.json            # all English UI strings
    │   └── ml.json            # all Malayalam UI strings (mark "needs native review")
    ├── sample/
    │   ├── segments.json      # mirrors /api/segments/ contract exactly
    │   ├── routes.json        # mirrors /api/routes/ contract exactly
    │   ├── trip_options.json  # mirrors POST /api/trip/options/ response exactly
    │   ├── service_points.json# mirrors /api/service-points/ contract exactly
    │   ├── scenario.json      # mirrors GET /api/scenario/ response exactly
    │   └── fleet.json         # mirrors /api/fleet/ response exactly (for B7)
    ├── manifest.json
    └── sw.js                  # service worker (app shell + last API response cache)
```

---

## Build Order and Sub-Tasks

### B0 — Sample JSON (prerequisite for everything)
**Status:** `[x] done` — completed as part of B1

**Intent:** create sample data files in `frontend/static/sample/` that exactly mirror every API contract shape from `docs/TEAM_BRIEF.md` section 1.10. These unblock all rendering work before A's endpoints exist. The demo scenario (5,000 kg vegetables, Palakkad→Kochi, LCV, 8 h shelf life) must be represented in full — normal and flood scenarios both.

**Expected Outcomes:**
- `segments.json`: all required fields (`segment_id`, `name`, `route_ids`, `geometry`, `length_km`, `road_class`, `risk_level`, `risk_score`, `reasons[]`, `factors`, `confidence`, `data_source`, `data_timestamp`, `flood_memory`, `clears_in_hours`). At minimum 12 main-route segments and 8 alt1 segments. In the flood variant, at least 2 segments near Chalakudy and Aluva are `"high"` risk.
- `routes.json`: `main` and `alt1` entries with `id`, `name`, `segment_ids[]`, `distance_km`.
- `scenario.json`: `{"scenario": "normal", "data_source": "simulated"}` (the GET response shape).
- `trip_options.json`: a complete flood-scenario response — 2-3 options (`reroute`, `wait`, `divert_store`), `excluded_routes`, `warnings`, `generated_at`, `data_source`. Cargo window values must vary so one option fails the check.
- `service_points.json`: 25-40 points with all required fields; 2+ hospitals so the "nearest reachable" flip works; 2-3 cold stores with `"simulated"` `data_source`; at least one point with `reachable: false` and a `reason`.
- `fleet.json`: 5-8 simulated vehicles.

**Todo List:**
1. Write `frontend/static/sample/segments.json` — 12 main + 8 alt1 segments, both normal and flood states represented (flood state via a second array or a top-level `flood_overrides` map; whichever `api.js` expects — decide in B0 and document in a `# FORMAT NOTE` comment).
2. Write `frontend/static/sample/routes.json`.
3. Write `frontend/static/sample/scenario.json` (GET response shape).
4. Write `frontend/static/sample/trip_options.json` — full flood-scenario response.
5. Write `frontend/static/sample/service_points.json` — 25-40 points.
6. Write `frontend/static/sample/fleet.json`.
7. Cross-check every field name against `docs/TEAM_BRIEF.md` section 1.10. Fix any mismatches.

**Relevant Context:**
- API contract: `docs/TEAM_BRIEF.md` section 1.10 (segment object, trip options request/response, service point object).
- Demo corridor coordinates: Palakkad (10.787, 76.655) → Thrissur (10.528, 76.214) → Chalakudy (10.307, 76.332) → Angamaly (10.196, 76.387) → Aluva (10.100, 76.357) → Kochi (9.931, 76.267).
- Flood scenario rule: two or three main-route segments near Chalakudy and Aluva become `"high"` risk; one alternate segment becomes `"medium"`.

---

### B1 — Base App and Map
**Status:** `[x] done`

**Intent:** create the Django template shell and a working Leaflet map that draws routes and segments from sample JSON. Establishes the mobile-first layout, the SIMULATED DATA banner, the language toggle placeholder, and the `config.js` / `api.js` / `i18n.js` scaffolding that every later task builds on.

**Expected Outcomes:**
- `base.html`: header with app name, language toggle button (wired to i18n.js but styling only for now), SIMULATED DATA banner (hidden by default, shown when any data_source is `"simulated"`), footer.
- `map.html` extends `base.html`: full-viewport Leaflet map centred on the Palakkad–Kochi corridor; routes drawn as polylines from `sample/routes.json`; segments drawn as coloured polylines from `sample/segments.json` (colour by risk_level — full styling done in B2); map still shows route+segments if tiles fail to load.
- `config.js`: `USE_REAL_API = false`, map centre/zoom, API base URL, sample file paths, all as named constants.
- `api.js`: one fetch function per endpoint, each falling back to the corresponding sample JSON file when `USE_REAL_API = false` or when the real call fails.
- `i18n.js`: loads `en.json`; exposes `t(key)` helper; language switch reloads strings without page reload.
- Leaflet JS+CSS+icons bundled in `static/vendor/leaflet/` (no CDN tag in HTML).
- `base.css`: CSS custom properties for risk colours, font scale, touch-target sizes; mobile-first (single column, 16 px+ base).
- Django URL wiring: a view in `frontend/` that serves `map.html` at `/`.

**Todo List:**
1. Download Leaflet release (JS, CSS, marker icons) into `static/vendor/leaflet/`. Update `.gitignore` if needed — vendor assets ARE committed (no CDN fallback).
2. Write `static/js/config.js`.
3. Write `static/js/api.js` with sample-JSON fallback for all endpoints.
4. Write `static/js/i18n.js` and seed `static/i18n/en.json` with at least the base layout string keys.
5. Write `base.html` — layout, header, SIMULATED banner, language toggle placeholder, footer; loads config.js, i18n.js, leaflet CSS, base.css.
6. Write `map.html` — extends base, sets up map div, loads map.js.
7. Write `static/js/map.js` — init Leaflet, draw routes (polylines), draw segment polylines colour-coded by risk_level (basic green/amber/red/dark for now).
8. Write `static/css/base.css` and `static/css/map.css`.
9. Wire Django: `frontend/views.py` + `frontend/urls.py` entry for `/`.
10. Verify the map renders with no network by serving static files locally.

**Relevant Context:**
- Leaflet download: https://leafletjs.com/download.html (copy to vendor; no CDN).
- Django static/template setup: follows standard Django `STATICFILES_DIRS` + `TEMPLATES` settings (A's territory; B adds `frontend/` to those lists via a stub settings include, or asks A via `docs/QUESTIONS.md`).
- `data_source` banner logic: after any API call resolves, if any item in the response contains `data_source === "simulated"`, add class `simulated-active` to `<body>`; CSS shows the banner.

---

### B2 — Risk Overlay and Explanation
**Status:** `[ ] pending`

**Intent:** make the map's risk visualisation fully informative — not just colour but also icons/patterns so it works for colour-blind users. Tapping a segment opens a detail panel that shows everything a driver needs to make a decision.

**Expected Outcomes:**
- Segments coloured AND patterned/icon-marked: green (low), amber/dashed (medium), red/striped (high), dark/cross-hatched (closed).
- Tapping a segment opens a slide-up panel (mobile) or sidebar (desktop) with: `risk_level`, `risk_score`, bulleted `reasons[]`, `confidence`, data age string ("updated 12 min ago" computed from `data_timestamp`), `data_source`, and `clears_in_hours` if present.
- A map legend (always visible, compact) showing the 4 risk levels with their pattern codes.
- A persistent data-freshness indicator in the header (e.g. "Data: 12 min ago | Simulated") that updates when the map refreshes.
- Never shows a plain "safe" — wording is "Low risk (moderate confidence)" etc., driven by i18n keys.

**Todo List:**
1. Define Leaflet `polylineDecorator` or CSS dash patterns for the 4 risk levels in `map.css`. No library CDN — use pure CSS stroke-dasharray on SVG path elements or Leaflet's built-in options.
2. Write `static/js/risk.js` — `styleForRisk(segment)` returns Leaflet polyline options; `renderPopupHTML(segment)` returns the panel HTML using `t()` keys.
3. Update `map.js` to use `styleForRisk` and attach click handler → open panel.
4. Build the slide-up panel HTML in `map.html` (hidden by default; shown on segment click).
5. Add legend component to `map.html` (small, fixed position, keyboard-accessible).
6. Add data-freshness indicator to `base.html` header; `map.js` updates it after each data load.
7. Add all new string keys to `en.json` and `ml.json` (mark ml as "needs native review").
8. Test: click each risk level; verify all fields render; verify "updated X min ago" is computed correctly.

**Relevant Context:**
- Segment object fields: `risk_level`, `risk_score`, `reasons[]`, `confidence`, `data_source`, `data_timestamp`, `clears_in_hours` — all in `static/sample/segments.json`.
- Colour-blind accessibility: use both colour and pattern/icon; contrast ratio ≥ 4.5:1 for text on panel.

---

### B3 — Flood Toggle and Trip Form
**Status:** `[ ] pending`

**Intent:** build the two key demo controls — the "Simulate flood" switch (the single most important UI element for the judges) and the trip form — and wire both to the map refresh cycle.

**Expected Outcomes:**
- A large, prominent "Simulate Flood" toggle button (not a small checkbox) in the header or a fixed overlay. Pressing it calls `POST /api/scenario/ {"scenario":"flood"}` (or flips `config.js` `SCENARIO` to `"flood"` when using sample JSON), then re-fetches segments and options and refreshes the map. A reverse press returns to `"normal"`.
- Trip form (collapsible panel): origin, destination (dropdown, pre-filled Palakkad/Kochi), departure time, vehicle type (dropdown, default LCV), cargo type, weight (kg), shelf-life hours, value (INR). All labels from i18n. "Get Options" button calls `POST /api/trip/options/`.
- Demo scenario values pre-filled (5,000 kg vegetables, LCV, 8 h shelf life, 06:00 departure) — driven by constants in `config.js`.
- The flood toggle and trip form work from sample JSON with no backend.

**Todo List:**
1. Design the flood toggle: large toggle button in the header, with icon + i18n label. On activation, add `data-scenario="flood"` to `<body>` so the SIMULATED DATA banner shows.
2. Write the scenario switch logic in `api.js` / `map.js`: call `POST /api/scenario/` (real) or just flip `config.SCENARIO` (sample), then call `loadSegments()` and `loadOptions()` to refresh.
3. Build the trip form HTML in `map.html` (collapsible side drawer). Wire each field to a `TripRequest` object in `trip.js`.
4. Write `static/js/trip.js` — assembles the request object, calls `api.postTripOptions(request)`, passes result to `options.js`.
5. Pre-fill demo values from `config.js` constants on page load.
6. Add all new string keys to `en.json` + `ml.json`.
7. Test: toggle flood on → segments turn red on the map → toggle off → segments return to green.

**Relevant Context:**
- `POST /api/scenario/` body: `{"scenario": "flood" | "normal"}`.
- Sample JSON approach: `config.SCENARIO` flag used by `api.js` to choose between normal and flood sample files (or a single file with both scenarios keyed).
- Trip options request shape: `docs/TEAM_BRIEF.md` section 1.10 (origin, destination, depart_at, vehicle_type, cargo object, current_segment_id, scenario).

---

### B4 — Options and ETA Screens
**Status:** `[ ] pending`

**Intent:** render the trip options returned by the backend as clear, scannable cards that show everything a driver needs to decide — ETA range, cargo window pass/fail, trade-offs, and which routes were excluded and why.

**Expected Outcomes:**
- 2-3 option cards rendered from `trip_options.json` / real API response, each showing: type icon, label, ETA range + reason line, distance km, fuel cost INR, cargo-window badge (green "✓ 1.5 h remaining" or red "✗ cargo expires"), trade-off bullets, "Recommended" badge if `recommended: true`.
- `excluded_routes` rendered below the cards: "Main route excluded: contains high-risk segments M-07 and M-11."
- Tapping an option highlights that route on the Leaflet map; other routes dim.
- A mock "Receiver notified of new ETA" confirmation message appears after selection (toast/snackbar, i18n string, disappears after 4 s).
- Empty state: if `options` is empty, show `message` field text prominently (never a crash or blank screen).
- `warnings[]` rendered as yellow notice chips above the cards.

**Todo List:**
1. Write `static/js/options.js` — `renderOptions(response)` builds the card HTML; `onSelectOption(optionId)` highlights the route on the map.
2. Build the options panel HTML container in `map.html`.
3. Add cargo-window badge logic: compare `cargo_window.ok` and `cargo_window.remaining_hours_at_latest_eta`; use i18n keys for text.
4. Wire `trip.js` → `options.js`: after `api.postTripOptions()` resolves, call `renderOptions()`.
5. Implement route-highlight: when an option is selected, `map.js.highlightRoute(routeId)` sets selected route polyline to full opacity, others to 25% opacity.
6. Add "Receiver notified" toast (CSS animation, no library).
7. Add empty-state and warning rendering.
8. Add all new string keys to `en.json` + `ml.json`.
9. Test with `trip_options.json`: verify all 3 card types render; verify empty `options` shows message; verify cargo-window badge is correct.

**Relevant Context:**
- Options response shape: `docs/TEAM_BRIEF.md` section 1.10. `option.type` values: `proceed | reroute | wait | divert_store`.
- `cargo_window`: `{ok: bool, remaining_hours_at_latest_eta: number}`.
- Route highlight: `map.js` must expose a `highlightRoute(routeId)` function callable from `options.js`.

---

### B5 — Service Map
**Status:** `[ ] pending`

**Intent:** add the service-point layer to the map so drivers can find hospitals, fuel, repair etc., ranked by safe reachable time — and flip automatically to emergency mode when needed.

**Expected Outcomes:**
- Service-point markers on the map with category-specific icons (SVG inline icons in `static/vendor/icons/`; no CDN).
- Filter chips (default visible: hospital, fuel, repair, police, safe_halt) — toggling a chip hides/shows that category on both map and list.
- A list-view panel sorted as returned by the API, showing: name, category, `reachable_minutes`, last verified date, and data source. Unreachable points shown in a distinct style with `reason` text ("Not reachable: flooded route between current position and attach segment").
- Emergency mode: a clearly labelled "Emergency" button (and automatic trigger when an SOS alert arrives from D's API) switches to `mode=emergency` — only hospital/police/fire/safe_halt shown; UI turns high-contrast (dark red background, white text, large icons).
- Normal mode restores on a "Cancel emergency" button.
- All strings in i18n files.

**Todo List:**
1. Write `static/js/service.js` — `loadServicePoints(mode, positionSegmentId, vehicleType, scenario)` calls `api.getServicePoints()`, renders markers and list; `setEmergencyMode(bool)` switches layout.
2. Create SVG icons for the 5 default categories (hospital, fuel, repair, police, safe_halt) and place in `static/vendor/icons/`.
3. Build filter chip HTML in `map.html`; wire chips to `service.js` `toggleCategory(cat)`.
4. Build the list-view panel HTML; wire to the same data.
5. Implement emergency mode: `setEmergencyMode(true)` adds `emergency-active` class to `<body>`; CSS re-themes the page (`options.css`).
6. Wire the emergency mode button; also expose `window.triggerEmergencyMode()` so D's station dashboard iframe/postMessage can call it.
7. Add "last verified" display (date string from `service_points.json`).
8. Add unreachable-state styling (`reachable: false` → muted with icon + reason tooltip).
9. Add all new string keys to `en.json` + `ml.json`.
10. Test: normal mode shows all categories; toggling chips hides them; emergency mode hides non-emergency categories and re-themes.

**Relevant Context:**
- Service point object: `docs/TEAM_BRIEF.md` section 1.10. `category` values: hospital, fuel, repair, towing, police, fire, safe_halt, cold_store, food, toilet.
- `mode=emergency` returns only hospital/police/fire/safe_halt — the filter chips are hidden in emergency mode (only these 4 shown).
- D's SOS dashboard may reuse this map component. Expose `triggerEmergencyMode()` on `window` for cross-component communication.

---

### B6 — Language Toggle and PWA / Offline Simulation
**Status:** `[ ] pending`

**Intent:** complete the P1 polish — Malayalam language support, PWA installability, offline resilience, and the sliding-window simulation that demonstrates "keeping only the corridor you still need" — including a unit-tested pure function.

**Expected Outcomes:**
- Language toggle (English / Malayalam) switches all visible strings without page reload using `i18n.js`. Malayalam strings marked "NEEDS NATIVE REVIEW" as a JSON comment or in a companion `ml.notes.json`.
- PWA: `manifest.json`, `sw.js` caches the app shell (HTML, JS, CSS, vendor assets) and the last-fetched API responses per endpoint; an "Offline" banner appears when the network is unavailable; a "Risk data is X h old" note appears when the cached response is older than 1 h.
- `computeWindow(positionKm, segments, retreatBufferKm, aheadKm)` pure function in `window.js`: returns `{kept: segmentId[], released: segmentId[]}`. Default `retreatBufferKm = 25`, `aheadKm = 50` (from `config.js`).
- A UI slider that moves the truck along the route; the map shows kept segments with full opacity and released segments with low opacity; a counter shows "X segments cached".
- Unit tests for `computeWindow` in `static/js/tests/window.test.js` (pure function, no DOM, runnable with any test runner or a simple assertion loop in the browser console).

**Todo List:**
1. Complete `ml.json` — translate all keys from `en.json`; add `"_note": "NEEDS NATIVE REVIEW"` key at top of file.
2. Update `i18n.js` to load either `en.json` or `ml.json` based on `document.documentElement.lang`; wire language toggle button to switch and re-render all `data-i18n` elements.
3. Write `manifest.json` with name, short_name, icons (use existing category icons), start_url, display, background_color, theme_color.
4. Write `sw.js` — cache-first for app shell; network-first with cache fallback for API calls; store `data_timestamp` of last cached response; expose `getDataAge()` to the page.
5. Write `static/js/pwa.js` — register service worker; listen for `offline`/`online` events; show/hide offline banner and stale-data note.
6. Write `computeWindow` in `window.js` as a pure function with JSDoc.
7. Write `window.test.js` — at least 4 test cases: truck at start, truck at middle, truck near end, retreat buffer clips at route start.
8. Build the offline slider UI in `map.html`; wire to `computeWindow` and `map.js.setWindowOpacity(kept, released)`.
9. Add all new i18n keys.
10. Test offline mode: open app, load map, disable network → offline banner appears → map still shows last route with stale-data note.

**Relevant Context:**
- `computeWindow` signature and defaults are specified in `docs/TEAM_BRIEF.md` section B6 (retreatBufferKm = 25, aheadKm configurable).
- Service worker must cache sample JSON files as part of the app shell so the map works with zero network.
- PWA `manifest.json` and `sw.js` must be served from the Django root, not from `/static/` — coordinate with A via `docs/QUESTIONS.md` if the Django `urls.py` doesn't expose them.

---

## Dependencies on Other Members

| Needed from | What | When | Workaround |
|---|---|---|---|
| A | Django skeleton (`manage.py`, settings, static/template config, stub `urls.py`) | Phase 1 | B uses `python -m http.server` to test HTML/JS locally until A's skeleton is on `main` |
| A | `/api/segments/`, `/api/routes/`, `/api/scenario/` | Phase 2 | Sample JSON in `sample/` |
| A | `/api/trip/options/`, `/api/service-points/` | Phase 3 | `sample/trip_options.json`, `sample/service_points.json` |
| A | `/api/fleet/` | Phase 4 (B7) | `sample/fleet.json` |
| C | Verified corridor geometry for `segments.json` | Phase 1 | Use approximate coordinates from section 1.12; mark all geometry `data_source: "simulated"` |
| D | `window.triggerEmergencyMode()` call convention | Phase 3 | Expose on `window`; document in `docs/QUESTIONS.md` |

---

## Questions to log in docs/QUESTIONS.md before starting

1. `[from B to A]` Will `backend/safehaul/settings.py` include `frontend/templates/` in `TEMPLATES DIRS` and `frontend/static/` in `STATICFILES_DIRS`, or should B add a separate Django app for the frontend views? (Blocking: yes for B1)
2. `[from B to A]` The options response has no `route_geometry` field. B will reconstruct the route polyline by cross-referencing `route_id` from `/api/routes/` with segment geometries from `/api/segments/`. Is that the intended pattern? (Blocking: no)
3. `[from B to D]` For the emergency mode trigger, B will expose `window.triggerEmergencyMode(bool)`. Can D call this from the station dashboard (same origin, postMessage, or direct function call)? (Blocking: no)
4. `[from B to E]` Please arrange a native Malayalam speaker to review `static/i18n/ml.json` before the demo. (Blocking: no for build; yes for demo quality)
