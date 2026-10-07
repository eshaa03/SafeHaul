/**
 * SafeHaul Kerala — map module (B1)
 *
 * Responsibilities (B1 scope):
 *   - Initialise a Leaflet map centred on the Palakkad–Kochi corridor.
 *   - Load routes and segments from SafehaulAPI (sample JSON or real).
 *   - Draw route polylines (thin background line per route).
 *   - Draw segment polylines coloured by risk_level.
 *   - Show/hide SIMULATED DATA banner based on data_source.
 *   - Update data-freshness indicator in the header.
 *   - Graceful tile-failure notice.
 *
 * B2 will add: patterns, popups, legend, click handlers.
 * B3 will add: flood toggle, scenario refresh.
 * Public surface used by later modules is noted with @public.
 */

const MapApp = (() => {

  /* ── state ──────────────────────────────────────────────────────────── */
  let _map = null;
  let _segmentLayers = {};   // segment_id → Leaflet polyline
  let _routeLayers = {};     // route id  → Leaflet polyline (background)
  let _segments = [];        // last-loaded segment objects
  let _routes = [];          // last-loaded route objects
  let _loadedAt = null;      // Date of last successful data load

  /* ── Leaflet icon path fix (bundled vendor) ─────────────────────────── */
  function _fixLeafletIconPaths() {
    // Leaflet auto-detects icon paths from its own script tag URL, which
    // fails when the file is served from a custom vendor path.
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconUrl:       '/static/vendor/leaflet/images/marker-icon.png',
      iconRetinaUrl: '/static/vendor/leaflet/images/marker-icon-2x.png',
      shadowUrl:     '/static/vendor/leaflet/images/marker-shadow.png',
    });
  }

  /* ── risk colour ────────────────────────────────────────────────────── */
  function _colourForRisk(level) {
    return SAFEHAUL_CONFIG.RISK_COLOURS[level] || SAFEHAUL_CONFIG.RISK_COLOURS.low;
  }

  /* ── simulated-data banner ──────────────────────────────────────────── */
  function _updateSimulatedBanner(dataItems) {
    // dataItems: array of objects that may have a data_source field.
    var hasSimulated = dataItems.some(function (item) {
      return item && item.data_source === 'simulated';
    });
    if (hasSimulated) {
      document.body.classList.add('simulated-active');
    }
    // We never remove the banner once shown — simulated data stays flagged.
  }

  /* ── data-freshness indicator ───────────────────────────────────────── */
  function _updateFreshness() {
    var el = document.getElementById('data-freshness');
    if (!el || !_loadedAt) return;
    var minutesAgo = Math.round((Date.now() - _loadedAt) / 60000);
    var label = t('header.data_freshness') + ' ' + minutesAgo + ' min ' + t('header.data_ago');
    el.textContent = label;
  }

  /* ── tile-failure handling ──────────────────────────────────────────── */
  function _handleTileError() {
    var notice = document.getElementById('map-no-tiles');
    if (notice) notice.hidden = false;
  }

  /* ── draw routes (background polylines) ────────────────────────────── */
  function _drawRoutes(routes) {
    // Build a lookup: segment_id → geometry from already-loaded segments
    var geomMap = {};
    _segments.forEach(function (seg) {
      geomMap[seg.segment_id] = seg.geometry;
    });

    routes.forEach(function (route) {
      // Concatenate all segment geometries in order
      var latlngs = [];
      (route.segment_ids || []).forEach(function (sid) {
        var geom = geomMap[sid];
        if (geom) latlngs = latlngs.concat(geom);
      });
      if (!latlngs.length) return;

      var poly = L.polyline(latlngs, {
        color: '#94a3b8',    // slate-400 background line
        weight: 8,
        opacity: 0.25,
        className: 'route-line route-line--' + route.id,
      }).addTo(_map);

      poly.bindTooltip(route.name || route.id, { sticky: true, direction: 'top' });
      _routeLayers[route.id] = poly;
    });
  }

  /* ── draw segments (risk-coloured polylines) ────────────────────────── */
  function _drawSegments(segments) {
    segments.forEach(function (seg) {
      if (!seg.geometry || !seg.geometry.length) return;

      var colour = _colourForRisk(seg.risk_level);
      var poly = L.polyline(seg.geometry, {
        color: colour,
        weight: SAFEHAUL_CONFIG.RISK_WEIGHT,
        opacity: 0.90,
        className: 'segment-line segment-line--' + seg.risk_level,
      }).addTo(_map);

      // Minimal tooltip for B1 — B2 will replace with full popup panel.
      var riskLabel = t('risk.' + seg.risk_level) || seg.risk_level;
      poly.bindTooltip(
        '<strong>' + seg.name + '</strong><br>' + riskLabel,
        { sticky: true, direction: 'top' }
      );

      _segmentLayers[seg.segment_id] = poly;
    });
  }

  /* ── load and render ────────────────────────────────────────────────── */
  async function _load() {
    var loadingEl = document.getElementById('map-loading');

    try {
      // Fetch routes and segments in parallel.
      var [routes, segments] = await Promise.all([
        SafehaulAPI.getRoutes(),
        SafehaulAPI.getSegments(),
      ]);

      _routes   = Array.isArray(routes)   ? routes   : [];
      _segments = Array.isArray(segments) ? segments : [];
      _loadedAt = Date.now();

      // Draw routes first (background), then segments on top.
      _drawRoutes(_routes);
      _drawSegments(_segments);

      // Update simulated banner and freshness.
      _updateSimulatedBanner(_segments);
      _updateFreshness();

    } catch (err) {
      console.error('[map] load failed:', err);
      if (loadingEl) loadingEl.textContent = t('map.load_error');
      return;
    }

    // Hide loading overlay once data is drawn.
    if (loadingEl) loadingEl.hidden = true;
  }

  /* ── public API ─────────────────────────────────────────────────────── */

  /**
   * @public
   * Initialise the map. Called from map.html once the DOM is ready.
   */
  function init() {
    _fixLeafletIconPaths();

    _map = L.map('map', {
      center: SAFEHAUL_CONFIG.MAP_CENTER,
      zoom:   SAFEHAUL_CONFIG.MAP_ZOOM,
      minZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MIN,
      maxZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MAX,
      zoomControl: true,
    });

    // Tile layer — OSM; detect failures for the no-tile notice.
    var tileLayer = L.tileLayer(SAFEHAUL_CONFIG.TILE_URL, {
      attribution: SAFEHAUL_CONFIG.TILE_ATTRIBUTION,
      maxZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MAX,
    });
    tileLayer.on('tileerror', _handleTileError);
    tileLayer.addTo(_map);

    // Kick off data load.
    _load();

    // Refresh freshness label every minute.
    setInterval(_updateFreshness, 60000);
  }

  /**
   * @public — used by B3 to reload after scenario change.
   * Clears all drawn layers and re-fetches from the API.
   */
  function reload() {
    Object.values(_segmentLayers).forEach(function (p) { _map.removeLayer(p); });
    Object.values(_routeLayers).forEach(function (p)  { _map.removeLayer(p); });
    _segmentLayers = {};
    _routeLayers   = {};
    _segments      = [];
    _routes        = [];
    _load();
  }

  /**
   * @public — used by B4 to highlight a selected route.
   * routeId: string matching route.id in routes.json.
   */
  function highlightRoute(routeId) {
    Object.entries(_routeLayers).forEach(function ([id, poly]) {
      poly.setStyle({ opacity: id === routeId ? 0.8 : 0.1 });
    });
    Object.entries(_segmentLayers).forEach(function ([sid, poly]) {
      // Find the segment to check which routes it belongs to.
      var seg = _segments.find(function (s) { return s.segment_id === sid; });
      var onSelectedRoute = seg && seg.route_ids && seg.route_ids.includes(routeId);
      poly.setStyle({ opacity: onSelectedRoute ? 0.9 : 0.25 });
    });
  }

  /**
   * @public — used by B6 for offline window simulation.
   */
  function setWindowOpacity(keptIds, releasedIds) {
    var keptSet = new Set(keptIds);
    Object.entries(_segmentLayers).forEach(function ([sid, poly]) {
      poly.setStyle({ opacity: keptSet.has(sid) ? 0.9 : 0.2 });
    });
  }

  return { init, reload, highlightRoute, setWindowOpacity };

})();
