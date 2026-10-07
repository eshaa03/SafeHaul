"""
validate_segments.py — checks that data/segments.json and data/routes.json
are self-consistent and conform to the §1.12 spec.

Run:  python data/scripts/validate_segments.py
Exit 0 = all checks passed.  Exit 1 = at least one failure.
"""

import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

REQUIRED_SEGMENT_FIELDS = [
    "segment_id", "name", "route_ids", "geometry",
    "length_km", "road_class", "elevation_m", "river_distance_m",
    "historical_flood_count", "hazard_type", "data_source",
]
VALID_ROAD_CLASSES = {"highway", "state_road"}
VALID_HAZARD_TYPES = {"none", "underpass", "low_bridge", "landslide_prone"}
VALID_DATA_SOURCES = {"live", "simulated", "historical"}
REQUIRED_ROUTE_FIELDS = ["id", "name", "segment_ids", "distance_km"]


def load(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


errors = []
warnings = []


def fail(msg):
    errors.append(msg)
    print("  FAIL: " + msg)


def warn(msg):
    warnings.append(msg)
    print("  WARN: " + msg)


def ok(msg):
    print("  OK:   " + msg)


print("=== Loading files ===")
segments = load("segments.json")
routes = load("routes.json")
print("  segments.json: %d segments" % len(segments))
print("  routes.json:   %d routes" % len(routes))

# ---- Segment checks --------------------------------------------------------
print()
print("=== Segment checks ===")

seg_ids = set()
for seg in segments:
    sid = seg.get("segment_id", "<missing>")

    # Required fields
    for field in REQUIRED_SEGMENT_FIELDS:
        if field not in seg:
            fail("[%s] missing required field '%s'" % (sid, field))

    # Duplicate IDs
    if sid in seg_ids:
        fail("Duplicate segment_id: %s" % sid)
    seg_ids.add(sid)

    # Geometry: at least 2 points, each a [lat, lng] pair
    geom = seg.get("geometry", [])
    if len(geom) < 2:
        fail("[%s] geometry has fewer than 2 points" % sid)
    for i, pt in enumerate(geom):
        if not (isinstance(pt, list) and len(pt) == 2):
            fail("[%s] geometry[%d] is not a [lat, lng] pair" % (sid, i))
        else:
            lat, lng = pt
            # Kerala bounding box check (very loose)
            if not (8.0 <= lat <= 12.5):
                fail("[%s] geometry[%d] lat %.4f outside Kerala range" % (sid, i, lat))
            if not (74.0 <= lng <= 78.0):
                fail("[%s] geometry[%d] lng %.4f outside Kerala range" % (sid, i, lng))

    # road_class
    rc = seg.get("road_class")
    if rc not in VALID_ROAD_CLASSES:
        fail("[%s] invalid road_class '%s'" % (sid, rc))

    # hazard_type
    ht = seg.get("hazard_type")
    if ht not in VALID_HAZARD_TYPES:
        fail("[%s] invalid hazard_type '%s'" % (sid, ht))

    # clearance_m required when hazard_type is underpass or low_bridge
    if ht in ("underpass", "low_bridge") and "clearance_m" not in seg:
        warn("[%s] hazard_type='%s' but clearance_m not set" % (sid, ht))

    # data_source
    ds = seg.get("data_source")
    if ds not in VALID_DATA_SOURCES:
        fail("[%s] invalid data_source '%s'" % (sid, ds))

    # route_ids non-empty list
    rids = seg.get("route_ids", [])
    if not isinstance(rids, list) or len(rids) == 0:
        fail("[%s] route_ids must be a non-empty list" % sid)

    # Numeric sanity
    if seg.get("length_km", 0) <= 0:
        fail("[%s] length_km must be > 0" % sid)
    if seg.get("elevation_m", -1) < 0:
        fail("[%s] elevation_m must be >= 0" % sid)
    if seg.get("river_distance_m", -1) < 0:
        fail("[%s] river_distance_m must be >= 0" % sid)
    if seg.get("historical_flood_count", -1) < 0:
        fail("[%s] historical_flood_count must be >= 0" % sid)

if not errors:
    ok("All %d segments pass field checks" % len(segments))

# ---- Route checks ----------------------------------------------------------
print()
print("=== Route checks ===")

route_ids_seen = set()
for route in routes:
    rid = route.get("id", "<missing>")

    for field in REQUIRED_ROUTE_FIELDS:
        if field not in route:
            fail("[route %s] missing required field '%s'" % (rid, field))

    if rid in route_ids_seen:
        fail("Duplicate route id: %s" % rid)
    route_ids_seen.add(rid)

    seg_id_list = route.get("segment_ids", [])
    if not isinstance(seg_id_list, list) or len(seg_id_list) == 0:
        fail("[route %s] segment_ids must be a non-empty list" % rid)

    # Every segment ID in the route must exist in segments.json
    missing = [s for s in seg_id_list if s not in seg_ids]
    if missing:
        fail("[route %s] segment_ids reference unknown segments: %s" % (rid, missing))
    else:
        ok("[route %s] all %d segment IDs resolve" % (rid, len(seg_id_list)))

    # distance_km must be positive
    if route.get("distance_km", 0) <= 0:
        fail("[route %s] distance_km must be > 0" % rid)

# ---- Cross-reference: every segment's route_ids resolve --------------------
print()
print("=== Cross-reference: segment.route_ids vs routes ===")

for seg in segments:
    sid = seg["segment_id"]
    for rid in seg.get("route_ids", []):
        if rid not in route_ids_seen:
            fail("[%s] route_ids references unknown route '%s'" % (sid, rid))

# Check that every route's segments back-reference the route
for route in routes:
    rid = route["id"]
    for sid in route.get("segment_ids", []):
        seg = next((s for s in segments if s["segment_id"] == sid), None)
        if seg and rid not in seg.get("route_ids", []):
            fail("[%s] is in route '%s' segment_ids but does not list '%s' in its own route_ids"
                 % (sid, rid, rid))

if not errors:
    ok("All cross-references consistent")

# ---- Route coverage: main and alt1 must exist ------------------------------
print()
print("=== Required routes present ===")
for required in ("main", "alt1"):
    if required in route_ids_seen:
        ok("Route '%s' present" % required)
    else:
        fail("Required route '%s' is missing" % required)

# ---- Summary ---------------------------------------------------------------
print()
print("=" * 50)
if errors:
    print("RESULT: %d error(s), %d warning(s) — FAILED" % (len(errors), len(warnings)))
    sys.exit(1)
else:
    print("RESULT: 0 errors, %d warning(s) — PASSED" % len(warnings))
    sys.exit(0)
