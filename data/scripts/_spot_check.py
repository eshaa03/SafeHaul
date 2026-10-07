import json
with open('data/segments.json') as f:
    segs = json.load(f)
demo_ids = ['M-07', 'M-09', 'M-11', 'A-04']
for s in segs:
    if s['segment_id'] in demo_ids:
        print("%s: %s" % (s['segment_id'], s['name']))
        print("  route_ids=%s  road_class=%s  hazard=%s  elevation=%dm  river=%dm  hist_flood=%d  len=%.1fkm" % (
            s['route_ids'], s['road_class'], s['hazard_type'],
            s['elevation_m'], s['river_distance_m'],
            s['historical_flood_count'], s['length_km']))
        if 'clearance_m' in s:
            print("  clearance_m=%.1f" % s['clearance_m'])
        print()
