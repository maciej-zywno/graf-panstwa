#!/usr/bin/env python3
"""Niezależna weryfikacja nakładki samorządowej (organy spoza rejestrów PKW: zarządy, prezydia rad, zastępcy, skarbnicy, sekretarze).

Dla KAŻDEJ osoby w pliku nakładki pobiera od nowa jej `sourceUrl` i sprawdza, czy na stronie występuje nazwisko
razem ze słowem kluczowym funkcji (np. „starost", „marszał", „przewodnicz", „członek zarządu"). Wynik zapisuje w polu
`verdict` (`confirmed` albo `unverified` z powodem w `note`) i odświeża `meta.stats`.

Użycie:  python3 scripts/jst/verify-overlay.py data/jst/overlay/10.json [--only 1020] [--js] [--no-write] [--verbose]
  --only KEY   sprawdź tylko jednostkę o tym kluczu (można podać kilka razy)
  --js         wymuś Playwright (przeglądarka bez okna) dla wszystkich stron, nie tylko awaryjnie
  --no-write   nie zapisuj wyniku do pliku, tylko wypisz
Kod wyjścia: 0 gdy wszystko potwierdzone, 1 gdy są rekordy `unverified`, 2 przy błędzie wejścia.

Zasady sieci: User-Agent projektu, odstęp ≥1 s między żądaniami do tego samego hosta, robots.txt honorowany
(strona zabroniona → `unverified` z powodem, bez obchodzenia). Strony JS: najpierw zwykłe pobranie; gdy nazwiska nie ma,
a Playwright jest w node_modules, drugi odczyt przeglądarką. Ładunek Next.js (self.__next_f.push) jest dekodowany, bo
niektóre BIP-y (dostawca bip.net.pl) trzymają treść artykułu tylko tam. PDF-y czytane przez pdftotext (skany bez warstwy
tekstu dają `unverified`).
"""
import datetime, html, json, os, re, subprocess, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request, urllib.robotparser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA = 'graf-panstwa/0.1 (+https://github.com/maciej-zywno/graf-panstwa; projekt obywatelski)'
PW = os.path.join(ROOT, 'node_modules', '@playwright', 'test')
KEYWORDS = {  # słowa kluczowe funkcji; wystarczy jedno; porównanie bez wielkości liter, po normalizacji spacji
    'marszalek': ['marszałek', 'marszałkiem', 'marszałka'],
    'wicemarszalek': ['wicemarszał'],
    'czlonek_zarzadu': ['członek zarządu', 'członkowie zarządu', 'członkiem zarządu', 'członka zarządu', 'członkini zarządu', 'skład zarządu', 'zarząd powiatu', 'zarząd województwa'],
    'starosta': ['starost'],
    'wicestarosta': ['wicestarost'],
    'przewodniczacy_rady': ['przewodnicz'],
    'wiceprzewodniczacy_rady': ['wiceprzewodnicz'],
    'zastepca_prezydenta': ['wiceprezydent', 'zastępca prezydenta', 'zastępcy prezydenta', 'z-ca prezydenta', 'zastępca prezydent'],
    'skarbnik': ['skarbnik'],
    'sekretarz': ['sekretarz'],
}
WINDOW = 600  # znaki: jak blisko nazwiska musi stać słowo kluczowe
_last = {}


def host_wait(url):
    h = urllib.parse.urlsplit(url).netloc
    d = time.time() - _last.get(h, 0)
    if d < 1.1:
        time.sleep(1.1 - d)
    _last[h] = time.time()


_robots = {}


def robots_ok(url):
    u = urllib.parse.urlsplit(url); base = f'{u.scheme}://{u.netloc}'
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            host_wait(url)
            r = urllib.request.urlopen(urllib.request.Request(base + '/robots.txt', headers={'User-Agent': UA}), timeout=20)
            rp.parse(r.read().decode('utf-8', 'replace').splitlines()) if r.status == 200 else rp.parse([])
        except Exception:
            rp.parse([])
        _robots[base] = rp
    rp = _robots[base]
    return rp.can_fetch(UA, url) and rp.can_fetch('graf-panstwa', url)


