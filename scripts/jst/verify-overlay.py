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
tekstu przechodzą przez OCR: tesseract z pakietem `pol` w CI albo Apple Vision przez ocrmac na macOS). Awaria sieci lub serwera
(błąd połączenia, HTTP 5xx) ani blokada klienta (HTTP 403, 406, 429: zapory urzędów odrzucają adresy centrów danych, np. runnerów GitHuba)
nie zmienia werdyktu, tylko dopisuje notatkę „nie sprawdzono”; strona, która zniknęła (404, 410), daje `unverified`.
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
    'zastepca_prezydenta': ['wiceprezydent', 'zastępca prezydenta', 'zastępcy prezydenta', 'zastępczyni prezydenta', 'z-ca prezydenta', 'zastępca prezydent'],
    'skarbnik': ['skarbnik'],
    'sekretarz': ['sekretarz'],
    'burmistrz_dzielnicy': ['burmistrz'],
    'zastepca_burmistrza': ['zastępca burmistrza', 'zastępcy burmistrza', 'zastępczyni burmistrza', 'wiceburmistrz', 'z-ca burmistrza'],
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


import http.cookiejar
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch(url):
    """Zwraca (tekst, opis_błędu). Tekst po zdjęciu HTML; PDF przez pdftotext, skany przez OCR. Ciasteczka sesji są trzymane w obrębie przebiegu."""
    if not robots_ok(url):
        return '', 'robots.txt zabrania pobrania'
    host_wait(url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/pdf,*/*'})
        r = _opener.open(req, timeout=45); raw = r.read(); ct = r.headers.get('Content-Type', '')
        if not raw.strip() and r.status == 200:  # BIP m.st. Warszawy (Liferay) oddaje pustą odpowiedź na pierwsze żądanie bez ciasteczka sesji; drugie żądanie z ciasteczkiem ma treść
            host_wait(url); r = _opener.open(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/pdf,*/*'}), timeout=45); raw = r.read(); ct = r.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        return '', f'HTTP {e.code}'
    except Exception as e:
        return '', f'błąd pobrania: {type(e).__name__}: {str(e)[:80]}'
    if 'pdf' in ct or raw[:5] == b'%PDF-':
        try:
            out = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, timeout=60)
            txt = out.stdout.decode('utf-8', 'replace')
            if len(re.sub(r'[^\w]', '', txt)) >= 200:
                return txt, ''
            return ocr_pdf(raw)  # skan bez warstwy tekstu
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


OCR_VENV = os.path.expanduser('~/.venvs/ocr/bin/python')  # macOS: Vision przez pakiet ocrmac (Homebrew bez licencji Xcode nie instaluje tesseracta)


def ocr_pdf(raw):
    """Skany: pdftoppm → tesseract z pakietem polskim (Linux, CI) albo Apple Vision przez ocrmac (macOS). Zwraca (tekst, opis_błędu)."""
    import glob as _glob, shutil, tempfile
    d = tempfile.mkdtemp(prefix='gp-ocr-')
    try:
        src = os.path.join(d, 'in.pdf'); open(src, 'wb').write(raw)
        subprocess.run(['pdftoppm', '-r', '200', '-png', src, os.path.join(d, 'p')], check=True, timeout=300, capture_output=True)
        pages = sorted(_glob.glob(os.path.join(d, 'p-*.png')))
        if not pages:
            return '', 'PDF bez warstwy tekstu (skan); pdftoppm nie dał stron'
        if shutil.which('tesseract'):
            out = []
            for png in pages:
                r = subprocess.run(['tesseract', png, '-', '-l', 'pol'], capture_output=True, timeout=300); out.append(r.stdout.decode('utf-8', 'replace'))
            return '\n'.join(out), ''
        if os.path.exists(OCR_VENV):
            code = ("import sys, glob\nfrom ocrmac import ocrmac\n"
                    "for f in sorted(glob.glob(sys.argv[1] + '/p-*.png')):\n"
                    "    a = ocrmac.OCR(f, language_preference=['pl-PL'], recognition_level='accurate').recognize()\n"
                    "    print('\\n'.join(x[0] for x in sorted(a, key=lambda x: (-x[2][1], x[2][0]))))\n")
            r = subprocess.run([OCR_VENV, '-c', code, d], capture_output=True, timeout=900)
            return r.stdout.decode('utf-8', 'replace'), ('' if r.returncode == 0 else 'OCR (ocrmac) nie zadziałał: ' + r.stderr.decode('utf-8', 'replace')[-120:])
        return '', 'PDF bez warstwy tekstu (skan); brak OCR (tesseract z pakietem pol albo ocrmac)'
    except Exception as e:
        return '', f'OCR nie zadziałał: {type(e).__name__}: {str(e)[:80]}'
    finally:
        shutil.rmtree(d, ignore_errors=True)


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


def tok_re(t):
    """Wzorzec członu nazwiska odporny na odmianę: temat (bez 1–2 ostatnich liter) plus do 5 liter końcówki, np. „Jacka Zatorskiego” dla „Jacek Zatorski”."""
    stem = t[:max(3, len(t) - (2 if len(t) > 4 else 1))]
    return re.compile(r'(?<!\w)' + re.escape(stem) + r'\w{0,5}')


def name_positions(text, name):
    """Pozycje wszystkich wystąpień nazwiska: każdy człon imienia i nazwiska (≥3 znaki, w dowolnej odmianie) w oknie 80 znaków, w dowolnej kolejności."""
    toks = [t for t in re.split(r'[\s\-]+', norm(name)) if len(t) >= 3]
    if not toks:
        return []
    anchor = max(toks, key=len); pats = [tok_re(t) for t in toks]; out = []
    for m in tok_re(anchor).finditer(text):
        win = text[max(0, m.start() - 80):m.end() + 80]
        if all(pt.search(win) for pt in pats):
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
                if err and not text and (err.startswith('błąd pobrania') or re.match(r'HTTP (5\d\d|403|406|429)', err)):
                    # awaria sieci, serwera albo blokada klienta (403/429: zapory urzędów odrzucają adresy centrów danych, np. runnery GitHuba): werdykt zostaje, tylko notatka; strona zniknięta (404/410) albo skan bez OCR daje unverified niżej
                    p['note'] = f'nie sprawdzono {today}: {err}'; stats[p.get('verdict') if p.get('verdict') in stats else 'unverified'] += 1
                    print(f'??? {key} {pos["role"]:24} {p["name"]:32} {p["note"]}  {url}'); continue
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
