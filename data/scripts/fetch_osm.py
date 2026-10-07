"""
fetch_osm.py — one-time script to pull road geometry from OpenStreetMap via Overpass API.

Run once:  python data/scripts/fetch_osm.py
Output:    data/scripts/raw_osm_main.json   (NH 544 Palakkad–Kochi corridor)
           data/scripts/raw_osm_alt1.json   (alternate via Kodungallur)

Data source: OpenStreetMap contributors, © ODbL
             https://www.openstreetmap.org/copyright
             Overpass API: https://overpass-api.de
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
import sys
import os

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def query_overpass(query: str, label: str) -> dict:
    """POST an Overpass QL query and return parsed JSON."""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "SafeHaul-Kerala/1.0 (hackathon project)"},
    )
    print(f"[{label}] Querying Overpass API …", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        print(f"[{label}] ERROR: {exc}", file=sys.stderr)
        return None
    result = json.loads(raw)
    n_elements = len(result.get("elements", []))
    print(f"[{label}] Got {n_elements} elements.", flush=True)
    return result


# ---------------------------------------------------------------------------
# Main corridor: NH 544 trunk ways only, tight corridor bounding boxes
# Split into 3 sub-queries (Palakkad→Thrissur, Thrissur→Aluva, Aluva→Kochi)
# to avoid Overpass timeouts.
# bbox format: (south, west, north, east)
# ---------------------------------------------------------------------------

# Segment 1: Palakkad to Thrissur  (approx 10.48–10.80 N, 76.19–76.70 E)
MAIN_Q1 = """
[out:json][timeout:60];
way["highway"~"^(trunk|primary)$"]["name"~"(National Highway|NH|544)", i]
   (10.48,76.18,10.82,76.72);
out body;
>;
out skel qt;
"""

# Segment 2: Thrissur to Aluva  (approx 10.05–10.55 N, 76.19–76.42 E)
MAIN_Q2 = """
[out:json][timeout:60];
way["highway"~"^(trunk|primary)$"]["name"~"(National Highway|NH|544)", i]
   (10.05,76.18,10.55,76.42);
out body;
>;
out skel qt;
"""

# Segment 3: Aluva to Kochi  (approx 9.88–10.15 N, 76.25–76.40 E)
MAIN_Q3 = """
[out:json][timeout:60];
way["highway"~"^(trunk|primary)$"]
   (9.88,76.24,10.15,76.40);
out body;
>;
out skel qt;
"""

# ---------------------------------------------------------------------------
# Alternate: Thrissur → Irinjalakuda → Kodungallur → North Paravur → Kochi
# Primary/secondary roads in the western coastal strip
# bbox: (9.88–10.55 N, 76.05–76.30 E)
# ---------------------------------------------------------------------------
ALT1_QUERY = """
[out:json][timeout:60];
way["highway"~"^(primary|secondary)$"]
   (9.88,76.05,10.55,76.32);
out body;
>;
out skel qt;
"""


def merge_overpass_results(results: list) -> dict:
    """Merge multiple Overpass JSON results into one (deduplicate by element id)."""
    seen = set()
    merged = {"elements": []}
    for r in results:
        if r is None:
            continue
        for el in r.get("elements", []):
            key = (el.get("type"), el.get("id"))
            if key not in seen:
                seen.add(key)
                merged["elements"].append(el)
    return merged


def save(data: dict, filename: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    size_kb = os.path.getsize(path) // 1024
    print(f"Saved {path} ({size_kb} KB)")


if __name__ == "__main__":
    print("=== Fetching main corridor (3 sub-queries) ===")
    r1 = query_overpass(MAIN_Q1, "MAIN-1 Palakkad-Thrissur")
    time.sleep(4)
    r2 = query_overpass(MAIN_Q2, "MAIN-2 Thrissur-Aluva")
    time.sleep(4)
    r3 = query_overpass(MAIN_Q3, "MAIN-3 Aluva-Kochi")
    time.sleep(4)

    main_merged = merge_overpass_results([r for r in [r1, r2, r3] if r])
    save(main_merged, "raw_osm_main.json")

    print("\n=== Fetching alternate corridor ===")
    alt1_data = query_overpass(ALT1_QUERY, "ALT1 via Kodungallur")
    if alt1_data:
        save(alt1_data, "raw_osm_alt1.json")

    print("\nDone. Check data/scripts/raw_osm_main.json and raw_osm_alt1.json.")
