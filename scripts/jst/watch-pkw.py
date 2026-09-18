#!/usr/bin/env python3
"""Strażnik zmian w samorządzie w toku kadencji 2024–2029 (portale wyników PKW na wybory.gov.pl).
Trzy listy: wybory uzupełniające/ponowne/przedterminowe do rad (radygmin_2024_2029), przedterminowe i ponowne wybory wójtów,
burmistrzów i prezydentów (wojtburmistrz_2024_2029), referenda lokalne w sprawie odwołania organu (referendum_lokalne_2024_2029).
Skrypt niczego nie zmienia w danych grafu: porównuje listy z pamięcią data/jst/state/pkw.json i wypisuje nowe pozycje do przejrzenia.
Wyjście: Markdown na stdout; liczba nowych pozycji w ostatniej linii stderr. Kod wyjścia 0 przy sukcesie, 2 gdy źródło niedostępne
albo nieczytelne (stan zostaje nietknięty). Pierwszy przebieg tworzy stan bazowy i drukuje tylko podsumowanie źródeł.
Użycie: python3 scripts/jst/watch-pkw.py --date RRRR-MM-DD [--dry-run] [--state PLIK] [--base https://wybory.gov.pl]

Metoda. Źródłem są oficjalne portale wyników PKW dla kadencji 2024–2029 na wybory.gov.pl, które dla każdej zarządzonej elekcji
publikują wpis od dnia zarządzenia (postanowienia komisarza wyborczego) aż po wyniki. Portale to aplikacje JS, ale dane ciągną
z jednego stałego pliku `data/list.blob` (Protocol Buffers); skrypt dekoduje go własnym, minimalnym dekoderem wire-format
według schematu odczytanego z kodu portalu (numery pól: id, terminy, ścieżka TERYT, nazwa organu, podtyp, pytania referendalne).
Każda pozycja ma identyfikator PKW, datę głosowania, datę zarządzenia, sześciocyfrowy TERYT gminy/powiatu (z PKW, weryfikowany
w data/jst/index.json; przy braku dopasowanie po nazwie) i link do strony elekcji w portalu. Skrypt wykrywa nowe pozycje oraz
zmianę terminu lub zawieszenie już znanych. Nie wykrywa wygaśnięć mandatów ani obsadzenia mandatów bez wyborów (wstąpienie następnego
kandydata z listy): PKW publikuje je tylko jako PDF-y na 49 stronach delegatur KBW (dział „Zmiany w składach"), bez listy zbiorczej.
Nie wykrywa też zmian personalnych innych niż wybory (np. odwołania przez rozwiązanie rady ustawą) ani wyniku elekcji: po nią trzeba
wejść w link. Skrypt nie zna wyników wyborów z arkuszy PKW użytych do zbudowania warstwy JST, więc nie mówi, kto stracił mandat."""
import datetime, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request, urllib.robotparser
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
date = arg('--date'); dry = '--dry-run' in sys.argv; BASE = arg('--base', 'https://wybory.gov.pl').rstrip('/')
STATE = arg('--state', os.path.join(ROOT, 'data/jst/state/pkw.json')); INDEX = os.path.join(ROOT, 'data/jst/index.json')
if not date or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date): sys.exit('użycie: watch-pkw.py --date RRRR-MM-DD [--dry-run]')
UA = 'graf-panstwa/0.1 (+https://github.com/maciej-zywno/graf-panstwa; projekt obywatelski)'
try:
    import zoneinfo; TZ = zoneinfo.ZoneInfo('Europe/Warsaw')
except Exception: TZ = datetime.timezone.utc
def day(ts): return datetime.datetime.fromtimestamp(ts, TZ).strftime('%Y-%m-%d') if ts else None

