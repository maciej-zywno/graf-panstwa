#!/usr/bin/env python3
"""Scala chunki data/pl/chunks/*.json z werdyktami *.verdicts.json w data/pl/graph.json.
Reguły: refuted node → usuń (+ jego krawędzie, + head/headOf odwołania); refuted person → usuń z people;
corrected → nadpisz polami fixes; unverified → confidence=low. additions → dodaj. Spójność: children z parent,
head/headOf, dangling refs → raport. Użycie: python3 scripts/merge-chunks.py [--today YYYY-MM-DD]"""
import json, glob, os, sys, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, 'data/pl/chunks')
today = sys.argv[sys.argv.index('--today')+1] if '--today' in sys.argv else '2026-09-17'

nodes, edges, report = {}, {}, collections.Counter()
owners = {}
REMAP = {  # kolizje ID między chunkami: chunk -> {stare_id: nowe_id}
    'urzedy-prm': {'pl-pan': 'pl-polska-akademia-nauk', 'pl-dyrektor-ies': 'pl-dyrektor-instytutu-europy-srodkowej'},
}
def remap_chunk(key, d):
    m = REMAP.get(key)
    if not m: return d
    r = lambda x: m.get(x, x) if isinstance(x, str) else x
    nn = {}
    for nid, n in d.get('nodes', {}).items():
        n['id'] = r(nid)
        for f in ('parent', 'head', 'headOf'): n[f] = r(n.get(f))
        for per in ((n.get('people') or {}).get('people') or []): per['positionId'] = r(per.get('positionId'))
        nn[n['id']] = n
    d['nodes'] = nn
    for e in d.get('edges', {}).values(): e['fromId'] = r(e['fromId']); e['toId'] = r(e['toId'])
    return d
def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict): deep_merge(dst[k], v)
        else: dst[k] = v

chunk_files = sorted(f for f in glob.glob(os.path.join(CH, '*.json')) if not f.endswith('.verdicts.json'))
for f in chunk_files:
    key = os.path.basename(f)[:-5]
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception as e: print('SKIP (bad json)', f, e); continue
    d = remap_chunk(key, d)
    vf = f[:-5] + '.verdicts.json'
    v = None
    if os.path.exists(vf):
        try: v = json.load(open(vf, encoding='utf-8'))
        except Exception as e: print('WARN bad verdicts json', vf, e)
    cn, ce = d.get('nodes', {}), d.get('edges', {})
    rm = REMAP.get(key, {})
    vn = {rm.get(x['id'], x['id']): x for x in (v or {}).get('nodes', [])}
    vp = collections.defaultdict(list)
    for x in (v or {}).get('people', []): vp[rm.get(x.get('nodeId'), x.get('nodeId'))].append(x)
    ve = {x['id']: x for x in (v or {}).get('edges', [])}
    for nid, n in cn.items():
        if nid in nodes:
            report['duplicate_node'] += 1; print(f'DUP node {nid}: {owners[nid]} vs {key} (keeping first)'); continue
        vv = vn.get(nid)
        if vv:
            st = vv.get('status')
            if st == 'refuted' and vv.get('fixes'): st = 'corrected'; report['node_refuted_with_fixes_as_corrected'] += 1
            if st == 'refuted': report['node_refuted'] += 1; print(f'REFUTED node {nid} ({key}): {vv.get("note","")[:160]}'); continue
            if st == 'corrected' and vv.get('fixes'): deep_merge(n, vv['fixes']); report['node_corrected'] += 1
            n.setdefault('provenance', {})
            n['provenance'].setdefault('verifiedAt', today)  # data faktycznego sprawdzenia zostaje; przebieg tygodniowy nie może „odświeżać” węzłów, których nie czytał
            n['provenance']['verdict'] = st
            if st == 'unverified': n['provenance']['confidence'] = 'low'
        else:
            n.setdefault('provenance', {}); n['provenance']['verdict'] = 'unchecked'
        # people verdicts
        ppl = n.get('people')
        if ppl and ppl.get('type') == 'people':
            keep = []
            for per in ppl.get('people', []):
                pv = next((x for x in vp.get(nid, []) if x.get('personId') == per.get('id')), None)
                if pv:
                    st = pv.get('status')
                    if st == 'refuted': report['person_refuted'] += 1; print(f'REFUTED person {per.get("id")} @ {nid}: {pv.get("note","")[:160]}'); continue
                    if st == 'corrected' and pv.get('fixes'): deep_merge(per, pv['fixes']); report['person_corrected'] += 1
                    per['verdict'] = st
                    if st == 'confirmed': per['status'] = per.get('status') if per.get('status') in ('acting','disputed') else 'verified'
                    if st == 'unverified': per['status'] = 'unverified'
                else: per['verdict'] = 'unchecked'
                keep.append(per)
            ppl['people'] = keep
        nodes[nid] = n; owners[nid] = key
    for eid, e in ce.items():
        if eid in edges: report['duplicate_edge'] += 1; continue
        vv = ve.get(eid)
        if vv:
            st = vv.get('status')
            if st == 'refuted': report['edge_refuted'] += 1; print(f'REFUTED edge {eid} ({key}): {vv.get("note","")[:160]}'); continue
            if st == 'corrected' and vv.get('fixes'): deep_merge(e, vv['fixes']); report['edge_corrected'] += 1
            e.setdefault('provenance', {}); e['provenance']['verdict'] = st
            if st == 'unverified': e['provenance']['confidence'] = 'low'
        edges[eid] = e
    add = (v or {}).get('additions') or {}
    for nid, n in (add.get('nodes') or {}).items():
        if nid not in nodes: n.setdefault('provenance', {})['verdict'] = 'added_by_verifier'; nodes[nid] = n; owners[nid] = key + ':verifier'; report['node_added'] += 1
    for eid, e in (add.get('edges') or {}).items():
        if eid not in edges: e.setdefault('provenance', {})['verdict'] = 'added_by_verifier'; edges[eid] = e; report['edge_added'] += 1

