/**
 * SafeHaul Kerala — frontend configuration
 * All tunable constants live here. Never hard-code these values elsewhere.
 *
 * To switch from sample JSON to the real Django API, set USE_REAL_API = true.
 * The sample files in static/sample/ exactly mirror the API contract in
 * docs/TEAM_BRIEF.md section 1.10.
 */

const SAFEHAUL_CONFIG = Object.freeze({

  /* ── API mode ──────────────────────────────────────────────────────────── */
  USE_REAL_API: true,           // tries real API first; falls back to sample JSON on failure
  API_BASE: '/api',             // Django API root; no trailing slash

  /* ── Scenario ──────────────────────────────────────────────────────────── */
  // Active scenario used when USE_REAL_API = false.
  // Toggled at runtime by the flood switch; do not read this directly from
  // other modules — use api.getScenario() so the live path also works.
  _scenario: 'normal',          // 'normal' | 'flood'

  /* ── Sample-JSON paths (relative to window.location) ───────────────────── */
  SAMPLE: {
    segments:      '/static/sample/segments.json',
    routes:        '/static/sample/routes.json',
    scenario:      '/static/sample/scenario.json',
    trip_options:  '/static/sample/trip_options.json',
    service_points:'/static/sample/service_points.json',
    fleet:         '/static/sample/fleet.json',
  },

  /* ── Map defaults ──────────────────────────────────────────────────────── */
  MAP_CENTER: [10.35, 76.40],   // [lat, lng] centred on Palakkad–Kochi corridor
  MAP_ZOOM: 9,
  MAP_ZOOM_MIN: 7,
  MAP_ZOOM_MAX: 16,
  TILE_URL: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  TILE_ATTRIBUTION: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',

  /* ── Risk colours (used by map.js; full pattern styling is in B2) ───────── */
  RISK_COLOURS: {
    low:    '#22c55e',   // green
    medium: '#f59e0b',   // amber
    high:   '#ef4444',   // red
    closed: '#1f2328',   // near-black
  },
  RISK_WEIGHT: 5,        // polyline stroke width (px)

  /* ── Demo scenario defaults (prefill for trip form in B3) ──────────────── */
  DEMO: {
    origin:             'Palakkad',
    destination:        'Kochi',
    depart_at:          '2026-10-08T06:00:00+05:30',
    vehicle_type:       'lcv',
    cargo_type:         'vegetables',
    cargo_weight_kg:    5000,
    cargo_shelf_life_h: 8,
    cargo_value_inr:    250000,
  },

  /* ── Offline sliding window defaults (B6) ───────────────────────────────── */
  WINDOW_RETREAT_KM: 25,
  WINDOW_AHEAD_KM:   50,

  /* ── Timing ─────────────────────────────────────────────────────────────── */
  STALE_DATA_WARN_MINUTES: 60,  // show stale-data warning after this many minutes
});
