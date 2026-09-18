#!/usr/bin/env python3
"""Sprawdza cytaty szablonów samorządowych na tekstach ustaw z ELI: dla każdego cytatu pobiera tekst aktu (PDF → pdftotext),
wycina wskazany artykuł i wymaga, żeby zawierał wszystkie słowa z pola must. Kod wyjścia ≠ 0 przy jakiejkolwiek niezgodności.
Użycie: python3 scripts/jst/verify-templates.py [--offline]"""
import json, os, re, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(ROOT, 'data/jst/src'); os.makedirs(SRC, exist_ok=True)
T = json.load(open(os.path.join(ROOT, 'scripts/jst/templates.json'), encoding='utf-8')); UA = {'User-Agent': 'graf-panstwa/0.1 (+https://github.com/maciej-zywno/graf-panstwa; projekt obywatelski)'}
def text_of(eli):
    pdf = os.path.join(SRC, eli.replace('/', '-') + '.pdf')
    if not os.path.exists(pdf):
        if '--offline' in sys.argv: raise SystemExit(f'brak {pdf} w pamięci podręcznej')
        open(pdf, 'wb').write(urllib.request.urlopen(urllib.request.Request(f'https://api.sejm.gov.pl/eli/acts/{eli}/text.pdf', headers=UA), timeout=90).read()); time.sleep(1)
    return subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True, check=True).stdout
def articles(txt):
    txt = re.sub(r'-\n\s*', '', txt); parts = re.split(r'\n\s*Art\.\s*(\d+[a-z]*)\.', '\n' + txt); out = {}
    for i in range(1, len(parts) - 1, 2): out.setdefault(parts[i], ''); out[parts[i]] += ' ' + parts[i + 1]
    return {k: re.sub(r'\s+', ' ', v) for k, v in out.items()}
cache = {}; bad = []; ok = 0
for key, c in T['cites'].items():
    act = T['acts'][c['act']]; arts = cache.setdefault(act['text'], articles(text_of(act['text']))); body = arts.get(c['art'], '')
    miss = [m for m in c['must'] if re.sub(r'\s+', ' ', m).lower() not in body.lower()]
    if not body: bad.append(f"{key}: brak art. {c['art']} w {act['text']}")
    elif miss: bad.append(f"{key}: art. {c['art']} ({act['text']}) nie zawiera: {miss} | początek: {body[:160]!r}")
    else: ok += 1
print(f'cytaty potwierdzone: {ok} z {len(T["cites"])}')
for b in bad: print('NIEZGODNE', b)
sys.exit(1 if bad else 0)
