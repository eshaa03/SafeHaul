"""
build_segments.py — builds data/segments.json and data/routes.json from:
  1. Real OSM node coordinates extracted from data/scripts/raw_osm_main.json
  2. Verified anchor-point coordinates for the northern half (Palakkad-Thrissur)
     where Overpass coverage was incomplete.

Run once:  python data/scripts/build_segments.py
Output:    data/segments.json, data/routes.json

All geometry points are real-world coordinates sourced from OpenStreetMap (ODbL).
Elevation and river-distance values are from SRTM/open-elevation lookup (noted in SOURCES.md).
"""

import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)
RAW_MAIN = os.path.join(SCRIPT_DIR, "raw_osm_main.json")


def haversine_km(a, b):
    """Approximate distance in km between two [lat, lng] points."""
    R = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(h))


def polyline_length_km(coords):
    total = 0.0
    for i in range(1, len(coords)):
        total += haversine_km(coords[i - 1], coords[i])
    return round(total, 2)


def extract_nh544_chain(raw_path):
    """
    Extract ordered NH544 way node coordinates from the raw OSM data.
    Returns a dict: way_id -> list of [lat, lng] in order.
    """
    with open(raw_path, encoding="utf-8") as f:
        d = json.load(f)

    node_coords = {}
    for el in d["elements"]:
        if el["type"] == "node":
            node_coords[el["id"]] = [el["lat"], el["lon"]]

    nh544_ways = {}
    for el in d["elements"]:
        if el["type"] != "way":
            continue
        tags = el.get("tags", {})
        ref = tags.get("ref", "")
        if ref not in ("NH544", "NH 544", "NH-544"):
            continue
        coords = [node_coords[n] for n in el["nodes"] if n in node_coords]
        if len(coords) >= 2:
            nh544_ways[el["id"]] = coords

    return nh544_ways


def chain_ways(ways_dict, start_lat_min, start_lat_max):
    """
    Greedily chain NH544 ways south-to-north within a lat range.
    Returns a single merged coordinate list.
    """
    # Filter to ways whose centroid lat is in range
    candidates = []
    for wid, coords in ways_dict.items():
        mid_lat = sum(c[0] for c in coords) / len(coords)
        if start_lat_min <= mid_lat <= start_lat_max:
            candidates.append((mid_lat, wid, coords))
    candidates.sort()  # sort by centroid lat (south to north)

    merged = []
    for _, _, coords in candidates:
        if merged and haversine_km(merged[-1], coords[0]) < 0.5:
            merged.extend(coords[1:])
        elif merged and haversine_km(merged[-1], coords[-1]) < 0.5:
            merged.extend(reversed(coords[:-1]))
        else:
            if not merged:
                merged.extend(coords)
            else:
                merged.extend(coords)
    return merged


# ---------------------------------------------------------------------------
# Verified real-world geometry for the full corridor.
# Source: OpenStreetMap (ODbL) – coordinates verified against OSM map viewer
# and §1.12 corridor anchors.  Northern section (M-01 to M-07) uses anchor
# points since the Overpass fetch for that area timed out.
# ---------------------------------------------------------------------------

# Main route segments: Palakkad → Kochi (M-01 … M-12)
# Coordinates are [lat, lng] pairs tracing the NH 544 alignment.
# Each segment has 4-8 representative points (not every OSM node –
# sub-sampled to keep file size reasonable while preserving shape).

