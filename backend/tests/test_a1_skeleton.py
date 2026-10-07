"""
tests/test_a1_skeleton.py — smoke tests for task A1.

Verifies the project skeleton, data loader, and scenario endpoints.
"""

import json
import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def test_data_loader_returns_segments():
    from safehaul.data_loader import get_segments
    segments = get_segments()
    assert isinstance(segments, list), "get_segments() must return a list"
    assert len(segments) >= 1, "Must have at least one segment"


def test_data_loader_returns_routes():
    from safehaul.data_loader import get_routes
    routes = get_routes()
    assert isinstance(routes, list)
    assert len(routes) >= 1


def test_data_loader_segments_have_required_fields():
    from safehaul.data_loader import get_segments
    required = {
        "segment_id", "name", "route_ids", "geometry",
        "length_km", "road_class", "elevation_m",
        "river_distance_m", "historical_flood_count", "hazard_type",
    }
    for seg in get_segments():
        missing = required - seg.keys()
        assert not missing, f"Segment {seg.get('segment_id')} missing fields: {missing}"


def test_data_loader_routes_have_required_fields():
    from safehaul.data_loader import get_routes
    required = {"route_id", "name", "segment_ids", "distance_km"}
    for route in get_routes():
        missing = required - route.keys()
        assert not missing, f"Route {route.get('route_id')} missing fields: {missing}"


def test_data_loader_scenarios_has_normal_and_flood():
    from safehaul.data_loader import get_scenarios
    scenarios = get_scenarios()
    assert "normal" in scenarios, "scenarios.json must have a 'normal' key"
    assert "flood" in scenarios, "scenarios.json must have a 'flood' key"


def test_data_loader_vehicles_keyed_by_type():
    from safehaul.data_loader import get_vehicles
    vehicles = get_vehicles()
    assert isinstance(vehicles, dict)
    assert "lcv" in vehicles, "vehicles must include 'lcv' (demo default)"


# ---------------------------------------------------------------------------
# Scenario endpoint — GET
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_get_scenario_returns_json(client):
    resp = client.get("/api/scenario/")
    assert resp.status_code == 200
    data = resp.json()
    assert "scenario" in data
    assert data["scenario"] in ("normal", "flood")


# ---------------------------------------------------------------------------
# Scenario endpoint — POST
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_post_scenario_flood(client):
    resp = client.post(
        "/api/scenario/",
        data=json.dumps({"scenario": "flood"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["scenario"] == "flood"


@pytest.mark.django_db
def test_post_scenario_normal(client):
    resp = client.post(
        "/api/scenario/",
        data=json.dumps({"scenario": "normal"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json()["scenario"] == "normal"


@pytest.mark.django_db
def test_post_scenario_invalid(client):
    resp = client.post(
        "/api/scenario/",
        data=json.dumps({"scenario": "hurricane"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


@pytest.mark.django_db
def test_scenario_toggle_persists(client):
    """POST flood, then GET — should still be flood."""
    client.post(
        "/api/scenario/",
        data=json.dumps({"scenario": "flood"}),
        content_type="application/json",
    )
    resp = client.get("/api/scenario/")
    assert resp.json()["scenario"] == "flood"
    # Reset to normal for other tests
    client.post(
        "/api/scenario/",
        data=json.dumps({"scenario": "normal"}),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Routes endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_get_routes_returns_list(client):
    resp = client.get("/api/routes/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.django_db
def test_get_routes_have_segment_ids(client):
    resp = client.get("/api/routes/")
    for route in resp.json():
        assert "route_id" in route
        assert "segment_ids" in route
        assert isinstance(route["segment_ids"], list)


# ---------------------------------------------------------------------------
# Config module — spot-check constants exist and have sensible values
# ---------------------------------------------------------------------------

def test_config_weights_sum_to_one():
    from safehaul import config as c
    total = c.RISK_WEIGHT_STATIC + c.RISK_WEIGHT_DYNAMIC + c.RISK_WEIGHT_CROWD
    assert abs(total - 1.0) < 1e-9, f"Top-level risk weights must sum to 1.0, got {total}"


def test_config_static_sub_weights_sum_to_one():
    from safehaul import config as c
    total = (
        c.STATIC_WEIGHT_ELEVATION
        + c.STATIC_WEIGHT_RIVER_PROXIMITY
        + c.STATIC_WEIGHT_HISTORY
        + c.STATIC_WEIGHT_STRUCTURE
    )
    assert abs(total - 1.0) < 1e-9, f"Static sub-weights must sum to 1.0, got {total}"


def test_config_dynamic_sub_weights_sum_to_one():
    from safehaul import config as c
    total = (
        c.DYNAMIC_WEIGHT_RAIN_24H
        + c.DYNAMIC_WEIGHT_RIVER_LEVEL
        + c.DYNAMIC_WEIGHT_FORECAST_3H
    )
    assert abs(total - 1.0) < 1e-9, f"Dynamic sub-weights must sum to 1.0, got {total}"


def test_config_base_speeds_include_highway():
    from safehaul import config as c
    assert "highway" in c.BASE_SPEEDS_KMH
    assert c.BASE_SPEEDS_KMH["highway"] == 45.0


def test_config_lcv_fuel_cost():
    from safehaul import config as c
    assert c.FUEL_COST_PER_KM_INR["lcv"] == 14.0


def test_config_risk_thresholds_ordered():
    from safehaul import config as c
    assert c.RISK_THRESHOLD_LOW < c.RISK_THRESHOLD_MEDIUM < c.RISK_THRESHOLD_HIGH
