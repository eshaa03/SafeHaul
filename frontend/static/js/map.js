/**
 * SafeHaul Kerala — map module
 *
 * Responsibilities:
 *   - Leaflet map init centred on Palakkad–Kochi corridor.
 *   - Draw route polylines (background) and risk-coloured+patterned segment polylines.
 *   - Segment click → open detail panel (risk, reasons, confidence, data age, source).
 *   - Flood toggle: POST /api/scenario/ then reload all data.
 *   - SIMULATED DATA banner, data-freshness indicator, tile-failure notice.
 *
 * Public API used by other modules:
 *   MapApp.init()
 *   MapApp.reload()
 *   MapApp.highlightRoute(routeId)
 *   MapApp.setWindowOpacity(keptIds, releasedIds)
 */

const MapApp = (() => {

  /* ── state ──────────────────────────────────────────────────────────── */
  let _map          = null;
  let _segmentLayers = {};    // segment_id → Leaflet polyline
  let _routeLayers   = {};    // route id   → Leaflet polyline (background)
  let _segments      = [];
  let _routes        = [];
  let _loadedAt      = null;
  let _isFlood       = false;

  /* ── Leaflet icon fix ────────────────────────────────────────────────── */
  function _fixLeafletIconPaths() {
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconUrl:       '/static/vendor/leaflet/images/marker-icon.png',
      iconRetinaUrl: '/static/vendor/leaflet/images/marker-icon-2x.png',
      shadowUrl:     '/static/vendor/leaflet/images/marker-shadow.png',
    });
  }

  /* ── simulated banner ────────────────────────────────────────────────── */
  function _updateSimulatedBanner(items) {
    var hasSim = items.some(function (x) { return x && x.data_source === 'simulated'; });
    if (hasSim) document.body.classList.add('simulated-active');
  }

  /* ── freshness indicator ─────────────────────────────────────────────── */
  function _updateFreshness() {
    var el = document.getElementById('data-freshness');
    if (!el || !_loadedAt) return;
    var mins = Math.round((Date.now() - _loadedAt) / 60000);
    el.textContent = t('header.data_freshness') + ' ' + mins + ' min ' + t('header.data_ago');
  }

  /* ── tile error ──────────────────────────────────────────────────────── */
  function _handleTileError() {
    var n = document.getElementById('map-no-tiles');
    if (n) n.hidden = false;
  }

  /* ── segment panel ───────────────────────────────────────────────────── */
  function _openSegmentPanel(seg) {
    var container = document.getElementById('seg-panel-container');
    if (!container) return;
    container.innerHTML = Risk.renderSegmentPanel(seg);
    container.hidden = false;
    var closeBtn = document.getElementById('seg-panel-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        container.hidden = true;
      });
    }
  }

  /* ── draw routes ─────────────────────────────────────────────────────── */
  function _drawRoutes(routes) {
    var geomMap = {};
    _segments.forEach(function (s) { geomMap[s.segment_id] = s.geometry; });

    routes.forEach(function (route) {
      var latlngs = [];
      (route.segment_ids || []).forEach(function (sid) {
        var g = geomMap[sid];
        if (g) latlngs = latlngs.concat(g);
      });
      if (!latlngs.length) return;

      var poly = L.polyline(latlngs, {
        color: '#94a3b8', weight: 10, opacity: 0.20,
        className: 'route-line route-line--' + route.id,
      }).addTo(_map);
      poly.bindTooltip(route.name || route.id, { sticky: true, direction: 'top' });
      _routeLayers[route.id] = poly;
    });
  }

  /* ── draw segments ───────────────────────────────────────────────────── */
  function _drawSegments(segments) {
    segments.forEach(function (seg) {
      if (!seg.geometry || !seg.geometry.length) return;

      var style = Risk.styleForRisk(seg);
      style.className = 'segment-line segment-line--' + seg.risk_level;
      var poly = L.polyline(seg.geometry, style).addTo(_map);

      // Hover tooltip (quick label)
      var icon  = Risk.ICONS[seg.risk_level] || '●';
      var label = t('risk.' + seg.risk_level) || seg.risk_level;
      poly.bindTooltip(
        '<span style="font-size:1.1em">' + icon + '</span> ' +
        '<strong>' + seg.name + '</strong><br>' + label,
        { sticky: true, direction: 'top' }
      );

      // Click → full detail panel
      poly.on('click', function () { _openSegmentPanel(seg); });

      _segmentLayers[seg.segment_id] = poly;
    });
  }

  /* ── load & render ───────────────────────────────────────────────────── */
  async function _load() {
    var loadingEl = document.getElementById('map-loading');

    try {
      var [routes, segments] = await Promise.all([
        SafehaulAPI.getRoutes(),
        SafehaulAPI.getSegments(),
      ]);

      _routes   = Array.isArray(routes)   ? routes   : [];
      _segments = Array.isArray(segments) ? segments : [];
      _loadedAt = Date.now();

      _drawRoutes(_routes);
      _drawSegments(_segments);
      _updateSimulatedBanner(_segments);
      _updateFreshness();

    } catch (err) {
      console.error('[map] load failed:', err);
      if (loadingEl) loadingEl.textContent = t('map.load_error');
      return;
    }

    if (loadingEl) loadingEl.hidden = true;
  }

  /* ── flood toggle ────────────────────────────────────────────────────── */
  async function _toggleFlood() {
    var btn = document.getElementById('flood-toggle');
    _isFlood = !_isFlood;
    var scenario = _isFlood ? 'flood' : 'normal';

    document.body.dataset.scenario = scenario;

    if (btn) {
      btn.setAttribute('aria-pressed', String(_isFlood));
      btn.classList.toggle('flood-toggle--active', _isFlood);
      btn.textContent = _isFlood ? '🌊 ' + t('flood.on') : '☀ ' + t('flood.off');
    }

    try {
      await SafehaulAPI.setScenario(scenario);
    } catch (_) {}

    reload();

    // Refresh hospitals and auto-run trip options on flood change
    Service.loadHospitals({ scenario: scenario });
  }

  /* ── public ──────────────────────────────────────────────────────────── */

  function init() {
    _fixLeafletIconPaths();

    _map = L.map('map', {
      center:  SAFEHAUL_CONFIG.MAP_CENTER,
      zoom:    SAFEHAUL_CONFIG.MAP_ZOOM,
      minZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MIN,
      maxZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MAX,
    });

    var tileLayer = L.tileLayer(SAFEHAUL_CONFIG.TILE_URL, {
      attribution: SAFEHAUL_CONFIG.TILE_ATTRIBUTION,
      maxZoom: SAFEHAUL_CONFIG.MAP_ZOOM_MAX,
    });
    tileLayer.on('tileerror', _handleTileError);
    tileLayer.addTo(_map);

    _load();
    setInterval(_updateFreshness, 60000);

    // Flood toggle button
    var btn = document.getElementById('flood-toggle');
    if (btn) btn.addEventListener('click', _toggleFlood);
  }

  function reload() {
    Object.values(_segmentLayers).forEach(function (p) { _map.removeLayer(p); });
    Object.values(_routeLayers).forEach(function (p)  { _map.removeLayer(p); });
    _segmentLayers = {};
    _routeLayers   = {};
    _segments      = [];
    _routes        = [];
    // Close any open segment panel
    var panel = document.getElementById('seg-panel-container');
    if (panel) panel.hidden = true;
    _load();
  }

  function highlightRoute(routeId) {
    Object.entries(_routeLayers).forEach(function ([id, poly]) {
      poly.setStyle({ opacity: id === routeId ? 0.7 : 0.08 });
    });
    Object.entries(_segmentLayers).forEach(function ([sid, poly]) {
      var seg = _segments.find(function (s) { return s.segment_id === sid; });
      var onRoute = seg && seg.route_ids && seg.route_ids.includes(routeId);
      poly.setStyle({ opacity: onRoute ? 0.95 : 0.20 });
    });
  }

  function setWindowOpacity(keptIds, releasedIds) {
    var kept = new Set(keptIds);
    Object.entries(_segmentLayers).forEach(function ([sid, poly]) {
      poly.setStyle({ opacity: kept.has(sid) ? 0.95 : 0.18 });
    });
  }

  return { init, reload, highlightRoute, setWindowOpacity };

})();