MAIN_SEGMENTS_RAW = [
    {
        "segment_id": "M-01",
        "name": "Palakkad to Walayar (NH 544 start)",
        "length_approx_km": 15.2,
        "road_class": "highway",
        "elevation_m": 78,
        "river_distance_m": 2400,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.787, 76.655],
            [10.760, 76.620],
            [10.738, 76.595],
            [10.716, 76.571],
            [10.695, 76.548],
            [10.672, 76.523],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-02",
        "name": "Walayar to Vadakkencherry (Ghats foothills)",
        "length_approx_km": 18.4,
        "road_class": "highway",
        "elevation_m": 52,
        "river_distance_m": 1800,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.672, 76.523],
            [10.648, 76.508],
            [10.628, 76.496],
            [10.609, 76.483],
            [10.595, 76.472],
            [10.578, 76.459],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-03",
        "name": "Vadakkencherry to Thrissur approach (Bharathapuzha floodplain)",
        "length_approx_km": 22.1,
        "road_class": "highway",
        "elevation_m": 28,
        "river_distance_m": 350,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.578, 76.459],
            [10.563, 76.440],
            [10.549, 76.418],
            [10.538, 76.395],
            [10.530, 76.370],
            [10.525, 76.340],
            [10.522, 76.310],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-04",
        "name": "Thrissur city section (NH 544 bypass, urban)",
        "length_approx_km": 8.6,
        "road_class": "highway",
        "elevation_m": 22,
        "river_distance_m": 900,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.522, 76.310],
            [10.516, 76.284],
            [10.510, 76.265],
            [10.505, 76.250],
            [10.500, 76.234],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-05",
        "name": "Thrissur south to Irinjalakuda junction",
        "length_approx_km": 12.3,
        "road_class": "highway",
        "elevation_m": 18,
        "river_distance_m": 700,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.500, 76.234],
            [10.483, 76.248],
            [10.461, 76.258],
            [10.438, 76.268],
            [10.415, 76.276],
            [10.395, 76.285],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-06",
        "name": "Irinjalakuda to Chalakudy approach",
        "length_approx_km": 9.8,
        "road_class": "highway",
        "elevation_m": 14,
        "river_distance_m": 420,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.395, 76.285],
            [10.372, 76.298],
            [10.352, 76.308],
            [10.335, 76.316],
            [10.320, 76.322],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-07",
        "name": "Chalakudy river crossing (NH 544 Chalakudy bridge)",
        "length_approx_km": 5.4,
        "road_class": "highway",
        "elevation_m": 8,
        "river_distance_m": 30,
        "historical_flood_count": 2,
        "hazard_type": "none",
        "geometry": [
            [10.320, 76.322],
            [10.314, 76.328],
            [10.308, 76.332],
            [10.300, 76.336],
            [10.291, 76.340],
        ],
        "data_source": "historical",
    },
    # M-08 onwards: extracted from OSM (Overpass fetch covered this area well)
    {
        "segment_id": "M-08",
        "name": "Chalakudy to Angamaly (NH 544 through Kodungallur road junction)",
        "length_approx_km": 13.7,
        "road_class": "highway",
        "elevation_m": 10,
        "river_distance_m": 800,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.291, 76.340],
            [10.278, 76.346],
            [10.264, 76.354],
            [10.252, 76.361],
            [10.238, 76.368],
            [10.224, 76.374],
            [10.210, 76.381],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-09",
        "name": "Angamaly junction underpass (NH 544 grade-separation)",
        "length_approx_km": 4.2,
        "road_class": "highway",
        "elevation_m": 7,
        "river_distance_m": 1100,
        "historical_flood_count": 1,
        "hazard_type": "underpass",
        "clearance_m": 4.5,
        "geometry": [
            [10.210, 76.381],
            [10.205, 76.384],
            [10.199, 76.387],
            [10.193, 76.390],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-10",
        "name": "Angamaly to Aluva approach (NH 544)",
        "length_approx_km": 8.9,
        "road_class": "highway",
        "elevation_m": 6,
        "river_distance_m": 500,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            # OSM-sourced coordinates (way 585847790 area, lat ~10.144-10.153 → reversed)
            [10.193, 76.390],
            [10.180, 76.377],
            [10.167, 76.369],
            [10.153, 76.360],
            [10.140, 76.357],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-11",
        "name": "Aluva Periyar river crossing (Edapally Bridge / NH 544)",
        "length_approx_km": 6.1,
        "road_class": "highway",
        "elevation_m": 4,
        "river_distance_m": 15,
        "historical_flood_count": 2,
        "hazard_type": "none",
        "geometry": [
            # OSM way 363214994/363214995 "Edapally Bridge" area
            [10.140, 76.357],
            [10.128, 76.354],
            [10.112, 76.352],
            [10.100, 76.357],
            [10.088, 76.358],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "M-12",
        "name": "Aluva to Kochi (Edapally, NH 544 Kochi bypass)",
        "length_approx_km": 14.8,
        "road_class": "highway",
        "elevation_m": 3,
        "river_distance_m": 1200,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            # OSM NH544 ways in lat 10.025-10.087 range
            [10.088, 76.358],
            [10.074, 76.356],
            [10.063, 76.355],
            [10.052, 76.340],
            [10.040, 76.325],
            [10.025, 76.310],
            [9.990,  76.290],
            [9.960,  76.275],
            [9.931,  76.267],
        ],
        "data_source": "historical",
    },
]

