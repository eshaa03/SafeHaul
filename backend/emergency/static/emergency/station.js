/* SafeHaul Kerala — Station Dashboard JS
   Polls GET /api/emergency/?since= every 2 s.
   Renders event cards. Plays a Web Audio beep on new events (no audio file, no CDN).
   Sends POST /api/emergency/<id>/ack/ when operator clicks Acknowledge.
   Works fully offline — no external resources.
   -------------------------------------------------------------------- */

(function () {
  'use strict';

  // ---- State ----
  var lastTs = new Date(0).toISOString();  // ISO string, updated after each poll
  var knownIds = {};      // id → true, prevents re-rendering known events
  var maps = {};          // id → Leaflet map instance (if Leaflet available)

  // CODES is injected by the Django template: var CODES = {...};
  // severity map for CSS class
  var SEV = { critical: 'sev-critical', high: 'sev-high', medium: 'sev-medium', low: 'sev-low' };

  // ---- Web Audio beep (no file, no CDN) ----
  var audioCtx = null;
  function beep() {
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.frequency.value = 880;   // A5 — loud, cuts through noise
      gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.6);
    } catch (e) { /* Audio not available — fail silently */ }
  }

  // ---- DOM helpers ----
  function el(id) { return document.getElementById(id); }

  function setConnStatus(ok) {
    var s = el('conn-status');
    if (!s) return;
    s.textContent = ok ? '● Connected' : '● Disconnected';
    s.className = 'conn-status ' + (ok ? 'ok' : 'err');
  }

  function codeInfo(code) {
    return CODES[code] || { en: 'Unknown code ' + code, severity: 'medium', ml: '' };
  }

  // ---- Render one event card ----
  function renderCard(ev) {
    var info   = codeInfo(ev.code);
    var sevCls = SEV[info.severity] || 'sev-medium';
    var isNew  = ev.status === 'new';
    var isSim  = ev.via === 'sim';

    var ts = ev.device_ts
      ? new Date(ev.device_ts).toLocaleTimeString()
      : new Date(ev.received_at).toLocaleTimeString();

    var card = document.createElement('div');
    card.className = 'event-card ' + sevCls + (isNew ? ' new' : '');
    card.id = 'card-' + ev.id;
    card.dataset.seq = ev.seq;

    var actionHtml = isNew
      ? '<button class="ack-btn" onclick="ackEvent(' + ev.id + ', this)">Acknowledge</button>'
      : '<span class="ack-badge">✓ Acknowledged' +
          (ev.acked_at ? ' ' + new Date(ev.acked_at).toLocaleTimeString() : '') +
        '</span>';

    var simLabel = isSim
      ? '<span class="event-via-sim"> [SIMULATED RADIO LINK]</span>'
      : '';

    card.innerHTML =
      '<div>' +
        '<div class="event-code">' + ev.code + ' — ' +
          '<span class="event-meaning">' + info.en + '</span>' +
          simLabel +
        '</div>' +
        '<div class="event-meta">' +
          'Vehicle ' + ev.vehicle_id + ' &nbsp;·&nbsp; ' +
          'Seq ' + ev.seq + ' &nbsp;·&nbsp; ' +
          ts + ' &nbsp;·&nbsp; ' +
          ev.lat.toFixed(4) + ', ' + ev.lng.toFixed(4) +
        '</div>' +
        '<div style="margin-top:8px">' + actionHtml + '</div>' +
      '</div>' +
      '<div class="event-map" id="map-' + ev.id + '">map</div>';

    return card;
  }

  // ---- Build Leaflet mini-map for one card ----
  function buildMap(ev) {
    if (typeof L === 'undefined' || !L) return;   // Leaflet not loaded — skip
    var container = el('map-' + ev.id);
    if (!container || maps[ev.id]) return;
    container.textContent = '';  // clear placeholder text
    try {
      var m = L.map(container, { zoomControl: false, attributionControl: false });
      L.tileLayer('', {}).addTo(m);  // blank tile (no internet tiles needed for demo)
      var latlng = [ev.lat, ev.lng];
      m.setView(latlng, 13);
      L.circleMarker(latlng, {
        radius: 8, color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.9
      }).addTo(m).bindTooltip('Vehicle ' + ev.vehicle_id, { permanent: true });
      maps[ev.id] = m;
    } catch (e) { container.textContent = ev.lat.toFixed(4) + ', ' + ev.lng.toFixed(4); }
  }

  // ---- Process poll results ----
  function processEvents(events) {
    if (!events.length) return;

    var list    = el('event-list');
    var emptyEl = el('empty-msg');
    var anyNew  = false;
    var hasSimEvent = false;

    events.forEach(function (ev) {
      if (ev.via === 'sim') hasSimEvent = true;

      if (knownIds[ev.id]) {
        // Update status on existing card if it changed (e.g. got acked from /sos-demo/)
        var card = el('card-' + ev.id);
        if (card && ev.status === 'acked') {
          card.classList.remove('new');
          var btn = card.querySelector('.ack-btn');
          if (btn) {
            var ackTs = ev.acked_at ? new Date(ev.acked_at).toLocaleTimeString() : '';
            btn.outerHTML =
              '<span class="ack-badge">✓ Acknowledged ' + ackTs + '</span>';
          }
        }
        return;
      }

      // New event
      knownIds[ev.id] = true;
      anyNew = true;

      if (emptyEl) { emptyEl.style.display = 'none'; }

      var card = renderCard(ev);
      // Prepend (newest first)
      if (list.firstChild && list.firstChild.id !== 'empty-msg') {
        list.insertBefore(card, list.firstChild);
      } else {
        list.appendChild(card);
      }
      buildMap(ev);
    });

    if (anyNew) beep();

    // Show/hide SIM banner
    var banner = el('sim-banner');
    if (banner) banner.hidden = !hasSimEvent;

    // Update lastTs to the most recent received_at seen
    var maxTs = events.reduce(function (acc, ev) {
      return ev.received_at > acc ? ev.received_at : acc;
    }, lastTs);
    lastTs = maxTs;
  }

  // ---- Acknowledge button handler (global so onclick= works) ----
  window.ackEvent = function (eventId, btnEl) {
    btnEl.disabled = true;
    btnEl.textContent = 'Acknowledging…';
    fetch('/api/emergency/' + eventId + '/ack/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ acked_by: 'station' })
    })
    .then(function (r) { return r.json(); })
    .then(function (ev) {
      var card = el('card-' + eventId);
      if (card) {
        card.classList.remove('new');
        var ackTs = ev.acked_at ? new Date(ev.acked_at).toLocaleTimeString() : '';
        btnEl.outerHTML =
          '<span class="ack-badge">✓ Acknowledged ' + ackTs + '</span>';
      }
    })
    .catch(function () {
      btnEl.disabled = false;
      btnEl.textContent = 'Acknowledge';
    });
  };

  // ---- Poll loop ----
  function poll() {
    fetch('/api/emergency/?since=' + encodeURIComponent(lastTs))
      .then(function (r) {
        setConnStatus(true);
        return r.json();
      })
      .then(processEvents)
      .catch(function () { setConnStatus(false); });
  }

  // Start polling immediately, then every 2 s
  poll();
  setInterval(poll, 2000);

}());