# --- sieć: User-Agent, robots.txt, odstęp >= 1 s na host, 3 próby ---------------------------------------------------------------
_last = {}; _robots = {}
def fetch(url, tries=3):
    host = urllib.parse.urlsplit(url).netloc
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser(); rp.parse([])
        try:
            r = urllib.request.urlopen(urllib.request.Request(f'{BASE.split("//")[0]}//{host}/robots.txt', headers={'User-Agent': UA}), timeout=30)
            if r.headers.get_content_type() == 'text/plain': rp.parse(r.read().decode('utf-8', 'replace').splitlines())
        except Exception: pass   # brak pliku = brak ograniczeń (wybory.gov.pl zwraca pod /robots.txt zwykłą stronę HTML)
        _robots[host] = rp; _last[host] = time.monotonic()
    if not _robots[host].can_fetch(UA, url): raise RuntimeError(f'robots.txt zabrania pobrania {url}')
    for i in range(tries):
        wait = 1.0 - (time.monotonic() - _last.get(host, 0))
        if wait > 0: time.sleep(wait)
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=45); body = r.read(); _last[host] = time.monotonic()
            return body, r.headers.get_content_type()
        except Exception as e:
            _last[host] = time.monotonic()
            if i == tries - 1: raise RuntimeError(f'{url}: {e}')
            time.sleep(2 * (i + 1))

# --- minimalny dekoder Protocol Buffers (wire format) ze schematem odczytanym z kodu portali ------------------------------------
def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if c < 0x80: return r, i
def _fields(b):
    i = 0
    while i < len(b):
        k, i = _varint(b, i); f, w = k >> 3, k & 7
        if w == 0: v, i = _varint(b, i)
        elif w == 1: v = b[i:i + 8]; i += 8
        elif w == 2: n, i = _varint(b, i); v = b[i:i + n]; i += n
        elif w == 5: v = b[i:i + 4]; i += 4
        else: raise ValueError(f'nieznany typ pola protobuf: {w}')
        yield f, v
def decode(b, schema):
    """schema: {nr_pola: (nazwa, typ)}; typ: 's' string, 'z' sint (zigzag), 'i' int/enum, 'b' bool, dict = zagnieżdżony komunikat, [dict] = powtarzany."""
    d = {}
    for f, v in _fields(b):
        if f not in schema: continue
        name, ty = schema[f]
        if ty == 's': d[name] = v.decode('utf-8', 'replace')
        elif ty == 'z': d[name] = (v >> 1) ^ -(v & 1)
        elif ty == 'i': d[name] = v
        elif ty == 'b': d[name] = bool(v)
        elif isinstance(ty, list): d.setdefault(name, []).append(decode(v, ty[0]))
        else: d[name] = decode(v, ty)
    return d
PATH = {1: ('terytWoj', 'z'), 2: ('woj', 's'), 3: ('terytPow', 'z'), 4: ('pow', 's'), 5: ('terytGm', 'z'), 6: ('gm', 's')}
WYBORY = {1: ('id', 'z'), 2: ('aktualizacja', 'z'), 3: ('glosowanie', 'z'), 5: ('poziom', 'i'), 6: ('gmina', PATH), 8: ('typ', 'i'), 9: ('podtyp', 'i'),
          10: ('organ', 's'), 11: ('organD', 's'), 16: ('zarzadzenie', 'z'), 29: ('zawieszone', 'b')}
PYTANIE = {1: ('nr', 'z'), 2: ('tresc', 's'), 6: ('organ', 's')}
REFERENDUM = {1: ('id', 'z'), 2: ('aktualizacja', 'z'), 3: ('glosowanie', 'z'), 5: ('poziom', 'i'), 6: ('gmina', PATH), 7: ('zarzadzenie', 'z'),
              8: ('zawieszone', 'b'), 9: ('pytania', [PYTANIE]), 18: ('rodzaj', 'i')}
