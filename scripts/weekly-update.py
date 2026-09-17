#!/usr/bin/env python3
"""Cotygodniowa aktualizacja danych (uruchamiana przez GitHub Actions, działa też lokalnie).
Etap 1: parlament z API Sejmu i stron Senatu wchodzi automatycznie (decyzja właściciela z 18.09.2026), pod warunkiem że drugi,
niezależny odczyt potwierdził 100% nazwisk. Akty personalne z Monitora Polskiego i zmiany statusu podstaw prawnych NIE zmieniają danych:
trafiają na listę do przejrzenia przez człowieka.
Wynik: dist/weekly/report.md i dist/weekly/summary.json. Kod wyjścia 0 także przy problemie ze źródłem (dane zostają wtedy nietknięte).
Użycie: python3 scripts/weekly-update.py --date RRRR-MM-DD"""
import json, os, re, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
date = sys.argv[sys.argv.index('--date') + 1]; OUT = os.path.join(ROOT, 'dist/weekly'); os.makedirs(OUT, exist_ok=True)
FILES = ['data/pl/chunks/parlament.json', 'data/pl/chunks/parlament.verdicts.json', 'data/pl/graph.json']
bak = {f: open(f, 'rb').read() for f in FILES}
def restore():
    for f, b in bak.items(): open(f, 'wb').write(b)
def run(*cmd, timeout=1500):
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, timeout=timeout); return r.returncode, r.stdout, r.stderr
problem = None; summary_md = ''; events = 0
try:
    rc, out, err = run('scripts/build-parliament-chunk.py', '--today', date)
    if rc: raise RuntimeError('budowa części parlament: ' + (err or out)[-600:])
    rc, out, err = run('scripts/build-parliament-chunk.py', '--today', date, '--verify')
    m = re.search(r'potwierdzone (\d+) z (\d+)', out)
    if rc or not m: raise RuntimeError('weryfikacja części parlament: ' + (err or out)[-600:])
    ok, total = int(m.group(1)), int(m.group(2))
    if ok < total or total < 300: raise RuntimeError(f'drugi odczyt potwierdził {ok} z {total} osób; zmiany nie wchodzą automatycznie, dopóki nie będzie 100% (źródło mogło być chwilowo niedostępne)')
    rc, out, err = run('scripts/merge-chunks.py', '--today', date)
    if rc: raise RuntimeError('scalanie: ' + (err or out)[-600:])
    rc, out, err = run('scripts/validate-chunk.py', 'data/pl/graph.json')
    if rc: raise RuntimeError('walidacja schematu: ' + (out or err)[-600:])
    old = os.path.join(OUT, 'graph.before.json'); open(old, 'wb').write(bak['data/pl/graph.json'])
    rc, summary_md, err = run('scripts/diff-graph.py', old, 'data/pl/graph.json', '--date', date, '--source', 'parlament'); events = int((err.strip().splitlines() or ['0'])[-1]); os.remove(old)
    verified = f'Drugi odczyt źródeł potwierdził {ok} z {total} osób.'
except Exception as e:
    restore(); problem = str(e); verified = ''
rc, eli_md, err = run('scripts/watch-eli.py', '--date', date); lines = err.strip().splitlines(); findings = int(lines[-1]) if rc == 0 and lines and lines[-1].isdigit() else 0
if rc: eli_md = 'Strażnik aktów prawnych nie zadziałał: ' + err[-400:]
report = [f'# Aktualizacja tygodniowa {date}', '', '## Parlament (wchodzi automatycznie)', '']
report += [f'**Nie wprowadzono zmian.** Powód: {problem}'] if problem else [verified, '', summary_md.strip()]
report += ['', '## Akty prawne (do przejrzenia przez człowieka)', '', eli_md.strip(), '']
open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8').write('\n'.join(report))
json.dump({'date': date, 'events': events, 'findings': findings, 'problem': problem}, open(os.path.join(OUT, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('\n'.join(report))
