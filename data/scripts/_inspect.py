import json
with open('data/scripts/raw_osm_main.json') as f:
    d = json.load(f)
ways = [e for e in d['elements'] if e['type']=='way']
nodes = {e['id']: e for e in d['elements'] if e['type']=='node'}
print("Ways: %d, Nodes: %d" % (len(ways), len(nodes)))
for w in ways[:8]:
    tags = w.get('tags', {})
    name = tags.get('name','?')
    print("  way %d: highway=%s name=%s ref=%s nodes=%d" % (
        w['id'], tags.get('highway','?'), name[:50], tags.get('ref','?'), len(w.get('nodes',[]))))
