/**
 * SafeHaul Kerala — options panel module
 *
 * Renders 2-3 route option cards from the /api/trip/options/ response.
 * Each card shows: type icon, label, ETA range + reason, distance, fuel cost,
 * cargo-window pass/fail badge, trade-offs, Recommended badge.
 * Also renders excluded_routes and warnings.
 */

const Options = (() => {

  const TYPE_ICONS = {
    proceed:      '✅',
    reroute:      '↪',
    wait:         '⏳',
    divert_store: '🏪',
  };

  function _esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function _fmtTime(iso) {
    if (!iso) return '—';
    try {
      var d = new Date(iso);
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch (_) { return iso; }
  }

  function _cargoWindowBadge(cw) {
    if (!cw) return '';
    if (cw.ok) {
      var hrs = typeof cw.remaining_hours_at_latest_eta === 'number'
        ? cw.remaining_hours_at_latest_eta.toFixed(1)
        : '?';
      return '<span class="cargo-badge cargo-badge--ok">' +
        t('options.cargo_ok').replace('{hours}', hrs) + '</span>';
    }
    return '<span class="cargo-badge cargo-badge--fail">' + t('options.cargo_fail') + '</span>';
  }

  function _optionCard(opt) {
    var icon      = TYPE_ICONS[opt.type] || '→';
    var recBadge  = opt.recommended
      ? '<span class="opt-badge opt-badge--rec">' + t('options.recommended') + '</span>' : '';
    var typeLabel = t('options.type_' + opt.type) || opt.type;
    var etaEarliest = opt.eta ? _fmtTime(opt.eta.earliest) : '—';
    var etaLatest   = opt.eta ? _fmtTime(opt.eta.latest)   : '—';
    var etaReason   = opt.eta && opt.eta.reason ? _esc(opt.eta.reason) : '';
    var cwBadge     = _cargoWindowBadge(opt.cargo_window);
    var tradeoffs   = Array.isArray(opt.trade_offs) ? opt.trade_offs : [];
    var toHtml      = tradeoffs.length
      ? '<ul class="opt-tradeoffs">' +
          tradeoffs.map(function (x) { return '<li>' + _esc(x) + '</li>'; }).join('') +
        '</ul>'
      : '';

    return (
      '<div class="opt-card' + (opt.recommended ? ' opt-card--rec' : '') + '"' +
          ' data-route-id="' + _esc(opt.route_id || '') + '"' +
          ' role="button" tabindex="0">' +
        '<div class="opt-card__header">' +
          '<span class="opt-card__icon" aria-hidden="true">' + icon + '</span>' +
          '<div class="opt-card__title">' +
            '<div class="opt-card__type">' + typeLabel + '</div>' +
            '<div class="opt-card__label">' + _esc(opt.label) + '</div>' +
          '</div>' +
          recBadge +
        '</div>' +
        '<div class="opt-card__eta">' +
          '<span class="opt-eta-range">' + etaEarliest + ' – ' + etaLatest + '</span>' +
          (etaReason ? '<div class="opt-eta-reason">' + etaReason + '</div>' : '') +
        '</div>' +
        '<div class="opt-card__stats">' +
          '<span>' + (opt.distance_km || '—') + ' km</span>' +
          '<span>₹' + (opt.fuel_cost_inr || '—') + '</span>' +
        '</div>' +
        cwBadge +
        (toHtml ? '<div class="opt-tradeoffs-wrap">' + toHtml + '</div>' : '') +
      '</div>'
    );
  }

  function render(resp) {
    var panel = document.getElementById('options-panel');
    if (!panel) return;

    if (!resp) {
      panel.innerHTML = '<p class="opt-error">' + t('options.no_options') + '</p>';
      panel.hidden = false;
      return;
    }

    var html = '';

    // Warnings
    if (resp.warnings && resp.warnings.length) {
      html += '<div class="opt-warnings">';
      resp.warnings.forEach(function (w) {
        html += '<div class="opt-warning-chip">⚠ ' + _esc(w) + '</div>';
      });
      html += '</div>';
    }

    var options = Array.isArray(resp.options) ? resp.options : [];

    if (options.length === 0) {
      var msg = resp.message || t('options.no_options');
      html += '<p class="opt-empty">' + _esc(msg) + '</p>';
    } else {
      html += '<div class="opt-cards">';
      options.forEach(function (opt) { html += _optionCard(opt); });
      html += '</div>';
    }

    // Excluded routes
    if (resp.excluded_routes && resp.excluded_routes.length) {
      html += '<div class="opt-excluded">';
      html += '<div class="opt-excluded__title">' + t('options.excluded_title') + '</div>';
      resp.excluded_routes.forEach(function (ex) {
        html += '<div class="opt-excluded__item">&#128683; ' +
          '<strong>' + _esc(ex.route_id) + '</strong>: ' + _esc(ex.reason) +
        '</div>';
      });
      html += '</div>';
    }

    panel.innerHTML = html;
    panel.hidden = false;

    // Wire card clicks to highlight route on map
    panel.querySelectorAll('.opt-card[data-route-id]').forEach(function (card) {
      function activate() {
        var rid = card.dataset.routeId;
        if (rid) MapApp.highlightRoute(rid);
        // toast
        var toast = document.getElementById('receiver-toast');
        if (toast) {
          toast.hidden = false;
          clearTimeout(toast._timer);
          toast._timer = setTimeout(function () { toast.hidden = true; }, 4000);
        }
      }
      card.addEventListener('click', activate);
      card.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') activate();
      });
    });
  }

  return { render };

})();