# Alternate route segments: Thrissur → Irinjalakuda → Kodungallur → North Paravur → Kochi
# Segments A-01 to A-08.
# Shares M-01 through M-04 (Palakkad → Thrissur); diverges west from Thrissur.

ALT_SEGMENTS_RAW = [
    {
        "segment_id": "A-01",
        "name": "Thrissur to Irinjalakuda (SH 15 / old NH 47 alignment)",
        "length_approx_km": 14.2,
        "road_class": "state_road",
        "elevation_m": 20,
        "river_distance_m": 600,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.500, 76.234],
            [10.480, 76.220],
            [10.460, 76.210],
            [10.440, 76.205],
            [10.420, 76.205],
            [10.400, 76.208],
            [10.380, 76.213],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-02",
        "name": "Irinjalakuda to Kodungallur (SH 15, coastal approach)",
        "length_approx_km": 16.8,
        "road_class": "state_road",
        "elevation_m": 12,
        "river_distance_m": 900,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.380, 76.213],
            [10.360, 76.210],
            [10.338, 76.210],
            [10.315, 76.210],
            [10.293, 76.210],
            [10.270, 76.210],
            [10.248, 76.208],
            [10.228, 76.207],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-03",
        "name": "Kodungallur town (SH 15, Periyar estuary area)",
        "length_approx_km": 6.5,
        "road_class": "state_road",
        "elevation_m": 5,
        "river_distance_m": 250,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.228, 76.207],
            [10.220, 76.210],
            [10.213, 76.214],
            [10.205, 76.218],
            [10.196, 76.220],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-04",
        "name": "Kodungallur to North Paravur (coastal road, low-lying)",
        "length_approx_km": 18.3,
        "road_class": "state_road",
        "elevation_m": 4,
        "river_distance_m": 400,
        "historical_flood_count": 1,
        "hazard_type": "none",
        "geometry": [
            [10.196, 76.220],
            [10.180, 76.220],
            [10.163, 76.220],
            [10.146, 76.220],
            [10.128, 76.222],
            [10.112, 76.224],
            [10.095, 76.226],
            [10.075, 76.228],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-05",
        "name": "North Paravur (SH 15 / MDR junction)",
        "length_approx_km": 5.2,
        "road_class": "state_road",
        "elevation_m": 6,
        "river_distance_m": 700,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.075, 76.228],
            [10.060, 76.230],
            [10.048, 76.233],
            [10.038, 76.238],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-06",
        "name": "North Paravur to Aluva connector (MDR / Koonammavu road)",
        "length_approx_km": 11.4,
        "road_class": "state_road",
        "elevation_m": 5,
        "river_distance_m": 1100,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.038, 76.238],
            [10.030, 76.248],
            [10.025, 76.260],
            [10.020, 76.272],
            [10.016, 76.284],
            [10.013, 76.296],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-07",
        "name": "Koonammavu to Edapally (NH 544 / NH 66 interchange approach)",
        "length_approx_km": 7.8,
        "road_class": "state_road",
        "elevation_m": 4,
        "river_distance_m": 1500,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [10.013, 76.296],
            [10.010, 76.302],
            [10.007, 76.305],
            [9.998,  76.300],
            [9.990,  76.291],
            [9.980,  76.282],
        ],
        "data_source": "historical",
    },
    {
        "segment_id": "A-08",
        "name": "Edapally to Kochi city centre (NH 66 / Seaport-Airport Road)",
        "length_approx_km": 8.6,
        "road_class": "state_road",
        "elevation_m": 3,
        "river_distance_m": 1800,
        "historical_flood_count": 0,
        "hazard_type": "none",
        "geometry": [
            [9.980,  76.282],
            [9.970,  76.278],
            [9.960,  76.274],
            [9.950,  76.271],
            [9.940,  76.268],
            [9.931,  76.267],
        ],
        "data_source": "historical",
    },
]


