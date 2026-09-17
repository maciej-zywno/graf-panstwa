#!/usr/bin/env python3
"""Buduje publiczną stronę grafpanstwa.pl w dist/site/: sama skórka D (wierna CivLab) + graph.json obok.
Przełącznik skórek i skórki robocze zostają wyłącznie w prototypie (dist/graf-panstwa.html).
Użycie: python3 scripts/build-site.py [--index]   # --index: pozwól wyszukiwarkom indeksować (domyślnie noindex)
"""
import json, os, shutil, sys, hashlib, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'dist', 'site'); DOMAIN = 'https://grafpanstwa.pl'
allow_index = '--index' in sys.argv
html = open(os.path.join(ROOT, 'viewer/variants/D-styl-civlab/index.html'), encoding='utf-8').read()
data = json.load(open(os.path.join(ROOT, 'data/pl/graph.json'), encoding='utf-8'))
blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8'); ver = hashlib.sha1(blob).hexdigest()[:10]
desc = 'Interaktywna mapa organów państwa polskiego: kto kogo powołuje, zatwierdza, kontroluje i nadzoruje. Każda relacja z podstawą prawną.'
head = f'''<link rel="canonical" href="{DOMAIN}/">
<meta name="robots" content="{'index,follow' if allow_index else 'noindex,nofollow'}">
<meta property="og:type" content="website"><meta property="og:url" content="{DOMAIN}/"><meta property="og:locale" content="pl_PL">
<meta property="og:title" content="Graf Państwa Polskiego"><meta property="og:description" content="{desc}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-12 -12 24 24'%3E%3Ccircle r='9' fill='none' stroke='%23e0562f' stroke-width='2.4' stroke-dasharray='3.4 1.6'/%3E%3Ccircle r='3' fill='%23e0562f'/%3E%3C/svg%3E">'''
assert html.count('</title>') == 1
html = html.replace('</title>', '</title>\n' + head, 1)
# dane obok strony, z wersją w adresie (długi cache bez ryzyka starych danych)
assert "params.get('data') || './graph.json'" in html
html = html.replace("params.get('data') || './graph.json'", f"params.get('data') || './graph.json?v={ver}'")
if os.path.isdir(SITE): shutil.rmtree(SITE)
os.makedirs(SITE)
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
open(os.path.join(SITE, 'graph.json'), 'wb').write(blob)
open(os.path.join(SITE, 'robots.txt'), 'w').write('User-agent: *\n' + ('Allow: /\n' if allow_index else 'Disallow: /\n'))
open(os.path.join(SITE, 'BUILD.txt'), 'w').write(f"zbudowano: {datetime.datetime.now().isoformat(timespec='seconds')}\ndane: {ver}, {len(data['nodes'])} węzłów, {len(data['edges'])} relacji\nindeksowanie: {'tak' if allow_index else 'nie'}\n")
for f in sorted(os.listdir(SITE)): print(f"{f}: {os.path.getsize(os.path.join(SITE, f)) / 1024:.0f} KB")
