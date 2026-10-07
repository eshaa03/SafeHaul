/**
 * SafeHaul Kerala — API client
 *
 * Each function has two paths:
 *   1. SAFEHAUL_CONFIG.USE_REAL_API = false  → fetch sample JSON file
 *   2. USE_REAL_API = true                   → call the real Django endpoint,
 *      with automatic fallback to sample JSON on network/server error.
 *
 * All functions return a Promise that resolves to the parsed JSON object.
 * On unrecoverable failure they resolve to null and log to console.error.
 */

/* ── internal helpers ──────────────────────────────────────────────────── */

async function _fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${url}`);
  return res.json();
}

async function _withFallback(realUrl, sampleKey) {
  const sampleUrl = SAFEHAUL_CONFIG.SAMPLE[sampleKey];
  if (!SAFEHAUL_CONFIG.USE_REAL_API) {
    return _fetchJSON(sampleUrl);
  }
  try {
    return await _fetchJSON(realUrl);
  } catch (err) {
    console.warn(`[api] real endpoint failed (${realUrl}): ${err.message} — falling back to sample`);
    return _fetchJSON(sampleUrl);
  }
}

/* ── scenario helpers ──────────────────────────────────────────────────── */

/** Returns the current scenario string ('normal' | 'flood'). */
function _currentScenario() {
  return SAFEHAUL_CONFIG._scenario;
}

/** Update the in-memory scenario (used when USE_REAL_API = false). */
function _setScenario(scenario) {
  // SAFEHAUL_CONFIG is frozen but _scenario is the one mutable path we need;
  // we work around the freeze by keeping it on the object before the freeze.
  // Since config.js already assigns _scenario as a regular property before
  // Object.freeze() the assignment below must happen via Object.defineProperty.
  Object.defineProperty(SAFEHAUL_CONFIG, '_scenario', { value: scenario, writable: true, configurable: true });
}

/* ── public API ────────────────────────────────────────────────────────── */

const SafehaulAPI = {

  /**
   * GET /api/scenario/
   * Returns {scenario, data_source}
   */
  getScenario() {
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      return Promise.resolve({ scenario: _currentScenario(), data_source: 'simulated' });
    }
    return _withFallback(`${SAFEHAUL_CONFIG.API_BASE}/scenario/`, 'scenario');
  },

  /**
   * POST /api/scenario/  body: {scenario}
   * Switches the server-wide scenario; returns the new scenario object.
   */
  async setScenario(scenario) {
    _setScenario(scenario);
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      return { scenario, data_source: 'simulated' };
    }
    try {
      const res = await fetch(`${SAFEHAUL_CONFIG.API_BASE}/scenario/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (err) {
      console.warn(`[api] setScenario failed: ${err.message}`);
      return { scenario, data_source: 'simulated' };
    }
  },

  /**
   * GET /api/segments/?scenario=
   * Returns array of segment objects.
   */
  getSegments(scenario) {
    const sc = scenario || _currentScenario();
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      // Sample file contains all segments; flood risk_levels are pre-set in the
      // flood-scenario entries. When the scenario is 'normal', high-risk segments
      // are not present in the normal sample. For now the single segments.json
      // represents the flood state; B3 will extend this to swap per scenario.
      return _fetchJSON(SAFEHAUL_CONFIG.SAMPLE.segments);
    }
    return _withFallback(`${SAFEHAUL_CONFIG.API_BASE}/segments/?scenario=${sc}`, 'segments');
  },

  /**
   * GET /api/routes/
   * Returns array of route objects.
   */
  getRoutes() {
    return _withFallback(`${SAFEHAUL_CONFIG.API_BASE}/routes/`, 'routes');
  },

  /**
   * POST /api/trip/options/  body: TripRequest object
   * Returns trip options response.
   */
  async postTripOptions(requestBody) {
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      return _fetchJSON(SAFEHAUL_CONFIG.SAMPLE.trip_options);
    }
    try {
      const res = await fetch(`${SAFEHAUL_CONFIG.API_BASE}/trip/options/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (err) {
      console.warn(`[api] postTripOptions failed: ${err.message} — using sample`);
      return _fetchJSON(SAFEHAUL_CONFIG.SAMPLE.trip_options);
    }
  },

  /**
   * GET /api/service-points/?mode=&position_segment_id=&vehicle_type=&scenario=
   * Returns array of service point objects.
   */
  getServicePoints({ mode = 'normal', positionSegmentId = null, vehicleType = null, scenario = null } = {}) {
    const sc = scenario || _currentScenario();
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      return _fetchJSON(SAFEHAUL_CONFIG.SAMPLE.service_points);
    }
    const params = new URLSearchParams({ mode, scenario: sc });
    if (positionSegmentId) params.set('position_segment_id', positionSegmentId);
    if (vehicleType) params.set('vehicle_type', vehicleType);
    return _withFallback(`${SAFEHAUL_CONFIG.API_BASE}/service-points/?${params}`, 'service_points');
  },

  /**
   * GET /api/fleet/?scenario=
   * Returns array of fleet vehicle objects.
   */
  getFleet(scenario) {
    const sc = scenario || _currentScenario();
    return _withFallback(`${SAFEHAUL_CONFIG.API_BASE}/fleet/?scenario=${sc}`, 'fleet');
  },

  /**
   * GET /api/rainfall/?lat=&lng=
   * Returns rainfall data (owned by C).
   */
  getRainfall(lat, lng) {
    // No sample file for rainfall; return a minimal mock inline.
    if (!SAFEHAUL_CONFIG.USE_REAL_API) {
      return Promise.resolve({
        lat, lng,
        rain_24h_mm: 88,
        forecast_3h_mm: 12,
        data_source: 'simulated',
        data_timestamp: new Date().toISOString(),
      });
    }
    return _fetchJSON(`${SAFEHAUL_CONFIG.API_BASE}/rainfall/?lat=${lat}&lng=${lng}`);
  },
};