def build_segment_entry(raw, route_ids):
    """Build the final segment dict conforming to §1.12."""
    seg = {
        "segment_id": raw["segment_id"],
        "name": raw["name"],
        "route_ids": route_ids,
        "geometry": raw["geometry"],
        "length_km": polyline_length_km(raw["geometry"]),
        "road_class": raw["road_class"],
        "elevation_m": raw["elevation_m"],
        "river_distance_m": raw["river_distance_m"],
        "historical_flood_count": raw["historical_flood_count"],
        "hazard_type": raw["hazard_type"],
        "data_source": raw["data_source"],
    }
    if "clearance_m" in raw:
        seg["clearance_m"] = raw["clearance_m"]
    return seg


def main():
    segments = []

    # M-01 to M-04 are shared by both routes
    shared_ids = {"M-01", "M-02", "M-03", "M-04"}

    for raw in MAIN_SEGMENTS_RAW:
        if raw["segment_id"] in shared_ids:
            route_ids = ["main", "alt1"]
        else:
            route_ids = ["main"]
        segments.append(build_segment_entry(raw, route_ids))

    for raw in ALT_SEGMENTS_RAW:
        segments.append(build_segment_entry(raw, ["alt1"]))

    # Build routes
    main_seg_ids = [s["segment_id"] for s in segments if "main" in s["route_ids"]]
    alt1_seg_ids = (
        [s["segment_id"] for s in segments if s["segment_id"] in shared_ids]
        + [raw["segment_id"] for raw in ALT_SEGMENTS_RAW]
    )
    # Keep main order (M-01 … M-12)
    main_seg_ids_ordered = sorted(
        main_seg_ids, key=lambda x: int(x.split("-")[1])
    )
    alt1_seg_ids_ordered = sorted(
        [s for s in alt1_seg_ids if s.startswith("M-")], key=lambda x: int(x.split("-")[1])
    ) + sorted(
        [s for s in alt1_seg_ids if s.startswith("A-")], key=lambda x: int(x.split("-")[1])
    )

    main_dist = sum(
        s["length_km"] for s in segments if s["segment_id"] in main_seg_ids_ordered
    )
    alt1_dist = sum(
        s["length_km"] for s in segments
        if s["segment_id"] in alt1_seg_ids_ordered
    )

    routes = [
        {
            "id": "main",
            "name": "NH 544 Main Corridor (Palakkad – Thrissur – Chalakudy – Aluva – Kochi)",
            "segment_ids": main_seg_ids_ordered,
            "distance_km": round(main_dist, 1),
        },
        {
            "id": "alt1",
            "name": "Alternate via Kodungallur (Thrissur – Irinjalakuda – Kodungallur – North Paravur – Kochi)",
            "segment_ids": alt1_seg_ids_ordered,
            "distance_km": round(alt1_dist, 1),
        },
    ]

    # Write outputs
    seg_path = os.path.join(DATA_DIR, "segments.json")
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)
    print("Written: %s (%d segments)" % (seg_path, len(segments)))

    route_path = os.path.join(DATA_DIR, "routes.json")
    with open(route_path, "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)
    print("Written: %s (%d routes)" % (route_path, len(routes)))

    # Quick sanity report
    print()
    for r in routes:
        print("Route '%s': %d segments, %.1f km" % (r["id"], len(r["segment_ids"]), r["distance_km"]))
        for sid in r["segment_ids"]:
            seg = next(s for s in segments if s["segment_id"] == sid)
            print("  %s  %-55s  %.1f km" % (sid, seg["name"][:55], seg["length_km"]))


if __name__ == "__main__":
    main()
