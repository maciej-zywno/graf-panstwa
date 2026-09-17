#!/usr/bin/env python3
"""Użycie: build-artifact.py [graph.json] [out.html] [viewer.html]
Buduje wersję viewera do publikacji jako Artifact: bez własnego szkieletu <html>/<head>/<body>,
z danymi grafu wstrzykniętymi inline (window.GRAPH_DATA). Użycie: python3 scripts/build-artifact.py [graph.json] [out.html]"""
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data/pl/graph.json')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'dist/artifact.html')
src = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, 'viewer/variants/D-styl-civlab/index.html')   # jedyny widok projektu (skórka D)
html = open(src, encoding='utf-8').read()
head = re.search(r'<head[^>]*>(.*?)</head>', html, re.S).group(1)
body = re.search(r'<body[^>]*>(.*?)</body>', html, re.S).group(1)
# z head zostawiamy title, style, linki do fontów i skrypty CDN; wyrzucamy meta charset/viewport (dodaje publikator)
head_keep = re.sub(r'<meta[^>]*>', '', head)
data = json.load(open(data_path, encoding='utf-8'))
inline = '<script>window.GRAPH_DATA = ' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';</script>\n'
# title na samą górę
title = re.search(r'<title>.*?</title>', head_keep, re.S)
head_keep = head_keep.replace(title.group(0), '') if title else head_keep
page = (title.group(0) + '\n' if title else '') + head_keep.strip() + '\n' + inline + body.strip() + '\n'
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(page)
print(f'{out}: {len(page)/1e6:.2f} MB; nodes={len(data.get("nodes",{}))} edges={len(data.get("edges",{}))}')
