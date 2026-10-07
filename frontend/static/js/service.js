/**
 * SafeHaul Kerala — service-points module
 *
 * Loads /api/service-points/ filtered to hospitals and renders a compact list
 * showing reachable_minutes or a "Not reachable" notice with the reason.
 */

const Service = (() => {

  function _esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function _renderList(points) {
    var list = document.getElementById('hospital-list');
    if (!list) return;

    var hospitals = points.filter(function (p) { return p.category === 'hospital'; });

    if (!hospitals.length) {
      list.innerHTML = '<p class="svc-empty">No hospital data available.</p>';
      return;
    }

    var html = '';
    hospitals.forEach(function (h) {
      var reachableHtml;
      if (h.reachable) {
        var mins = typeof h.reachable_minutes === 'number' ? h.reachable_minutes : '?';
        reachableHtml =
          '<span class="svc-reachable">' +
          t('services.reachable_minutes').replace('{minutes}', mins) +
          '</span>';
      } else {
        var reason = h.reason || '—';
        reachableHtml =
          '<span class="svc-not-reachable">' +
          t('services.not_reachable') + '</span>' +
          '<div class="svc-reason">' + _esc(reason) + '</div>';
      }

      var verified = h.last_verified
        ? '<div class="svc-verified">' +
            t('services.last_verified').replace('{date}', h.last_verified) +
          '</div>'
        : '';

      html +=
        '<div class="svc-item' + (h.reachable ? '' : ' svc-item--blocked') + '">' +
          '<div class="svc-item__name">🏥 ' + _esc(h.name) + '</div>' +
          reachableHtml +
          verified +
        '</div>';
    });

    list.innerHTML = html;
  }

  async function loadHospitals({ vehicleType, scenario } = {}) {
    try {
      var pts = await SafehaulAPI.getServicePoints({
        mode: 'normal',
        vehicleType: vehicleType || SAFEHAUL_CONFIG.DEMO.vehicle_type,
        scenario:    scenario    || 'normal',
      });
      _renderList(Array.isArray(pts) ? pts : []);
    } catch (err) {
      console.error('[service] failed:', err);
    }
  }

  return { loadHospitals };

})();