SOURCES = {  # klucz: (portal, nazwa pola listy, schemat pozycji, opis)
    'rady': ('radygmin_2024_2029', 'wybory', WYBORY, 'wybory uzupełniające, ponowne i przedterminowe do rad gmin i powiatów'),
    'wojt': ('wojtburmistrz_2024_2029', 'wybory', WYBORY, 'przedterminowe i ponowne wybory wójtów, burmistrzów i prezydentów miast'),
    'referenda': ('referendum_lokalne_2024_2029', 'referenda', REFERENDUM, 'referenda lokalne w sprawie odwołania organu (rady lub wójta)')}
PODTYP = {0: 'uzupełniające', 1: 'ponowne', 2: 'przedterminowe'}   # 3, 4: portal nie ma etykiety; w danych to pierwsze wybory w nowo utworzonej gminie
RODZAJ = {0: 'gminne', 1: 'powiatowe', 2: 'wojewódzkie'}

# --- jednostka: TERYT z PKW zweryfikowany w index.json, w odwodzie dopasowanie po nazwie w tym samym powiecie ------------------
index = json.load(open(INDEX, encoding='utf-8'))['units']; by_teryt = {u['t']: u for u in index}
def norm(s): s = unicodedata.normalize('NFD', s.lower().replace('ł', 'l')); return re.sub(r'[^a-z0-9 ]', '', ''.join(c for c in s if unicodedata.category(c) != 'Mn')).strip()
def unit_for(path):
    teryt = next((f'{path[k]:06d}' for k in ('terytGm', 'terytPow', 'terytWoj') if path.get(k)), None)
    if teryt in by_teryt: return teryt, by_teryt[teryt]['n']
    name = re.sub(r'^(gm|m)\. ', '', path.get('gm') or path.get('pow') or path.get('woj') or ''); prefix = (teryt or '')[:4]
    hits = [u for u in index if u['t'].startswith(prefix) and norm(u['n'].split(' ', 1)[-1]) == norm(name)]
    return teryt, hits[0]['n'] if len(hits) == 1 else None
def item(src, e):
    portal, _, _, _ = SOURCES[src]; path = e.get('gmina') or {}; teryt, unit = unit_for(path)
    if src == 'referenda':
        title = f"Referendum {RODZAJ.get(e.get('rodzaj', 0), 'lokalne')} w sprawie " + (' oraz '.join(p.get('tresc', '') for p in e.get('pytania', [])) or '?')
    else:
        rodzaj = PODTYP.get(e.get('podtyp', 0), 'w nowo utworzonej jednostce')
        title = f"Wybory {rodzaj} {'do ' if src == 'rady' else ''}{e.get('organD') or e.get('organ') or '?'}"
    powiat = path.get('pow') if path.get('gm') and path.get('pow') and path['pow'] != re.sub(r'^m\. ', '', path['gm']) else None   # miasto na prawach powiatu: nie powtarzaj nazwy
    where = ', '.join(x for x in (path.get('gm') or path.get('pow') or path.get('woj'), f'pow. {powiat}' if powiat else None, f"woj. {path['woj']}" if path.get('woj') else None) if x)
    return {'id': f'{src}/{e["id"]}', 'src': src, 'title': title, 'date': day(e.get('glosowanie')), 'announced': day(e.get('zarzadzenie')), 'teryt': teryt, 'unit': unit,
            'unitPkw': where, 'url': f'{BASE}/{portal}/pl/{e["id"]}/home', 'suspended': bool(e.get('zawieszone')), 'level': e.get('poziom', 0)}