# duplikaty relacji (ten sam from, to, type) z różnych chunków: zostaje pierwsza, cytaty się łączą
seen_key = {}
for eid, e in list(edges.items()):
    k = (e.get('fromId'), e.get('toId'), e.get('type'))
    if k in seen_key:
        first = edges[seen_key[k]]
        c1, c2 = (first.get('cite') or '').strip(), (e.get('cite') or '').strip()
        if c2 and c2 not in c1: first['cite'] = (c1 + ' | ' + c2) if c1 else c2
        if not first.get('citeUrl') and e.get('citeUrl'): first['citeUrl'] = e['citeUrl']
        first['seatsAppointed'] = max(first.get('seatsAppointed') or 0, e.get('seatsAppointed') or 0)
        del edges[eid]; report['edge_deduped'] += 1
    else: seen_key[k] = eid

# integrity
def drop_edge(eid, why): report['edge_dropped_' + why] += 1; edges.pop(eid, None)
for eid, e in list(edges.items()):
    if e.get('fromId') not in nodes or e.get('toId') not in nodes:
        print(f'DANGLING edge {eid}: {e.get("fromId")} -> {e.get("toId")}'); drop_edge(eid, 'dangling')
for nid, n in nodes.items():
    for f in ('parent', 'head', 'headOf'):
        if n.get(f) and n[f] not in nodes: print(f'DANGLING {f} on {nid}: {n[f]}'); n[f] = None; report['ref_cleared'] += 1
    n['children'] = []
for nid, n in nodes.items():
    if n.get('parent'):
        nodes[n['parent']]['children'].append(nid)
        if n.get('ring') != 'satellite': n['ring'] = 'satellite'; report['ring_fixed'] += 1
    n['level'] = 0
    p = n.get('parent'); lvl = 0
    while p: lvl += 1; p = nodes[p].get('parent'); 
    n['level'] = lvl
    if n.get('type') == 'dept_head' and n.get('headOf') and n['headOf'] in nodes:
        org = nodes[n['headOf']]
        if not org.get('head'): org['head'] = nid; report['head_backfilled'] += 1
        n['ring'] = org.get('ring') if org.get('ring') != 'satellite' else 'satellite'
        n['parent'] = n['headOf'] if org.get('ring') == 'satellite' else None  # stanowisko satelity wisi przy organie
    if n.get('head') and n['head'] in nodes and not nodes[n['head']].get('headOf'): nodes[n['head']]['headOf'] = nid
# ensure dept_head edges exist
for nid, n in nodes.items():
    if n.get('head') and n['head'] in nodes:
        if not any(e.get('type') == 'dept_head' and e.get('fromId') == nid and e.get('toId') == n['head'] for e in edges.values()):
            eid = f'e-{nid}--dept_head--{n["head"]}'[:120]
            edges[eid] = {'id': eid, 'type': 'dept_head', 'fromId': nid, 'toId': n['head'], 'cite': None, 'citeUrl': None, 'seatsAppointed': 0, 'provenance': {'sources': [], 'confidence': 'high', 'verdict': 'derived'}}
            report['dept_head_edge_added'] += 1
# connectedNodes
conn = collections.defaultdict(set)
for e in edges.values(): conn[e['fromId']].add(e['toId']); conn[e['toId']].add(e['fromId'])
for nid, n in nodes.items():
    n['connectedNodes'] = sorted(conn.get(nid, set()))
    n['edges'] = sorted(eid for eid, e in edges.items() if nid in (e['fromId'], e['toId']))

people = [(nid, p) for nid, n in nodes.items() for p in ((n.get('people') or {}).get('people') or []) if (n.get('people') or {}).get('type') == 'people']
meta = {
    'gov': 'pl', 'name': 'Graf Państwa Polskiego', 'version': '0.1', 'generatedAt': today, 'constituency': 'pl-narod',
    'description': 'Kto kogo powołuje, zatwierdza, kontroluje i nadzoruje. Mapa organów państwa: od Narodu jako suwerena po urzędy centralne i ich jednostki.',
    'counts': {'nodes': len(nodes), 'edges': len(edges), 'people': len(people),
               'byType': dict(collections.Counter(n.get('type') for n in nodes.values())),
               'bySector': dict(collections.Counter(n.get('sector') for n in nodes.values())),
               'byRing': dict(collections.Counter(n.get('ring') for n in nodes.values())),
               'byEdgeType': dict(collections.Counter(e.get('type') for e in edges.values())),
               'peopleByStatus': dict(collections.Counter(p.get('status') for _, p in people)),
               'peopleByVerdict': dict(collections.Counter(p.get('verdict') for _, p in people)),
               'nodesByVerdict': dict(collections.Counter((n.get('provenance') or {}).get('verdict') for n in nodes.values())),
               'legalSourceCoverage': sum(1 for n in nodes.values() if (n.get('legalSource') or {}).get('url')) / max(1, len(nodes))},
    'chunks': [os.path.basename(f)[:-5] for f in chunk_files],
    'mergeReport': dict(report),
    'changes': [],
}
out = {'meta': meta, 'nodes': nodes, 'edges': edges}
json.dump(out, open(os.path.join(ROOT, 'data/pl/graph.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(meta['counts'], ensure_ascii=False, indent=1)); print('mergeReport', dict(report))
