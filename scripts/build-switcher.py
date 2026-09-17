#!/usr/bin/env python3
"""Buduje jedną stronę z przełącznikiem skórek (dropdown w prawym górnym rogu).
Powłoka trzyma dane grafu i stan (wybrany węzeł, motyw, aktywna skórka); każda skórka to kompletny viewer
ładowany do <iframe srcdoc>. Kontrakt skórki: czyta window.GRAPH_DATA, obsługuje #node=<id>, motyw w localStorage 'gp-theme'.
Użycie: python3 scripts/build-switcher.py [graph.json] [out.html]"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data/pl/graph.json')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'dist/graf-panstwa.html')
SKINS = [  # (id, etykieta, plik[, overlay]) — pierwsza pozycja jest domyślna; overlay=True: przełącznik pływa nad sceną i nie zabiera wysokości
    ('D', 'D · Styl CivLab', 'viewer/variants/D-styl-civlab/index.html', True),
]  # decyzja 17.09.2026: zostaje wyłącznie skórka D; pozostałe leżą w archive/skorki/. Przy jednej skórce przełącznik jest ukryty.
esc = lambda s: s.replace('</', '<\\/')
data_text = esc(json.dumps(json.load(open(data_path, encoding='utf-8')), ensure_ascii=False, separators=(',', ':')))
skins_js, embedded = [], []
for sid, label, rel, *flags in SKINS:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p): print('pomijam (brak pliku):', rel); continue
    html = open(p, encoding='utf-8').read()
    embedded.append(f'<script type="application/json" id="skin-{sid}">{esc(json.dumps(html, ensure_ascii=False))}</script>')
    skins_js.append({'id': sid, 'label': label, 'overlay': bool(flags and flags[0])})

SHELL = r'''<title>Graf Państwa Polskiego</title>
<style>
:root { --bar-bg:#fbfaf6; --bar-ink:#16181d; --bar-muted:#7c7a72; --bar-hair:rgba(22,24,29,.14); --bar-accent:#b8323f; --bar-field:#f0ede4;
  --font-ui:"IBM Plex Sans","Segoe UI",system-ui,sans-serif; --font-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bar-bg:#14181f; --bar-ink:#ece8de; --bar-muted:#8b877c; --bar-hair:rgba(236,232,222,.16); --bar-accent:#e0485a; --bar-field:#1a1f28; } }
:root[data-theme="dark"] { --bar-bg:#14181f; --bar-ink:#ece8de; --bar-muted:#8b877c; --bar-hair:rgba(236,232,222,.16); --bar-accent:#e0485a; --bar-field:#1a1f28; }
html, body { height:100%; }
body { margin:0; background:var(--bar-bg); color:var(--bar-ink); font:14px/1.3 var(--font-ui); display:flex; flex-direction:column; overflow:hidden; }
.bar { flex:none; display:flex; align-items:center; gap:12px; padding:6px 16px; border-bottom:1px solid var(--bar-hair); min-height:44px; box-sizing:border-box; }
.bar .tag { font:500 11px/1 var(--font-mono); letter-spacing:.11em; text-transform:uppercase; color:var(--bar-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0; }
.bar .tag b { color:var(--bar-accent); font-weight:500; }
.bar .sp { flex:1; min-width:0; }
.switch { display:flex; align-items:center; gap:6px; flex:none; }
.switch label { font:500 11px/1 var(--font-mono); letter-spacing:.09em; text-transform:uppercase; color:var(--bar-muted); }
.switch select, .switch button { font:500 13.5px/1 var(--font-ui); color:var(--bar-ink); background:var(--bar-field); border:1px solid var(--bar-hair); border-radius:6px; height:32px; }
.switch select { padding:0 30px 0 10px; max-width:52vw; appearance:none; -webkit-appearance:none; cursor:pointer;
  background-image:linear-gradient(45deg,transparent 50%,var(--bar-muted) 50%),linear-gradient(135deg,var(--bar-muted) 50%,transparent 50%); background-position:calc(100% - 15px) 13px,calc(100% - 10px) 13px; background-size:5px 5px; background-repeat:no-repeat; }
.switch button { width:32px; cursor:pointer; padding:0; }
.switch select:focus-visible, .switch button:focus-visible { outline:2px solid var(--bar-accent); outline-offset:1px; }
iframe { flex:1; width:100%; border:0; display:block; min-height:0; background:var(--bar-bg); }
@media (max-width:560px) { .bar .tag { display:none; } .switch label { display:none; } }
/* skórka z własnym układem całej strony: przełącznik pływa w prawym górnym rogu, scena dostaje pełną wysokość okna */
body.overlay { display:block; }
body.overlay iframe { position:absolute; inset:0; width:100%; height:100%; }
body.overlay .bar { position:absolute; top:14px; right:14px; z-index:5; padding:0; border:0; min-height:0; gap:0; background:transparent; }
body.overlay .bar .tag, body.overlay .bar .sp, body.overlay .switch label { display:none; }
body.overlay .switch { gap:4px; }
body.overlay .switch select, body.overlay .switch button { height:40px; border-radius:12px; border-color:transparent; box-shadow:0 1px 2px rgba(0,0,0,.06); }
body.overlay .switch select { width:140px; background-position:calc(100% - 15px) 17px,calc(100% - 10px) 17px; }
body.overlay .switch button { display:none; } /* strzałki znikają, zostają klawisze [ i ] */
@media (max-width:1240px) { body.overlay .switch select { width:60px; padding-right:24px; text-overflow:clip; } }
@media (max-width:760px) { body.overlay .bar { top:10px; right:10px; } }
body.single .bar { display:none; }
</style>
<div class="bar">
  <span class="tag">Prototyp · <b id="skin-name">widok</b></span><span class="sp"></span>
  <div class="switch">
    <label for="skin-select">Widok</label>
    <button id="skin-prev" type="button" title="Poprzedni widok ( [ )" aria-label="Poprzedni widok">‹</button>
    <select id="skin-select" title="Zmień widok grafu"></select>
    <button id="skin-next" type="button" title="Następny widok ( ] )" aria-label="Następny widok">›</button>
  </div>
</div>
<iframe id="stage" title="Widok grafu"></iframe>
__EMBEDDED__
<script type="application/json" id="graph-data">__DATA__</script>
<script>
(() => {
  const SKINS = __SKINS__;
  const DATA_TEXT = document.getElementById('graph-data').textContent;
  const frame = document.getElementById('stage'), sel = document.getElementById('skin-select'), nameEl = document.getElementById('skin-name');
  const state = { skin: null, node: null };
  const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch {} } };
  const nodeFromHash = h => { const m = /[#&](?:node|resort)=([^&]+)/.exec(h || ''); return m ? decodeURIComponent(m[1]) : null; };
  // Kod wstrzykiwany do każdej skórki: dane, stan początkowy, bezpieczne history w about:srcdoc, raportowanie stanu do powłoki.
  const barWidth = () => document.body.classList.contains('overlay') && !document.body.classList.contains('single') ? Math.ceil(document.querySelector('.bar').getBoundingClientRect().width) + 10 : 0;
  const bootstrap = node => '<script>window.GRAPH_DATA=' + DATA_TEXT + ';window.GP_EMBED=' + JSON.stringify({ topRight: barWidth() }) + ';<\/script><script>(' + function (hash) {
    const ps = history.pushState.bind(history), rs = history.replaceState.bind(history);
    const viaHash = u => { try { const s = String(u || ''); const i = s.indexOf('#'); location.hash = i >= 0 ? s.slice(i) : ''; } catch (e) {} };
    history.pushState = function (s, t, u) { try { ps(s, t, u); } catch (e) { viaHash(u); } };
    history.replaceState = function (s, t, u) { try { rs(s, t, u); } catch (e) { viaHash(u); } };
    if (hash) { try { location.hash = hash; } catch (e) {} }
    let lastH = null, lastT = null, lastTitle = null;
    setInterval(() => {
      const h = location.hash, t = document.documentElement.dataset.theme || null;
      if (h !== lastH) { lastH = h; parent.postMessage({ gp: 'hash', hash: h }, '*'); }
      if (t !== lastT) { lastT = t; parent.postMessage({ gp: 'theme', theme: t }, '*'); }
      if (document.title !== lastTitle) { lastTitle = document.title; parent.postMessage({ gp: 'title', title: lastTitle }, '*'); }
    }, 300);
    addEventListener('keydown', ev => { if (ev.target && /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName)) return; if (ev.key === '[' || ev.key === ']') parent.postMessage({ gp: 'cycle', dir: ev.key === ']' ? 1 : -1 }, '*'); });
  }.toString() + ')(' + JSON.stringify(node ? '#node=' + encodeURIComponent(node) : '') + ');<\/script>';
  function show(id, opts = {}) {
    const skin = SKINS.find(s => s.id === id) || SKINS[0];
    state.skin = skin.id; sel.value = skin.id; nameEl.textContent = skin.label; store.set('gp-skin-v2', skin.id); document.body.classList.toggle('overlay', !!skin.overlay);
    const html = JSON.parse(document.getElementById('skin-' + skin.id).textContent);
    const boot = bootstrap(state.node);
    frame.srcdoc = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, m => m + boot) : boot + html;
    if (!opts.silent) syncUrl();
  }
  function syncUrl() { try { history.replaceState(null, '', '#view=' + state.skin + (state.node ? '&node=' + encodeURIComponent(state.node) : '')); } catch {} }
  function cycle(dir) { const i = SKINS.findIndex(s => s.id === state.skin); show(SKINS[(i + dir + SKINS.length) % SKINS.length].id); }
  addEventListener('message', ev => {
    const m = ev.data; if (!m || ev.source !== frame.contentWindow) return;
    if (m.gp === 'hash') { state.node = nodeFromHash(m.hash); syncUrl(); }
    else if (m.gp === 'theme') { if (m.theme) document.documentElement.dataset.theme = m.theme; }
    else if (m.gp === 'title') { if (m.title) document.title = String(m.title).slice(0, 120); }
    else if (m.gp === 'cycle') cycle(m.dir);
  });
  addEventListener('resize', () => { try { frame.contentWindow.postMessage({ gp: 'embed', topRight: barWidth() }, '*'); } catch {} });
  addEventListener('keydown', ev => { if (ev.target === sel) return; if (ev.key === '[') cycle(-1); else if (ev.key === ']') cycle(1); });
  document.body.classList.toggle('single', SKINS.length < 2);
  for (const s of SKINS) { const o = document.createElement('option'); o.value = s.id; o.textContent = s.label; sel.appendChild(o); }
  sel.addEventListener('change', () => show(sel.value));
  document.getElementById('skin-prev').addEventListener('click', () => cycle(-1));
  document.getElementById('skin-next').addEventListener('click', () => cycle(1));
  const t = store.get('gp-theme'); if (t === 'dark' || t === 'light') document.documentElement.dataset.theme = t;
  const h = location.hash; state.node = nodeFromHash(h);
  const fromUrl = (/[#&]view=([^&]+)/.exec(h) || [])[1];
  show(fromUrl || store.get('gp-skin-v2') || SKINS[0].id, { silent: true });
})();
</script>
'''
page = SHELL.replace('__EMBEDDED__', '\n'.join(embedded)).replace('__DATA__', data_text).replace('__SKINS__', json.dumps(skins_js, ensure_ascii=False))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w', encoding='utf-8').write(page)
# wersja lokalna: pełny szkielet HTML z deklaracją kodowania (artefakt dostaje szkielet od publikatora)
local = out[:-5] + '.local.html'
open(local, 'w', encoding='utf-8').write('<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + page + '</body></html>')
print(f'{out}: {len(page)/1e6:.2f} MB; skórki: {[s["id"] for s in skins_js]}')
