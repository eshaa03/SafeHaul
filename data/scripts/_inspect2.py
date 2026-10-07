import json

with open('data/scripts/raw_osm_main.json') as f:
    d = json.load(f)

ways = [e for e in d['elements'] if e['type']=='way']
nodes = {e['id']: (e['lat'], e['lon']) for e in d['elements'] if e['type']=='node'}

# Find NH544-tagged ways
nh544 = [w for w in ways if w.get('tags',{}).get('ref','') in ('NH544','NH 544','NH-544')]
print("NH544 ways found: %d" % len(nh544))
for w in nh544:
    tags = w.get('tags', {})
    nids = w.get('nodes', [])
    coords = [nodes[n] for n in nids if n in nodes]
    if coords:
        print("  way %d: %s | nodes=%d | lat range %.3f-%.3f" % (
            w['id'], tags.get('name','?')[:40], len(nids),
            min(c[0] for c in coords), max(c[0] for c in coords)))

# Also find trunk/primary ways and show lat range
print()
print("All trunk ways in dataset:")
for w in [x for x in ways if x.get('tags',{}).get('highway')=='trunk']:
    tags = w.get('tags', {})
    nids = w.get('nodes', [])
    coords = [nodes[n] for n in nids if n in nodes]
    if coords:
        print("  way %d ref=%s name=%s | lat %.3f-%.3f" % (
            w['id'], tags.get('ref','?'), tags.get('name','?')[:40],
            min(c[0] for c in coords), max(c[0] for c in coords)))
