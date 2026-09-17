#!/usr/bin/env python3
"""Strażnik aktów prawnych (API ELI Sejmu, bez klucza). Dwa zadania:
1. Nowe akty personalne w Monitorze Polskim i Dzienniku Ustaw od poprzedniego przebiegu (powołania, odwołania, wybór, zmiany w składzie Rady Ministrów).
   Skrypt ich NIE wprowadza do grafu: wypisuje listę do przejrzenia z kandydatami na węzły, których dotyczą.
2. Status aktów, które są podstawą prawną węzłów (legalSource.act): sygnalizuje uchylenie albo inną zmianę statusu.
Stan między przebiegami: data/pl/state/eli.json. Wyjście: Markdown na stdout; liczba znalezisk w ostatniej linii stderr.
Użycie: python3 scripts/watch-eli.py --date RRRR-MM-DD [--limit-status N] [--dry-run]"""
import json, os, re, sys, time, unicodedata, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATE = os.path.join(ROOT, 'data/pl/state/eli.json')
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
date = arg('--date'); year = int(date[:4]); dry = '--dry-run' in sys.argv; limit = int(arg('--limit-status', '100000'))
UA = {'User-Agent': 'graf-panstwa/0.1 (+https://github.com/maciej-zywno/graf-panstwa; projekt obywatelski)', 'Accept': 'application/json'}
def jget(url, tries=3):
    for i in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read())
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 * (i + 1))
state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {'lastPos': {}, 'actStatus': {}}
graph = json.load(open(os.path.join(ROOT, 'data/pl/graph.json'), encoding='utf-8')); nodes = graph['nodes']
PERSONNEL = re.compile(r'zmianie w składzie Rady Ministrów|o powołaniu|o odwołaniu|w sprawie wyboru|w sprawie powołania|w sprawie odwołania|o wyborze|w sprawie stwierdzenia wygaśnięcia mandatu|o wstąpieniu|w sprawie obsadzenia mandatu|o powierzeniu', re.I)
SKIP = re.compile(r'o nadaniu (stopnia|orderu|odznacze)|tytułu profesora|o nadaniu tytułu|na stanowisku (sędziego|asesora)|na stanowisko (sędziego|asesora)', re.I)  # powołań zwykłych sędziów są setki rocznie, a graf nie ma pojedynczych sędziów
def norm(s): s = unicodedata.normalize('NFD', s.lower().replace('ł', 'l')); return ''.join(c for c in s if unicodedata.category(c) != 'Mn')
def stems(s): return {w[:6] for w in re.findall(r'[a-z]{4,}', norm(s))} - {'rzeczy', 'polski', 'prezyd', 'postan', 'uchwal', 'sprawi', 'powola', 'odwola', 'wyboru'}
index = [(i, n['name'], stems(n['name'] + ' ' + ' '.join(n.get('aliases') or []))) for i, n in nodes.items() if n['type'] in ('dept_head', 'commission', 'elected', 'department') and n.get('ring') != 'satellite']
def candidates(title):
    t = stems(title); out = []
    for i, name, st in index:
        if len(st) >= 2 and st <= t: out.append((len(st), i, name))
    return [f'{name} (`{i}`)' for _, i, name in sorted(out, reverse=True)[:3]]
found = []; out = []
for pub in ('MP', 'DU'):
    items = (jget(f'https://api.sejm.gov.pl/eli/acts/{pub}/{year}') or {}).get('items', [])
    last = state['lastPos'].get(f'{pub}/{year}', 0); top = max([int(i['pos']) for i in items] + [last])
    fresh = [i for i in items if int(i['pos']) > last and PERSONNEL.search(i.get('title', '')) and not SKIP.search(i.get('title', ''))]
    if last == 0: fresh = []   # pierwszy przebieg tylko ustawia punkt startu, żeby nie zalać przeglądu aktami z całego roku
    for i in sorted(fresh, key=lambda x: int(x['pos'])): found.append((pub, i))
    state['lastPos'][f'{pub}/{year}'] = top
if found:
    out.append(f'### Nowe akty personalne do przejrzenia ({len(found)})\nSkrypt niczego nie zmienił w danych. Dla każdego aktu sprawdź, czy dotyczy stanowiska z grafu, i popraw właściwą część w `data/pl/chunks/`.\n')
    for pub, i in found:
        eli = i['ELI']; cand = candidates(i['title']); out.append(f"- [ ] [{eli}](https://eli.gov.pl/eli/{eli}/ogl), ogłoszono {i.get('promulgation') or i.get('announcementDate')}: {i['title']}" + (f"\n  - możliwe węzły: {'; '.join(cand)}" if cand else ''))
# status aktów będących podstawą prawną
acts = sorted({(n.get('legalSource') or {}).get('act') for n in nodes.values()} - {None, ''}); changed = []; checked = 0
for act in acts[:limit]:
    if not re.fullmatch(r'(DU|MP)/\d{4}/\d+', act): continue
    try: d = jget(f'https://api.sejm.gov.pl/eli/acts/{act}')
    except Exception as e: changed.append((act, 'błąd pobrania', str(e)[:80])); continue
    checked += 1; st = d.get('status'); prev = state['actStatus'].get(act)
    if prev is not None and prev != st: changed.append((act, prev, st))
    elif prev is None and st and re.search(r'uchylon|nieobowiązując|wygaśnięcie|uznany za uchylony', st, re.I): changed.append((act, 'pierwsze sprawdzenie', st))
    state['actStatus'][act] = st; time.sleep(0.15)
if changed:
    out.append(f'\n### Podstawy prawne ze zmienionym statusem ({len(changed)})\n')
    for act, prev, st in changed:
        users = [n['name'] for n in nodes.values() if (n.get('legalSource') or {}).get('act') == act][:4]
        out.append(f"- [ ] [{act}](https://eli.gov.pl/eli/{act}/ogl): {prev} → **{st}**. Węzły: {', '.join(users)}")
state['checkedAt'] = date; state['actsChecked'] = checked
if not dry:
    os.makedirs(os.path.dirname(STATE), exist_ok=True); json.dump(state, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print('\n'.join(out) if out else 'Brak nowych aktów personalnych i zmian statusu podstaw prawnych.')
print(f'sprawdzono statusów aktów: {checked}', file=sys.stderr); print(len(found) + len(changed), file=sys.stderr)
