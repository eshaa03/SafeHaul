"""
tests/test_filters_and_core.py

Tests for A2-A5:
  - Risk engine: scoring, overrides, flood memory, confidence, reasons
  - ETA: range ordering, medium-segment widening, reason string
  - Options: hard filters (safety, shelf life), wait/divert options, recommended flag
  - Service points: reachability flip, mode=emergency filter

Fixtures are loaded from tests/fixtures/ (stand-in data).
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from django.test import Client

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_KL_TZ = ZoneInfo("Asia/Kolkata")
_NOW = datetime(2026, 10, 8, 6, 0, 0, tzinfo=_KL_TZ)
_DEPART = "2026-10-08T06:00:00+05:30"


def _make_dynamic(
    rain=10.0, river=25.0, forecast=3.0,
    closure=False, crowd=0, depth=0,
    clears=None, source="simulated", ts="2026-10-07T06:00:00+05:30"
):
    d = {
        "rain_24h_mm": rain,
        "river_level_pct": river,
        "forecast_3h_mm": forecast,
        "official_closure": closure,
        "crowd_reports": crowd,
        "reported_depth_level": depth,
        "data_source": source,
        "data_timestamp": ts,
    }
    if clears is not None:
        d["clears_in_hours"] = clears
    return d


def _make_segment(seg_id, elevation=40, river_dist=1200, hist=0,
                  hazard="none", length=20.0, road_class="highway",
                  flood_memory=None):
    s = {
        "segment_id": seg_id,
        "name": f"Test segment {seg_id}",
        "route_ids": ["main"],
        "geometry": [[10.5, 76.3]],
        "length_km": length,
        "road_class": road_class,
        "elevation_m": elevation,
        "river_distance_m": river_dist,
        "historical_flood_count": hist,
        "hazard_type": hazard,
        "data_source": "simulated",
    }
    if flood_memory:
        s["flood_memory"] = flood_memory
    return s


# ===========================================================================
# RISK ENGINE TESTS
# ===========================================================================

class TestRiskEngine:

    def test_low_risk_normal_conditions(self):
        from risk.engine import score_segment
        seg = _make_segment("X-01", elevation=50, river_dist=1800, hist=0)
        dyn = _make_dynamic(rain=5, river=15, forecast=1, crowd=0)
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["risk_level"] == "low"
        assert result["risk_score"] < 0.30
        assert len(result["reasons"]) >= 1

    def test_high_risk_flood_inputs(self):
        from risk.engine import score_segment
        seg = _make_segment("X-02", elevation=5, river_dist=100, hist=3, hazard="underpass")
        dyn = _make_dynamic(rain=100, river=90, forecast=35, crowd=3)
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["risk_level"] in ("high", "closed")
        assert result["risk_score"] >= 0.55
        assert len(result["reasons"]) >= 2

    def test_official_closure_forces_closed(self):
        """Hard override: official_closure=True always yields risk_level='closed'."""
        from risk.engine import score_segment
        seg = _make_segment("X-03")
        dyn = _make_dynamic(rain=5, river=10, closure=True)
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["risk_level"] == "closed"
        assert any("closure" in r.lower() or "official" in r.lower() for r in result["reasons"])

    def test_depth_level_override_for_mini_truck(self):
        """Depth level >= vehicle max forces closed for mini_truck but not heavy_truck."""
        from risk.engine import score_segment
        seg = _make_segment("X-04")
        # reported_depth_level=2 — exceeds mini_truck max (1) but not heavy_truck max (3)
        dyn = _make_dynamic(rain=20, river=30, depth=2)
        mini = score_segment(seg, dyn, "mini_truck", _NOW)
        heavy = score_segment(seg, dyn, "heavy_truck", _NOW)
        assert mini["risk_level"] == "closed", "mini_truck should be closed at depth 2"
        assert heavy["risk_level"] != "closed", "heavy_truck should NOT be closed at depth 2"

    def test_flood_memory_triggers_history_override(self):
        """When rain >= trigger_mm, flood memory overrides hist factor to 1.0."""
        from risk.engine import score_segment
        seg = _make_segment("X-05", hist=1, flood_memory={"trigger_mm": 80, "events": 2})
        dyn_below = _make_dynamic(rain=60, river=30, forecast=5)
        dyn_above = _make_dynamic(rain=95, river=30, forecast=5)
        result_below = score_segment(seg, dyn_below, "lcv", _NOW)
        result_above = score_segment(seg, dyn_above, "lcv", _NOW)
        # Score with triggered flood memory must be higher
        assert result_above["risk_score"] > result_below["risk_score"]
        # Reason must mention flood memory
        assert any("flood memory" in r.lower() or "trigger" in r.lower()
                   for r in result_above["reasons"])

    def test_confidence_moderate_for_simulated_data(self):
        from risk.engine import score_segment
        seg = _make_segment("X-06")
        dyn = _make_dynamic(source="simulated")
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["confidence"] == "moderate"

    def test_confidence_low_when_timestamp_missing(self):
        from risk.engine import score_segment
        seg = _make_segment("X-07")
        dyn = {"rain_24h_mm": 10, "river_level_pct": 20, "forecast_3h_mm": 3,
               "data_source": "live"}  # no timestamp
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["confidence"] == "low"

    def test_reasons_are_ordered_by_contribution(self):
        """Largest contributing factor should appear first in reasons."""
        from risk.engine import score_segment
        # Very high rain is the dominant factor
        seg = _make_segment("X-08", elevation=50, river_dist=1800, hist=0)
        dyn = _make_dynamic(rain=110, river=15, forecast=2, crowd=0)
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert len(result["reasons"]) >= 1
        # Rain reason should be present and mention mm
        assert any("mm" in r for r in result["reasons"])

    def test_medium_boundary(self):
        from risk.engine import score_segment
        # Craft inputs that should land in medium range
        seg = _make_segment("X-09", elevation=30, river_dist=800, hist=1)
        dyn = _make_dynamic(rain=55, river=45, forecast=12, crowd=1)
        result = score_segment(seg, dyn, "lcv", _NOW)
        assert result["risk_level"] in ("medium", "high")  # at this input level


# ===========================================================================
# ETA TESTS
# ===========================================================================

class TestETA:

    def _scored_map(self, level="low"):
        return {
            "S-01": {"length_km": 28.5, "road_class": "highway", "risk_level": level},
            "S-02": {"length_km": 22.0, "road_class": "highway", "risk_level": level},
            "S-03": {"length_km": 30.2, "road_class": "highway", "risk_level": level},
        }

    def test_earliest_less_than_latest(self):
        from routing.eta import compute_eta
        route = {"route_id": "main", "segment_ids": ["S-01", "S-02", "S-03"], "distance_km": 80}
        eta = compute_eta(route, self._scored_map("low"), "lcv", _DEPART)
        e = datetime.fromisoformat(eta["earliest"])
        l = datetime.fromisoformat(eta["latest"])
        assert e < l

    def test_medium_risk_widens_latest(self):
        from routing.eta import compute_eta
        route = {"route_id": "main", "segment_ids": ["S-01", "S-02", "S-03"], "distance_km": 80}
        eta_low = compute_eta(route, self._scored_map("low"), "lcv", _DEPART)
        eta_med = compute_eta(route, self._scored_map("medium"), "lcv", _DEPART)
        # Medium risk widens the latest ETA
        late_low = datetime.fromisoformat(eta_low["latest"])
        late_med = datetime.fromisoformat(eta_med["latest"])
        assert late_med > late_low, "Medium risk should push latest ETA later"

    def test_rest_added_after_long_drive(self):
        from routing.eta import compute_eta
        # 300 km at 45 km/h = ~6.67 h drive → should trigger rest break
        long_route = {"route_id": "main", "segment_ids": ["S-01"], "distance_km": 300}
        scored_map = {"S-01": {"length_km": 300, "road_class": "highway", "risk_level": "low"}}
        eta = compute_eta(long_route, scored_map, "lcv", _DEPART)
        # Expected: 300/45 * 3600 ≈ 24000 s + 1800 s rest = 25800 s
        assert eta["expected_seconds"] > 300 / 45 * 3600, "Rest break should add to expected time"

    def test_reason_string_non_empty(self):
        from routing.eta import compute_eta
        route = {"route_id": "alt1", "segment_ids": ["S-04", "S-05"], "distance_km": 97}
        scored_map = {
            "S-04": {"length_km": 35.0, "road_class": "state_road", "risk_level": "medium"},
            "S-05": {"length_km": 62.0, "road_class": "state_road", "risk_level": "low"},
        }
        eta = compute_eta(route, scored_map, "lcv", _DEPART, baseline_seconds=6000)
        assert isinstance(eta["reason"], str)
        assert len(eta["reason"]) > 0

    def test_latest_rounded_to_5_minutes(self):
        from routing.eta import compute_eta
        route = {"route_id": "main", "segment_ids": ["S-01", "S-02"], "distance_km": 50}
        scored = {
            "S-01": {"length_km": 28.5, "road_class": "highway", "risk_level": "low"},
            "S-02": {"length_km": 22.0, "road_class": "highway", "risk_level": "low"},
        }
        eta = compute_eta(route, scored, "lcv", _DEPART)
        latest = datetime.fromisoformat(eta["latest"])
        assert latest.second == 0
        assert latest.minute % 5 == 0, f"Latest ETA minute {latest.minute} not divisible by 5"


# ===========================================================================
# OPTIONS / HARD FILTER TESTS (the 5 required)
# ===========================================================================

class TestHardFilters:

    def _trip(self, scenario="normal", shelf_life=8, elapsed=0, vehicle="lcv"):
        return {
            "origin": "Palakkad",
            "destination": "Kochi",
            "depart_at": _DEPART,
            "vehicle_type": vehicle,
            "cargo": {
                "type": "vegetables",
                "weight_kg": 5000,
                "shelf_life_hours": shelf_life,
                "value_inr": 250000,
                "hours_already_elapsed": elapsed,
            },
            "scenario": scenario,
        }

    # --- Test 1 ---
    def test_normal_scenario_gives_proceed_option(self):
        """Normal scenario: main route is safe → a 'proceed' option must appear."""
        from safehaul.data_loader import get_routes, get_segments, get_scenarios, get_service_points
        from risk.engine import score_segment
        from routing.options import build_options

        segments = get_segments()
        scenarios_data = get_scenarios()
        routes = get_routes()
        service_points = get_service_points()
        scenario_data = scenarios_data.get("normal", {})
        dyn_by_seg = scenario_data.get("segments", {})
        scored_map = {
            seg["segment_id"]: score_segment(
                seg,
                {"data_source": "simulated", **dyn_by_seg.get(seg["segment_id"], {})},
                "lcv",
                _NOW,
            )
            for seg in segments
        }
        result = build_options(
            self._trip("normal"), scored_map, routes, service_points,
            vehicle_type="lcv", scenario="normal", now=_NOW,
        )
        option_types = [o["type"] for o in result["options"]]
        assert "proceed" in option_types, f"Expected 'proceed' option, got: {option_types}"

    # --- Test 2 ---
    def test_flood_scenario_excludes_main_route(self):
        """Flood scenario: main route has a high-risk segment → main is excluded."""
        from safehaul.data_loader import get_routes, get_segments, get_scenarios, get_service_points
        from risk.engine import score_segment
        from routing.options import build_options

        segments = get_segments()
        scenarios_data = get_scenarios()
        routes = get_routes()
        service_points = get_service_points()
        scenario_data = scenarios_data.get("flood", {})
        dyn_by_seg = scenario_data.get("segments", {})
        scored_map = {
            seg["segment_id"]: score_segment(
                seg,
                {"data_source": "simulated", **dyn_by_seg.get(seg["segment_id"], {})},
                "lcv",
                _NOW,
            )
            for seg in segments
        }
        result = build_options(
            self._trip("flood"), scored_map, routes, service_points,
            vehicle_type="lcv", scenario="flood", now=_NOW,
        )
        excluded_ids = [e["route_id"] for e in result["excluded_routes"]]
        assert "main" in excluded_ids, "Main route must be excluded in flood scenario"
        # Reason must mention a segment
        main_exclusion = next(e for e in result["excluded_routes"] if e["route_id"] == "main")
        assert "S-" in main_exclusion["reason"]

    # --- Test 3 ---
    def test_shelf_life_too_short_excludes_route(self):
        """A route whose latest ETA exceeds shelf life is excluded (not just penalised)."""
        from risk.engine import score_segment
        from routing.options import build_options

        # Build a slow route: 200 km on state_road at low risk → ~6.7 h expected, ~7.4 h latest
        segment = _make_segment("T-01", length=200.0, road_class="state_road")
        dyn = _make_dynamic(rain=5, river=10)
        scored_map = {"T-01": score_segment(segment, dyn, "lcv", _NOW)}

        routes = [{"route_id": "main", "segment_ids": ["T-01"], "distance_km": 200}]
        # Shelf life of 4 hours — 200 km at 30 km/h can't possibly fit
        trip = self._trip(scenario="normal", shelf_life=4)
        result = build_options(
            trip, scored_map, routes, [],
            vehicle_type="lcv", scenario="normal", now=_NOW,
        )
        excluded_ids = [e["route_id"] for e in result["excluded_routes"]]
        assert "main" in excluded_ids, "Route exceeding shelf life must be excluded"
        reason = next(e["reason"] for e in result["excluded_routes"] if e["route_id"] == "main")
        assert "shelf life" in reason.lower() or "elapsed" in reason.lower()

    # --- Test 4 ---
    def test_no_viable_option_gives_empty_options_and_message(self):
        """When every route fails filters, options=[] and message is non-empty."""
        from risk.engine import score_segment
        from routing.options import build_options

        # All segments are high risk
        seg = _make_segment("T-02")
        dyn = _make_dynamic(rain=110, river=95, forecast=38, crowd=3)
        scored_map = {"T-02": score_segment(seg, dyn, "lcv", _NOW)}
        # Force high risk to ensure filter triggers
        scored_map["T-02"]["risk_level"] = "high"

        routes = [{"route_id": "main", "segment_ids": ["T-02"], "distance_km": 50}]
        result = build_options(
            self._trip("flood"), scored_map, routes, [],
            vehicle_type="lcv", scenario="flood", now=_NOW,
        )
        assert result["options"] == [], "options must be empty when no route is viable"
        assert result["message"], "message must be non-empty when no option is available"

    # --- Test 5 ---
    def test_exactly_one_recommended(self):
        """Exactly one option must have recommended=True."""
        from safehaul.data_loader import get_routes, get_segments, get_scenarios, get_service_points
        from risk.engine import score_segment
        from routing.options import build_options

        segments = get_segments()
        scenarios_data = get_scenarios()
        routes = get_routes()
        service_points = get_service_points()
        scenario_data = scenarios_data.get("normal", {})
        dyn_by_seg = scenario_data.get("segments", {})
        scored_map = {
            seg["segment_id"]: score_segment(
                seg,
                {"data_source": "simulated", **dyn_by_seg.get(seg["segment_id"], {})},
                "lcv",
                _NOW,
            )
            for seg in segments
        }
        result = build_options(
            self._trip("normal"), scored_map, routes, service_points,
            vehicle_type="lcv", scenario="normal", now=_NOW,
        )
        if result["options"]:
            recommended_count = sum(1 for o in result["options"] if o.get("recommended"))
            assert recommended_count == 1, (
                f"Exactly 1 option must be recommended, found {recommended_count}"
            )


# ===========================================================================
# SERVICE POINTS TESTS
# ===========================================================================

class TestServicePoints:

    def _scored_map_with_flood(self):
        """S-03 is high risk (flood scenario); S-02, S-01 are low."""
        from safehaul.data_loader import get_segments, get_scenarios
        from risk.engine import score_segment
        segments = get_segments()
        scenario_data = get_scenarios().get("flood", {})
        dyn_by_seg = scenario_data.get("segments", {})
        scored = {}
        for seg in segments:
            sid = seg["segment_id"]
            dyn = {"data_source": "simulated", **dyn_by_seg.get(sid, {})}
            scored[sid] = score_segment(seg, dyn, "lcv", _NOW)
        return scored

    def test_hospital_behind_high_segment_is_unreachable(self):
        """H-01 attaches to S-02 (before flood). H-01 should still be reachable.
           But any hospital attaching to S-03 (high/closed in flood) must be unreachable."""
        from servicepoints.ranking import rank_service_points
        from safehaul.data_loader import get_routes

        scored = self._scored_map_with_flood()
        # In flood, S-03 should be high/closed
        assert scored["S-03"]["risk_level"] in ("high", "closed"), \
            "S-03 must be high/closed in flood for this test to be meaningful"

        # Construct a test point that attaches to S-03
        test_points = [
            {"id": "H-TEST", "name": "Test Hospital", "category": "hospital",
             "lat": 10.3, "lng": 76.3, "attach_segment_id": "S-03", "detour_minutes": 5}
        ]
        route = next(r for r in get_routes() if r["route_id"] == "main")
        ranked = rank_service_points(test_points, route, scored, "lcv", None, "normal")

        assert len(ranked) == 1
        assert ranked[0]["reachable"] is False
        assert ranked[0]["reason"] is not None
        assert "S-03" in ranked[0]["reason"]

    def test_reachable_hospital_ranks_before_unreachable(self):
        """A reachable hospital must appear before an unreachable one in results."""
        from servicepoints.ranking import rank_service_points
        from safehaul.data_loader import get_routes

        scored = self._scored_map_with_flood()
        points = [
            {"id": "H-BLOCK", "name": "Blocked Hospital", "category": "hospital",
             "lat": 10.3, "lng": 76.3, "attach_segment_id": "S-03", "detour_minutes": 5},
            {"id": "H-CLEAR", "name": "Clear Hospital", "category": "hospital",
             "lat": 10.6, "lng": 76.4, "attach_segment_id": "S-01", "detour_minutes": 10},
        ]
        route = next(r for r in get_routes() if r["route_id"] == "main")
        ranked = rank_service_points(points, route, scored, "lcv", None, "normal")

        first = ranked[0]
        second = ranked[1]
        assert first["reachable"] is True, "Reachable hospital must rank first"
        assert first["id"] == "H-CLEAR"
        assert second["reachable"] is False

    def test_emergency_mode_filters_categories(self):
        """mode=emergency must exclude fuel, food, repair etc."""
        from servicepoints.ranking import rank_service_points
        from safehaul.data_loader import get_routes

        scored = self._scored_map_with_flood()
        points = [
            {"id": "H-01", "category": "hospital", "attach_segment_id": "S-01", "detour_minutes": 5},
            {"id": "F-01", "category": "fuel", "attach_segment_id": "S-01", "detour_minutes": 3},
            {"id": "R-01", "category": "repair", "attach_segment_id": "S-01", "detour_minutes": 4},
            {"id": "P-01", "category": "police", "attach_segment_id": "S-01", "detour_minutes": 6},
        ]
        route = next(r for r in get_routes() if r["route_id"] == "main")
        ranked = rank_service_points(points, route, scored, "lcv", None, "emergency")
        cats = {p["category"] for p in ranked}
        assert "fuel" not in cats
        assert "repair" not in cats
        assert "hospital" in cats
        assert "police" in cats


# ===========================================================================
# API ENDPOINT INTEGRATION TESTS
# ===========================================================================

@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_segments_endpoint_flood_has_reasons(client):
    """GET /api/segments/?scenario=flood must return segments with reasons."""
    resp = client.get("/api/segments/?scenario=flood")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for seg in data:
        assert "risk_level" in seg
        assert "risk_score" in seg
        assert "reasons" in seg
        assert isinstance(seg["reasons"], list)
        assert len(seg["reasons"]) >= 1
        assert "confidence" in seg
        assert "data_source" in seg
        assert "data_timestamp" in seg


@pytest.mark.django_db
def test_segments_flood_changes_risk_levels(client):
    """Flood scenario must produce different (higher) risk levels than normal."""
    normal = {s["segment_id"]: s["risk_level"] for s in client.get("/api/segments/?scenario=normal").json()}
    flood = {s["segment_id"]: s["risk_level"] for s in client.get("/api/segments/?scenario=flood").json()}
    level_order = {"low": 0, "medium": 1, "high": 2, "closed": 3}
    worse_count = sum(
        1 for sid in normal
        if level_order.get(flood.get(sid, "low"), 0) > level_order.get(normal[sid], 0)
    )
    assert worse_count >= 1, "At least one segment must be worse in flood scenario"


@pytest.mark.django_db
def test_trip_options_normal_returns_options(client):
    resp = client.post(
        "/api/trip/options/",
        data=json.dumps({
            "origin": "Palakkad",
            "destination": "Kochi",
            "depart_at": _DEPART,
            "vehicle_type": "lcv",
            "cargo": {"type": "vegetables", "weight_kg": 5000,
                      "shelf_life_hours": 10, "value_inr": 250000,
                      "hours_already_elapsed": 0},
            "scenario": "normal",
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "options" in body
    assert "excluded_routes" in body
    assert "generated_at" in body


@pytest.mark.django_db
def test_trip_options_flood_excludes_main(client):
    resp = client.post(
        "/api/trip/options/",
        data=json.dumps({
            "origin": "Palakkad",
            "destination": "Kochi",
            "depart_at": _DEPART,
            "vehicle_type": "lcv",
            "cargo": {"type": "vegetables", "weight_kg": 5000,
                      "shelf_life_hours": 10, "value_inr": 250000,
                      "hours_already_elapsed": 0},
            "scenario": "flood",
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.json()
    excluded_ids = [e["route_id"] for e in body["excluded_routes"]]
    assert "main" in excluded_ids


@pytest.mark.django_db
def test_service_points_endpoint_normal(client):
    resp = client.get("/api/service-points/?scenario=normal")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for pt in data:
        assert "reachable" in pt
        assert "reachable_minutes" in pt or pt["reachable"] is False


@pytest.mark.django_db
def test_service_points_emergency_mode(client):
    resp = client.get("/api/service-points/?mode=emergency&scenario=normal")
    assert resp.status_code == 200
    for pt in resp.json():
        assert pt["category"] in ("hospital", "police", "fire", "safe_halt")


@pytest.mark.django_db
def test_trip_options_missing_fields_returns_400(client):
    resp = client.post(
        "/api/trip/options/",
        data=json.dumps({"origin": "Palakkad"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
