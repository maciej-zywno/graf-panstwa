#!/usr/bin/env python3
"""Walidator chunku grafu: python3 scripts/validate-chunk.py data/pl/chunks/<key>.json
Sprawdza schemat, enumy, referencje (w chunku lub w ids-canon.json), spójność head/headOf. Exit 1 przy błędach."""
import json, sys, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = {'constituency','elected','department','commission','advisory','dept_head','political_group'}
SUBTYPES = {'legislature','chamber','ministry','chancellery','central_office','executive_agency','state_fund','state_legal_person','court','tribunal','regulatory_body','oversight_body','council','government_corporation','voivode','advisory_body','adjudicative_body','military','service','inspection','institute','committee','parliamentary_club','parliamentary_circle','other'}
SECTORS = {'legislative','executive','judicial','independent'}
RINGS = {'sovereign','highest','oversight','cabinet','administration','satellite'}
EDGE_TYPES = {'appoints','confirms','elects','nominates','oversees','ex_officio','advises','administers','dept_head','office'}
NODE_STATUS = {'active','disputed','vacant','pending_abolition','unverified'}
PERSON_STATUS = {'verified','unverified','acting','disputed'}
ID_RE = re.compile(r'^pl-[a-z0-9]+(-[a-z0-9]+)*$')

def main(path):
    errors, warns = [], []
    d = json.load(open(path, encoding='utf-8'))
    canon = json.load(open(os.path.join(ROOT,'data/pl/ids-canon.json'), encoding='utf-8'))
    canon_ids = set(canon['core'].keys())
    for g in canon['ministries'].values():
        for mid, v in g.items(): canon_ids.add(mid); canon_ids.add(v['minister'])
    nodes, edges = d.get('nodes', {}), d.get('edges', {})
    if not isinstance(nodes, dict) or not isinstance(edges, dict): errors.append('nodes/edges muszą być obiektami {id: …}'); print('\n'.join(errors)); sys.exit(1)
    known = set(nodes.keys()) | canon_ids
    def ref_ok(x): return x in known
    for nid, n in nodes.items():
        p = f'node {nid}'
        if not ID_RE.match(nid): errors.append(f'{p}: zły format id')
        if n.get('id') != nid: errors.append(f'{p}: id != klucz')
        for f in ('type','sector','ring','name','description'):
            if not n.get(f): errors.append(f'{p}: brak pola {f}')
        if n.get('type') not in TYPES: errors.append(f'{p}: type={n.get("type")}')
        if n.get('subtype') and n['subtype'] not in SUBTYPES: errors.append(f'{p}: subtype={n["subtype"]}')
        if n.get('sector') not in SECTORS: errors.append(f'{p}: sector={n.get("sector")}')
        if n.get('ring') not in RINGS: errors.append(f'{p}: ring={n.get("ring")}')
        if n.get('parent') and n.get('ring') != 'satellite': warns.append(f'{p}: ma parent, a ring != satellite')
        if n.get('ring') == 'satellite' and not n.get('parent'): errors.append(f'{p}: ring=satellite bez parent')
        if n.get('status') and n['status'] not in NODE_STATUS: errors.append(f'{p}: status={n["status"]}')
        if len(n.get('description','')) > 600: warns.append(f'{p}: opis > 600 znaków')
        ls = n.get('legalSource')
        if n.get('type') != 'constituency':
            if not ls or not isinstance(ls, dict) or not ls.get('url','').startswith('http') or not ls.get('title'): errors.append(f'{p}: legalSource wymaga {{title,url}}')
        for f in ('parent','head','headOf'):
            if n.get(f) and not ref_ok(n[f]): errors.append(f'{p}: {f} → nieznany id {n[f]}')
        if n.get('type') == 'dept_head' and not n.get('headOf'): warns.append(f'{p}: dept_head bez headOf')
        if n.get('head') and n['head'] in nodes and nodes[n['head']].get('headOf') != nid: errors.append(f'{p}: head {n["head"]} nie ma headOf={nid}')
        ppl = n.get('people')
        if ppl is not None:
            if not isinstance(ppl, dict) or ppl.get('type') not in ('people','count'): errors.append(f'{p}: people.type musi być people|count')
            elif ppl['type'] == 'people':
                for i, per in enumerate(ppl.get('people', [])):
                    q = f'{p} people[{i}]'
                    for f in ('id','name','positionName','sourceUrl'):
                        if not per.get(f): errors.append(f'{q}: brak {f}')
                    if per.get('id') and not ID_RE.match(per['id']): errors.append(f'{q}: zły format id osoby')
                    if per.get('startedAt') and not re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', per['startedAt']): errors.append(f'{q}: startedAt format YYYY[-MM[-DD]]')
                    if per.get('status') and per['status'] not in PERSON_STATUS: errors.append(f'{q}: status={per["status"]}')
                    if per.get('type') and per['type'] not in ('appointed','elected'): errors.append(f'{q}: type appointed|elected')
        prov = n.get('provenance')
        if not prov or not prov.get('sources'): warns.append(f'{p}: brak provenance.sources')
    for eid, e in edges.items():
        p = f'edge {eid}'
        if e.get('id') != eid: errors.append(f'{p}: id != klucz')
        if e.get('type') not in EDGE_TYPES: errors.append(f'{p}: type={e.get("type")}')
        for f in ('fromId','toId'):
            if not e.get(f): errors.append(f'{p}: brak {f}')
            elif not ref_ok(e[f]): errors.append(f'{p}: {f} → nieznany id {e[f]}')
        if e.get('type') != 'dept_head' and not e.get('cite'): warns.append(f'{p}: brak cite')
        if e.get('citeUrl') and not e['citeUrl'].startswith('http'): errors.append(f'{p}: citeUrl nie jest URL')
        if e.get('type') == 'dept_head':
            f, t = e.get('fromId'), e.get('toId')
            if f in nodes and nodes[f].get('head') != t: errors.append(f'{p}: dept_head niespójny z nodes[{f}].head')
    # duplicates of people ids across nodes
    seen = {}
    for nid, n in nodes.items():
        for per in (n.get('people') or {}).get('people', []) if (n.get('people') or {}).get('type') == 'people' else []:
            seen.setdefault(per.get('id'), []).append(nid)
    for pid, where in seen.items():
        if len(where) > 1: warns.append(f'osoba {pid} występuje w {len(where)} węzłach: {where} (OK jeśli łączy funkcje, sprawdź)')
    ext = sorted({x for e in edges.values() for x in (e.get('fromId'), e.get('toId')) if x and x not in nodes} | {n[f] for n in nodes.values() for f in ('parent','head','headOf') if n.get(f) and n[f] not in nodes})
    print(f'{os.path.basename(path)}: {len(nodes)} węzłów, {len(edges)} krawędzi, {sum(len((n.get("people") or {}).get("people", [])) for n in nodes.values() if (n.get("people") or {}).get("type")=="people")} osób; referencje zewnętrzne (kanon): {len(ext)}')
    for w in warns: print('WARN', w)
    for e in errors: print('ERROR', e)
    print('WYNIK:', 'OK' if not errors else f'{len(errors)} błędów')
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main(sys.argv[1])