def fetch(url):
    """Zwraca (tekst, opis_błędu). Tekst po zdjęciu HTML; PDF przez pdftotext."""
    if not robots_ok(url):
        return '', 'robots.txt zabrania pobrania'
    host_wait(url)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/pdf,*/*'}), timeout=45)
        raw = r.read(); ct = r.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        return '', f'HTTP {e.code}'
    except Exception as e:
        return '', f'błąd pobrania: {type(e).__name__}: {str(e)[:80]}'
    if 'pdf' in ct or raw[:5] == b'%PDF-':
        try:
            out = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, timeout=60)
            txt = out.stdout.decode('utf-8', 'replace')
            return txt, ('' if txt.strip() else 'PDF bez warstwy tekstu (skan)')
        except FileNotFoundError:
            return '', 'brak pdftotext'
    enc = 'utf-8'
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000])
    if m:
        enc = m.group(1).decode()
    elif 'charset=' in ct:
        enc = ct.split('charset=')[1].strip()
    try:
        body = raw.decode(enc, 'replace')
    except Exception:
        body = raw.decode('utf-8', 'replace')
    return to_text(body), ''


def fetch_js(url):
    if not os.path.isdir(PW):
        return '', 'brak Playwrighta w node_modules'
    if not robots_ok(url):
        return '', 'robots.txt zabrania pobrania'
    host_wait(url)
    js = (
        "const {chromium}=require(process.argv[1]);(async()=>{const b=await chromium.launch({headless:true});"
        "const c=await b.newContext({userAgent:process.argv[3]});const p=await c.newPage();"
        "try{await p.goto(process.argv[2],{waitUntil:'networkidle',timeout:60000});}catch(e){}"
        "await p.waitForTimeout(2500);process.stdout.write(await p.content());await b.close();})();"
    )
    try:
        r = subprocess.run(['node', '-e', js, PW, url, UA], capture_output=True, text=True, timeout=120)
    except Exception as e:
        return '', f'Playwright: {type(e).__name__}'
    if not r.stdout.strip():
        return '', 'Playwright: pusta odpowiedź ' + r.stderr[-120:].strip()
    return to_text(r.stdout), ''


def rsc_payload(body):
    out = []
    for m in re.finditer(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', body):
        try:
            out.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            pass
    return '\n'.join(out)


def to_text(body):
    if 'self.__next_f.push' in body:
        body = body + '\n' + rsc_payload(body)
    body = re.sub(r'(?is)<(script|style|noscript|svg).*?</\1>', ' ', body)
    body = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th|section|article|header|footer|nav|ul|ol|table|dd|dt|option)>', '\n', body)
    body = re.sub(r'(?s)<!--.*?-->', ' ', body)
    body = re.sub(r'<[^>]+>', ' ', body)
    return html.unescape(body)


def norm(s):
    s = unicodedata.normalize('NFC', s).casefold()
    s = s.replace('\xa0', ' ').replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', s)


def name_positions(text, name):
    """Pozycje wszystkich wystąpień nazwiska: każdy człon imienia i nazwiska (≥3 znaki) w oknie 80 znaków, w dowolnej kolejności."""
    toks = [t for t in re.split(r'[\s\-]+', norm(name)) if len(t) >= 3]
    if not toks:
        return []
    anchor = max(toks, key=len); out = []
    for m in re.finditer(re.escape(anchor), text):
        win = text[max(0, m.start() - 80):m.end() + 80]
        if all(t in win for t in toks):
            out.append(m.start())
    return out


def check(text, person, role):
    t = norm(text)
    positions = name_positions(t, person['name'])
    kws = KEYWORDS.get(role, [])
    if not positions:
        return 'unverified', 'nazwiska nie ma w treści strony'
    quote_ok = norm(person.get('quote') or '') in t if person.get('quote') else None
    for pos in positions:  # nazwisko może stać kilka razy (menu, treść); wystarczy jedno wystąpienie obok słowa funkcji
        win = t[max(0, pos - WINDOW):pos + WINDOW]
        if any(k in win for k in kws):
            note = None if quote_ok in (True, None) else 'potwierdzone nazwisko i funkcja; cytat nie występuje już dosłownie'
            return 'confirmed', note
    anywhere = [k for k in kws if k in t]
    if anywhere:
        return 'unverified', f'nazwisko jest ({len(positions)}x), ale słowo funkcji ({anywhere[0]}) nie stoi w pobliżu (±{WINDOW} zn.)'
    return 'unverified', 'nazwisko jest, brak słowa kluczowego funkcji na stronie'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__); sys.exit(2)
    path = args[0]; only = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--only']
    force_js = '--js' in sys.argv; write = '--no-write' not in sys.argv; verbose = '--verbose' in sys.argv
    data = json.load(open(path, encoding='utf-8'))
    cache = {}
    stats = {'people': 0, 'confirmed': 0, 'unverified': 0}
    today = datetime.date.today().isoformat()
    for key, unit in data['units'].items():
        if only and key not in only:
            continue
        for pos in unit.get('positions', []):
            for p in pos.get('people', []):
                stats['people'] += 1
                url = p['sourceUrl']
                if url not in cache:
                    cache[url] = fetch_js(url) if force_js else fetch(url)
                text, err = cache[url]
                verdict, note = ('unverified', err) if err and not text else check(text, p, pos['role'])
                if verdict == 'unverified' and not force_js and not (err and 'robots' in err):
                    jtext, jerr = fetch_js(url)  # drugi odczyt przeglądarką: strony JS
                    if jtext:
                        v2, n2 = check(jtext, p, pos['role'])
                        if v2 == 'confirmed':
                            verdict, note = v2, (n2 or '') + ' (odczyt Playwright)'
                            note = note.strip()
                p['verdict'] = verdict; p['note'] = note; p['verifiedAt'] = today
                stats[verdict] += 1
                mark = 'OK ' if verdict == 'confirmed' else 'NIE'
                if verbose or verdict != 'confirmed':
                    print(f'{mark} {key} {pos["role"]:24} {p["name"]:32} {note or ""}  {url}')
    # statystyki liczone z całego pliku (także przy --only), żeby meta zawsze zgadzała się z rekordami
    total = {'people': 0, 'confirmed': 0, 'unverified': 0, 'unchecked': 0}
    for unit in data['units'].values():
        for pos in unit.get('positions', []):
            for p in pos.get('people', []):
                total['people'] += 1; total[p.get('verdict') or 'unchecked'] += 1
    data['meta'].setdefault('stats', {}).update({k: v for k, v in total.items() if k != 'unchecked' or v})
    if not total['unchecked']:
        data['meta']['stats'].pop('unchecked', None)
    data['meta']['verifiedAt'] = today
    if write:
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'osoby: {stats["people"]}, potwierdzone: {stats["confirmed"]}, niepotwierdzone: {stats["unverified"]}')
    sys.exit(1 if stats['unverified'] else 0)


if __name__ == '__main__':
    main()