# --- pobranie i porównanie ze stanem -------------------------------------------------------------------------------------------
state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {'items': {}, 'sources': {}}
first = not state['items']; known = state['items']; current = {}; sources = {}
try:
    for src, (portal, listfield, schema, desc) in SOURCES.items():
        url = f'{BASE}/{portal}/data/list.blob'; body, ctype = fetch(url)
        if ctype != 'application/octet-stream' or not body: raise RuntimeError(f'{url}: odpowiedź nie jest plikiem danych ({ctype}, {len(body)} B)')
        try: lst = decode(body, {1: (listfield, [schema]), 2: ('aktualizacja', 'z')})
        except Exception as e: raise RuntimeError(f'{url}: nie da się zdekodować ({e})')
        rows = [r for r in lst.get(listfield, []) if r.get('id')]
        if not rows or 'aktualizacja' not in lst: raise RuntimeError(f'{url}: pusta lub niekompletna lista')
        prev = state['sources'].get(src, {}).get('count', 0)
        if len(rows) < prev * 0.5: raise RuntimeError(f'{url}: lista skurczyła się z {prev} do {len(rows)} pozycji; wygląda na ucięte dane')
        for r in rows: it = item(src, r); current[it['id']] = it
        dates = sorted(x['date'] for x in current.values() if x['src'] == src and x['date'])
        sources[src] = {'url': url, 'desc': desc, 'count': len(rows), 'updatedAt': day(lst['aktualizacja']), 'dateRange': [dates[0], dates[-1]] if dates else None}
except RuntimeError as e:
    print(f'Strażnik PKW: źródło niedostępne, stan nietknięty. {e}', file=sys.stderr); sys.exit(2)
new = [it for k, it in current.items() if k not in known]
changed = [(known[k], it) for k, it in current.items() if k in known and (known[k]['date'] != it['date'] or known[k]['suspended'] != it['suspended'])]
gone = [k for k in known if k not in current]
for k, it in current.items(): known[k] = dict(it, seenAt=known.get(k, {}).get('seenAt') or date)
state.update({'checkedAt': date, 'sources': sources, 'baselineAt': state.get('baselineAt') or date})
if not dry:
    os.makedirs(os.path.dirname(STATE), exist_ok=True); json.dump(state, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)

def line(it): return f"{it['date'] or 'termin nieznany'} — {it['title']} — " + (f"{it['unit']} (`{it['teryt']}`)" if it['unit'] else f"{it['unitPkw']} (`{it['teryt']}`, brak w index.json)") + f" — [PKW]({it['url']})" + (f", zarządzone {it['announced']}" if it['announced'] else '') + (' — **zawieszone**' if it['suspended'] else '')
out = []
if first:
    out.append(f'### Wybory i referenda w toku kadencji 2024–2029 (PKW): stan bazowy z {date}\nPierwszy przebieg: wszystkie pozycje weszły do stanu bez zgłaszania jako nowe.\n')
    for src, s in sources.items():
        latest = max((x for x in current.values() if x['src'] == src), key=lambda x: (x['announced'] or '', x['date'] or ''))
        out.append(f"- **{s['desc']}**: <{s['url']}>, pozycji: {s['count']}, głosowania {s['dateRange'][0]} – {s['dateRange'][1]}, dane PKW z {s['updatedAt']}. Najnowsza: {line(latest)}")
else:
    if new:
        out.append(f'### Wybory i referenda w toku kadencji 2024–2029: nowe pozycje w PKW ({len(new)})\nSkrypt niczego nie zmienił w danych. Po głosowaniu sprawdź wynik pod linkiem i popraw jednostkę w `data/jst/`.\n')
        out += [f'- [ ] {line(it)}' for it in sorted(new, key=lambda x: (x['date'] or '', x['id']))]
    if changed:
        out.append(f'\n### Zmienione pozycje ({len(changed)})\n')
        for old, it in changed:
            what = [f"termin {old['date']} → **{it['date']}**"] if old['date'] != it['date'] else []
            if it['suspended'] != old['suspended']: what.append('**zawieszone**' if it['suspended'] else 'odwieszone')
            out.append(f"- [ ] {it['title']} — {it['unit'] or it['unitPkw']}: {', '.join(what)} — [PKW]({it['url']})")
print('\n'.join(out) if out else 'Brak nowych wyborów i referendów w toku kadencji w portalach PKW.')
counts = ', '.join(f"{s}={sources[s]['count']}" for s in sources)
print(f'źródła: {counts}; zmienione: {len(changed)}; zniknęły ze źródła: {len(gone)}', file=sys.stderr)
print(0 if first else len(new), file=sys.stderr)
