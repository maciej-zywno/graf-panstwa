#!/usr/bin/env python3
"""Różnica merytoryczna między dwoma plikami graph.json: zdarzenia do dziennika zmian i podsumowanie dla człowieka.
Pomija pola czysto techniczne (daty sprawdzenia i generowania, pola pochodne). Zdarzenia dopisuje do data/pl/changes.jsonl.
Użycie: python3 scripts/diff-graph.py <stary.json> <nowy.json> --date RRRR-MM-DD [--source parlament] [--no-append]
Wyjście (stdout): podsumowanie w Markdownie. Kod wyjścia 0 zawsze; liczba zdarzeń w ostatniej linii stderr."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old_p, new_p = sys.argv[1], sys.argv[2]
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
date, source = arg('--date'), arg('--source', 'aktualizacja')
A, B = json.load(open(old_p, encoding='utf-8')), json.load(open(new_p, encoding='utf-8'))
an, bn = A['nodes'], B['nodes']; ae, be = A['edges'], B['edges']
ev = []
def add(kind, node, **kw): ev.append(dict({'date': date, 'source': source, 'kind': kind, 'nodeId': node, 'nodeName': (bn.get(node) or an.get(node) or {}).get('name')}, **kw))
def people(n): return {p.get('name'): p for p in ((n.get('people') or {}).get('people') or []) if p.get('name')}
for i in sorted(set(bn) - set(an)): add('node_added', i, type=bn[i].get('type'))
for i in sorted(set(an) - set(bn)): add('node_removed', i, type=an[i].get('type'))
for i in sorted(set(an) & set(bn)):
    o, n = an[i], bn[i]
    for f in ('name', 'status', 'seatsCount', 'parent', 'head'):
        if o.get(f) != n.get(f): add('node_changed', i, field=f, old=o.get(f), new=n.get(f))
    if (o.get('legalSource') or {}).get('act') != (n.get('legalSource') or {}).get('act'): add('legal_basis_changed', i, old=(o.get('legalSource') or {}).get('act'), new=(n.get('legalSource') or {}).get('act'))
    po, pn = people(o), people(n)
    for name in sorted(set(pn) - set(po)): add('person_in', i, person=name, position=pn[name].get('positionName'), acting=bool(pn[name].get('acting')), evidence=pn[name].get('sourceUrl'))
    for name in sorted(set(po) - set(pn)): add('person_out', i, person=name, position=po[name].get('positionName'))
    for name in sorted(set(po) & set(pn)):
        for f in ('positionName', 'acting', 'status', 'startedAt', 'party'):
            if po[name].get(f) != pn[name].get(f): add('person_changed', i, person=name, field=f, old=po[name].get(f), new=pn[name].get(f), evidence=pn[name].get('sourceUrl'))
    co, cn = (o.get('people') or {}).get('count'), (n.get('people') or {}).get('count')
    if co != cn: add('node_changed', i, field='people.count', old=co, new=cn)
key = lambda e: (e['fromId'], e['toId'], e['type'])
ko, kn = {key(e) for e in ae.values()}, {key(e) for e in be.values()}
for f, t, ty in sorted(kn - ko): ev.append({'date': date, 'source': source, 'kind': 'edge_added', 'type': ty, 'fromId': f, 'toId': t})
for f, t, ty in sorted(ko - kn): ev.append({'date': date, 'source': source, 'kind': 'edge_removed', 'type': ty, 'fromId': f, 'toId': t})
if ev and '--no-append' not in sys.argv:
    with open(os.path.join(ROOT, 'data/pl/changes.jsonl'), 'a', encoding='utf-8') as fh:
        for e in ev: fh.write(json.dumps(e, ensure_ascii=False) + '\n')
LABEL = {'node_added': 'Nowe węzły', 'node_removed': 'Usunięte węzły', 'node_changed': 'Zmiany w węzłach', 'legal_basis_changed': 'Zmiana podstawy prawnej', 'person_in': 'Nowe osoby na stanowiskach', 'person_out': 'Osoby, które odeszły', 'person_changed': 'Zmiany przy osobach', 'edge_added': 'Nowe relacje', 'edge_removed': 'Usunięte relacje'}
if not ev: print('Bez zmian merytorycznych.')
for kind, label in LABEL.items():
    rows = [e for e in ev if e['kind'] == kind]
    if not rows: continue
    print(f'\n**{label} ({len(rows)})**')
    for e in rows[:40]:
        if kind in ('person_in', 'person_out'): print(f"- {e['person']}, {e.get('position') or ''} · {e['nodeName']}" + (f" · [źródło]({e['evidence']})" if e.get('evidence') else ''))
        elif kind == 'person_changed': print(f"- {e['person']} ({e['nodeName']}): {e['field']} {e['old']!r} → {e['new']!r}")
        elif kind.startswith('edge'): print(f"- {e['type']}: {(bn.get(e['fromId']) or an.get(e['fromId']) or {}).get('name')} → {(bn.get(e['toId']) or an.get(e['toId']) or {}).get('name')}")
        elif kind in ('node_changed', 'legal_basis_changed'): print(f"- {e['nodeName']}: {e.get('field', 'akt')} {e.get('old')!r} → {e.get('new')!r}")
        else: print(f"- {e['nodeName']} (`{e['nodeId']}`)")
    if len(rows) > 40: print(f'- … i {len(rows) - 40} więcej')
print(len(ev), file=sys.stderr)
