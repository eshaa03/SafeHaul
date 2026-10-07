/**
 * SafeHaul Kerala — trip form module
 *
 * Reads form values, builds the TripRequest body,
 * calls SafehaulAPI.postTripOptions(), and passes the result to Options.render().
 */

const Trip = (() => {

  function _val(id) {
    var el = document.getElementById(id);
    return el ? el.value.trim() : '';
  }

  function _buildRequest() {
    var sc = document.body.dataset.scenario || 'normal';
    return {
      origin:             _val('trip-origin')      || SAFEHAUL_CONFIG.DEMO.origin,
      destination:        _val('trip-dest')         || SAFEHAUL_CONFIG.DEMO.destination,
      depart_at:          _val('trip-depart')       || SAFEHAUL_CONFIG.DEMO.depart_at,
      vehicle_type:       _val('trip-vehicle')      || SAFEHAUL_CONFIG.DEMO.vehicle_type,
      cargo: {
        type:                _val('trip-cargo-type') || SAFEHAUL_CONFIG.DEMO.cargo_type,
        weight_kg:           parseFloat(_val('trip-weight'))     || SAFEHAUL_CONFIG.DEMO.cargo_weight_kg,
        shelf_life_hours:    parseFloat(_val('trip-shelf'))      || SAFEHAUL_CONFIG.DEMO.cargo_shelf_life_h,
        value_inr:           parseFloat(_val('trip-value'))      || SAFEHAUL_CONFIG.DEMO.cargo_value_inr,
        hours_already_elapsed: 0,
      },
      current_segment_id: null,
      scenario:           sc,
    };
  }

  async function submit() {
    var btn = document.getElementById('trip-submit');
    if (btn) { btn.disabled = true; btn.textContent = t('trip.loading'); }

    try {
      var req  = _buildRequest();
      var resp = await SafehaulAPI.postTripOptions(req);
      Options.render(resp);
      // Also refresh hospital list with current vehicle + scenario
      Service.loadHospitals({
        vehicleType: req.vehicle_type,
        scenario:    req.scenario,
      });
    } catch (err) {
      console.error('[trip] failed:', err);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = t('trip.get_options'); }
    }
  }

  function prefill() {
    var d = SAFEHAUL_CONFIG.DEMO;
    var set = function (id, val) {
      var el = document.getElementById(id);
      if (el && !el.value) el.value = val;
    };
    set('trip-origin',      d.origin);
    set('trip-dest',        d.destination);
    set('trip-depart',      d.depart_at);
    set('trip-vehicle',     d.vehicle_type);
    set('trip-cargo-type',  d.cargo_type);
    set('trip-weight',      d.cargo_weight_kg);
    set('trip-shelf',       d.cargo_shelf_life_h);
    set('trip-value',       d.cargo_value_inr);
  }

  return { submit, prefill };

})();
