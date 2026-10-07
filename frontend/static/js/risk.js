/**
 * SafeHaul Kerala — risk styling and segment popup
 *
 * Provides:
 *   styleForRisk(segment)      → Leaflet polyline options (colour + dashArray for pattern)
 *   renderSegmentPanel(segment) → HTML string for the segment detail panel
 */

const Risk = (() => {

  /* ── Leaflet polyline styles ─────────────────────────────────────────── */

  const STYLES = {
    low: {
      color:     '#22c55e',
      weight:    6,
      opacity:   0.92,
      dashArray: null,          // solid
    },
    medium: {
      color:     '#f59e0b',
      weight:    6,
      opacity:   0.92,
      dashArray: '10 5',        // dashed — visible pattern without extra library
    },
    high: {
      color:     '#ef4444',
      weight:    7,
      opacity:   0.95,
      dashArray: '4 4',         // short dashes
    },
    closed: {
      color:     '#1f2328',
      weight:    7,
      opacity:   1.0,
      dashArray: '2 6',         // dot-dash
    },
  };

  /** SVG icon badge shown alongside the risk label (colour-blind safe). */
  const ICONS = {
    low:    '&#9679;',   // ● filled circle
    medium: '&#9650;',   // ▲ triangle
    high:   '&#9632;',   // ■ square
    closed: '&#10005;',  // ✕ cross
  };

  function styleForRisk(segment) {
    return Object.assign({}, STYLES[segment.risk_level] || STYLES.low);
  }

  /* ── Data-age helper ─────────────────────────────────────────────────── */

  function _dataAge(isoTimestamp) {
    if (!isoTimestamp) return t('risk.updated_label') + ': —';
    var then = new Date(isoTimestamp);
    var diffMs = Date.now() - then.getTime();
    if (isNaN(diffMs)) return t('risk.updated_label') + ': —';
    var mins = Math.round(diffMs / 60000);
    if (mins < 1)   return t('risk.updated_label') + ': ' + t('header.data_ago') + ' <1 min';
    if (mins < 60)  return t('risk.updated_label') + ': ' + mins + ' min ' + t('header.data_ago');
    var hrs = Math.round(mins / 60);
    return t('risk.updated_label') + ': ' + hrs + ' h ' + t('header.data_ago');
  }

  /* ── Segment detail panel HTML ───────────────────────────────────────── */

  function _confidenceLabel(c) {
    if (c === 'high')     return t('risk.confidence_high');
    if (c === 'moderate') return t('risk.confidence_moderate');
    return t('risk.confidence_low');
  }

  function _sourceLabel(s) {
    if (s === 'live')       return t('header.data_source_live');
    if (s === 'simulated')  return t('header.data_source_simulated');
    return t('header.data_source_historical');
  }

  function renderSegmentPanel(seg) {
    var level     = seg.risk_level || 'low';
    var score     = typeof seg.risk_score === 'number' ? (seg.risk_score * 100).toFixed(0) + '%' : '—';
    var icon      = ICONS[level] || ICONS.low;
    var riskLabel = t('risk.' + level + '_with_confidence')
                      .replace('{confidence}', _confidenceLabel(seg.confidence));
    var reasons   = Array.isArray(seg.reasons) ? seg.reasons : [];
    var ageStr    = _dataAge(seg.data_timestamp);
    var srcStr    = _sourceLabel(seg.data_source);
    var clearsHtml = '';
    if (seg.clears_in_hours) {
      clearsHtml = '<p class="seg-panel__clears">' +
        t('risk.clears_in') + ' <strong>' + seg.clears_in_hours + '</strong> ' + t('risk.clears_hours') +
        '</p>';
    }

    var reasonsHtml = reasons.length
      ? '<ul class="seg-panel__reasons">' +
          reasons.map(function (r) { return '<li>' + _esc(r) + '</li>'; }).join('') +
        '</ul>'
      : '';

    return (
      '<div class="seg-panel" data-risk="' + level + '">' +
        '<div class="seg-panel__header">' +
          '<span class="seg-panel__icon risk-icon--' + level + '" aria-hidden="true">' + icon + '</span>' +
          '<div>' +
            '<div class="seg-panel__name">' + _esc(seg.name) + '</div>' +
            '<div class="seg-panel__risk-label">' + riskLabel + '</div>' +
          '</div>' +
          '<button class="seg-panel__close" id="seg-panel-close" aria-label="Close">&#10005;</button>' +
        '</div>' +
        '<div class="seg-panel__score">' + t('risk.score_label') + ': <strong>' + score + '</strong></div>' +
        '<div class="seg-panel__section-label">' + t('risk.reasons_label') + '</div>' +
        reasonsHtml +
        clearsHtml +
        '<div class="seg-panel__meta">' +
          '<span class="seg-panel__age">' + ageStr + '</span>' +
          '<span class="seg-panel__source">' + t('risk.data_source_label') + ': ' + srcStr + '</span>' +
        '</div>' +
      '</div>'
    );
  }

  function _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  return { styleForRisk, renderSegmentPanel, ICONS };

})();
