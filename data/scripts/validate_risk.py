"""
validate_risk.py — standalone validation script for SafeHaul Kerala data files.

Implements the exact §1.11 risk formula (no Django dependency) and asserts:
  1. FLOOD scenario: main route contains >= 2 high/closed segments
  2. FLOOD scenario: alt1 route has NO high/closed segments (survives safety filter)
  3. NORMAL scenario: NO segment on any route exceeds 'medium'
  4. clears_in_hours is set on at least one blocking segment in FLOOD
  5. Wait option is NOT viable: clears_in_hours + main_route_eta > shelf_life_hours
  6. service_points.json: H-01 attaches to a high/closed segment in FLOOD
  7. vehicles.json: all required vehicle types present with correct fields

Run:  python data/scripts/validate_risk.py
Exit 0 = all assertions passed.  Exit 1 = at least one failure.
"""

import json
import os
import sys
import math

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

HIGHWAY_SPEED_KMH = 45.0
STATE_ROAD_SPEED_KMH = 30.0
SHELF_LIFE_H = 8.0


def load(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clamp(x):
    return max(0.0, min(1.0, x))


def risk_score(seg, dyn):
    """Compute risk score and level per §1.11."""
    elev = clamp(1 - seg["elevation_m"] / 60)
    river_prox = clamp(1 - seg["river_distance_m"] / 2000)
    hist = clamp(seg["historical_flood_count"] / 3)
    structure = 1.0 if seg["hazard_type"] != "none" else 0.0
    static = 0.30 * elev + 0.25 * river_prox + 0.25 * hist + 0.20 * structure

    rain = dyn.get("rain_24h_mm", 0)
    river_pct = dyn.get("river_level_pct", 0)
    fc3h = dyn.get("forecast_3h_mm", 0)
    crowd = dyn.get("crowd_reports", 0)

    dynamic = (
        0.40 * clamp(rain / 120)
        + 0.35 * clamp(river_pct / 100)
        + 0.25 * clamp(fc3h / 40)
    )
    crowd_score = clamp(crowd / 3)

    score = 0.35 * static + 0.50 * dynamic + 0.15 * crowd_score

    # Override: official closure
    if dyn.get("official_closure", False):
        return 1.0, "closed"

    if score < 0.30:
        level = "low"
    elif score < 0.55:
        level = "medium"
    elif score < 0.80:
        level = "high"
    else:
        level = "closed"

    return score, level


def main_route_eta_latest(segments, seg_by_id, medium_sids):
    """
    Compute eta.latest for the main route per §1.11:
      expected = sum(segment_time * speed_multiplier)  [low=1.0, medium=0.75]
      latest = expected * (1.10 + 0.05 * n_medium_segments)
    Used to check whether the Wait option is viable.
    """
    expected = 0.0
    for sid in segments:
        seg = seg_by_id[sid]
        speed = HIGHWAY_SPEED_KMH if seg["road_class"] == "highway" else STATE_ROAD_SPEED_KMH
        multiplier = 0.75 if sid in medium_sids else 1.0
        expected += seg["length_km"] / speed * multiplier
    n_medium = len([s for s in segments if s in medium_sids])
    latest = expected * (1.10 + 0.05 * n_medium)
    return expected, latest


errors = []


def fail(msg):
    errors.append(msg)
    print("  FAIL: " + msg)


def ok(msg):
    print("  OK:   " + msg)


print("=== Loading data files ===")
segments_list = load("segments.json")
routes_list = load("routes.json")
scenarios = load("scenarios.json")
service_points = load("service_points.json")
vehicles_list = load("vehicles.json")
emergency_codes = load("emergency_codes.json")

seg_by_id = {s["segment_id"]: s for s in segments_list}
route_by_id = {r["id"]: r for r in routes_list}

print("  segments: %d, routes: %d" % (len(segments_list), len(routes_list)))

# ── 1. Compute risk levels for all scenarios ─────────────────────────────────
print()
print("=== Risk scores ===")
print("  %-6s  %-10s  %-8s  %-8s  %s" % ("seg", "scenario", "score", "level", ""))

results = {}
for scenario_name in ("normal", "flood"):
    scen_data = scenarios[scenario_name]
    results[scenario_name] = {}
    for seg in segments_list:
        sid = seg["segment_id"]
        dyn = scen_data.get(sid, {})
        score, level = risk_score(seg, dyn)
        results[scenario_name][sid] = {"score": score, "level": level,
                                       "clears_in_hours": dyn.get("clears_in_hours")}
        marker = " <-- HIGH/CLOSED" if level in ("high", "closed") else ""
        print("  %-6s  %-10s  %-8.3f  %-8s%s" % (sid, scenario_name, score, level, marker))

# ── 2. FLOOD: main route must be excluded (>= 2 high/closed segments) ────────
print()
print("=== Assertion: FLOOD excludes main route ===")
main_ids = route_by_id["main"]["segment_ids"]
flood_high_on_main = [
    sid for sid in main_ids
    if results["flood"][sid]["level"] in ("high", "closed")
]
if len(flood_high_on_main) >= 2:
    ok("Main route has %d high/closed segments in FLOOD: %s" % (len(flood_high_on_main), flood_high_on_main))
else:
    fail("Main route needs >= 2 high/closed segments in FLOOD; found %d: %s" % (
        len(flood_high_on_main), flood_high_on_main))

# ── 3. FLOOD: alt1 must have NO high/closed segments ─────────────────────────
print()
print("=== Assertion: FLOOD alt1 survives (no high/closed) ===")
alt1_ids = route_by_id["alt1"]["segment_ids"]
flood_high_on_alt1 = [
    sid for sid in alt1_ids
    if results["flood"][sid]["level"] in ("high", "closed")
]
if not flood_high_on_alt1:
    ok("alt1 has 0 high/closed segments in FLOOD — route survives safety filter")
else:
    fail("alt1 has high/closed segments in FLOOD (should be 0): %s" % flood_high_on_alt1)

alt1_medium = [
    sid for sid in alt1_ids
    if results["flood"][sid]["level"] == "medium"
]
if alt1_medium:
    ok("alt1 has medium segments in FLOOD (will appear in trade-offs): %s" % alt1_medium)
else:
    print("  WARN: alt1 has no medium segments in FLOOD — trade-offs will be empty")

# ── 4. NORMAL: no segment exceeds medium ─────────────────────────────────────
print()
print("=== Assertion: NORMAL scenario — no high/closed segments ===")
normal_high = [
    sid for sid in seg_by_id
    if results["normal"][sid]["level"] in ("high", "closed")
]
if not normal_high:
    ok("No high/closed segments in NORMAL scenario")
else:
    fail("NORMAL scenario has high/closed segments (should be 0): %s" % normal_high)

# ── 5. clears_in_hours set on at least one blocking segment ──────────────────
print()
print("=== Assertion: clears_in_hours on a blocking segment ===")
blocking_with_clears = [
    sid for sid in flood_high_on_main
    if results["flood"][sid].get("clears_in_hours") is not None
]
if blocking_with_clears:
    for sid in blocking_with_clears:
        ch = results["flood"][sid]["clears_in_hours"]
        ok("%s has clears_in_hours=%s" % (sid, ch))
else:
    fail("No blocking main-route segment has clears_in_hours set")

# ── 6. Wait option NOT viable (clears_in_hours + eta.latest > shelf_life) ────
print()
print("=== Assertion: Wait option excluded by cargo shelf-life filter ===")
# Medium segments on main route in flood scenario (for speed-multiplier)
flood_medium_on_main = set(
    sid for sid in main_ids if results["flood"][sid]["level"] == "medium"
)
expected_h, latest_h = main_route_eta_latest(main_ids, seg_by_id, flood_medium_on_main)
ok("Main route: expected=%.2f h, latest=%.2f h (%d medium segs)" % (
    expected_h, latest_h, len(flood_medium_on_main)))
for sid in blocking_with_clears:
    ch = results["flood"][sid]["clears_in_hours"]
    total = ch + latest_h
    if total > SHELF_LIFE_H:
        ok("%s: clears_in_hours(%s) + eta.latest(%.2f) = %.2f h > %.1f h => Wait excluded" % (
            sid, ch, latest_h, total, SHELF_LIFE_H))
    else:
        fail("%s: Wait option IS viable (%.2f h <= %.1f h shelf_life) — expected exclusion" % (
            sid, total, SHELF_LIFE_H))

# ── 7. Service-point: H-01 behind a high-risk segment in FLOOD ───────────────
print()
print("=== Assertion: H-01 attach segment is high-risk in FLOOD ===")
sp_by_id = {sp["id"]: sp for sp in service_points if "id" in sp}
h01 = sp_by_id.get("H-01")
if h01:
    attach = h01["attach_segment_id"]
    flood_level = results["flood"].get(attach, {}).get("level", "unknown")
    if flood_level in ("high", "closed"):
        ok("H-01 attaches to %s which is %s in FLOOD => nearest-reachable flip works" % (attach, flood_level))
    else:
        fail("H-01 attach segment %s is only '%s' in FLOOD — flip demo won't work" % (attach, flood_level))
else:
    fail("H-01 not found in service_points.json")

# ── 8. Vehicles: required types present ──────────────────────────────────────
print()
print("=== Assertion: vehicles.json has required types ===")
veh_types = {v["vehicle_type"] for v in vehicles_list}
for required in ("mini_truck", "lcv", "heavy_truck", "tipper"):
    if required in veh_types:
        ok("vehicle_type '%s' present" % required)
    else:
        fail("vehicle_type '%s' missing from vehicles.json" % required)

# ── 9. Emergency codes 01-07 present ─────────────────────────────────────────
print()
print("=== Assertion: emergency_codes.json has codes 01-07 ===")
code_set = {ec["code"] for ec in emergency_codes}
for c in ("01", "02", "03", "04", "05", "06", "07"):
    if c in code_set:
        ok("code %s present" % c)
    else:
        fail("code %s missing from emergency_codes.json" % c)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
if errors:
    print("RESULT: %d error(s) — FAILED" % len(errors))
    sys.exit(1)
else:
    print("RESULT: 0 errors — ALL ASSERTIONS PASSED")
    sys.exit(0)
