// Animacja rzędu podjednostek jak w oryginale (zmierzona klatka po klatce na graph.civlab.org/us, 17.09.2026):
// mini-glify startują z kątów własnych kropek (ciasno), rozsuwają się po łuku ok. 0,72 s (easeInOutCubic), wybrany jest 1,6× większy,
// odstęp między krawędziami sąsiadów jest stały, linie relacji wracają po zakończeniu ruchu, a zamknięcie jest natychmiastowe.
const { test, expect } = require('@playwright/test');
const { openD, T, settleRot } = require('./helpers');
const MSWIA = 'pl-ministerstwo-spraw-wewnetrznych-i-administracji';
const minis = page => page.evaluate(() => [...document.querySelectorAll('g.node.k-mini')].map(el => { const r = el.querySelector('.glyph').getBoundingClientRect(); return { id: el.getAttribute('data-id'), x: r.left + r.width / 2, y: r.top + r.height / 2, w: Math.max(r.width, r.height), big: el.classList.contains('big') }; }));
const spanOf = a => Math.hypot(Math.max(...a.map(m => m.x)) - Math.min(...a.map(m => m.x)), Math.max(...a.map(m => m.y)) - Math.min(...a.map(m => m.y)));

test('klik w kropkę: rząd startuje ciasno przy gronie, rozsuwa się płynnie, a linie relacji wracają po ruchu', async ({ page }) => {
  await openD(page); const dot = await page.evaluate(pid => { const a = window.__GP_TEST.glyphs().filter(g => g.kind === 'sat' && g.parent === pid); return a[Math.floor(a.length / 2)]; }, MSWIA);
  await page.mouse.click(dot.x, dot.y); await page.mouse.move(5, 5); const frames = [];
  for (let i = 0; i < 14; i++) { const m = await minis(page); const st = await T(page).state(); frames.push({ span: spanOf(m), moving: st.fanMoving, eop: await page.evaluate(() => +getComputedStyle(document.querySelector('g.edges')).opacity) }); await page.waitForTimeout(45); }
  await settleRot(page); await page.waitForTimeout(350); const end = await minis(page); const last = spanOf(end);
  expect(frames[0].moving, 'ruch trwa zaraz po kliknięciu').toBe(true); expect(frames[0].span, 'start: rząd ciasny (kąty kropek)').toBeLessThan(last * 0.55); expect(frames[0].eop, 'linie schowane na czas ruchu').toBeLessThan(0.05);
  const spans = frames.filter(f => f.moving).map(f => f.span); for (let i = 1; i < spans.length; i++) expect(spans[i], `rozpiętość rośnie monotonnie (klatka ${i})`).toBeGreaterThanOrEqual(spans[i - 1] - 8); // w trakcie obrotu ramka ekranowa lekko pływa
  const st = await T(page).state(); expect(st.fanMoving).toBe(false); expect(st.selected).toBe(dot.id); expect(st.edgesDrawn).toBeGreaterThan(0); expect(await page.evaluate(() => +getComputedStyle(document.querySelector('g.edges')).opacity)).toBeGreaterThan(0.95);
});

test('wybrany mini-glif jest ok. 1,6× większy, sąsiedzi robią mu miejsce (stały odstęp krawędzi), nic się nie nakłada', async ({ page }) => {
  await openD(page); const t = T(page); const kid = await page.evaluate(pid => window.__GP_TEST.glyphs().filter(g => g.kind === 'sat' && g.parent === pid)[3].id, MSWIA); await t.selectByHash(kid); await page.waitForTimeout(200);
  const m = await minis(page); const big = m.filter(x => x.big); expect(big.length).toBe(1); expect(big[0].id).toBe(kid); const norm = m.filter(x => !x.big); const med = norm.map(x => x.w).sort((a, b) => a - b)[Math.floor(norm.length / 2)];
  expect(big[0].w / med).toBeGreaterThan(1.4); expect(big[0].w / med).toBeLessThan(1.8); expect((await t.state()).fanFocus).toBe(kid);
  const near = norm.map(x => Math.hypot(x.x - big[0].x, x.y - big[0].y)).sort((a, b) => a - b); const pitch = norm.length > 2 ? Math.min(...norm.flatMap((a, i) => norm.slice(i + 1).map(b => Math.hypot(a.x - b.x, a.y - b.y)))) : 0;
  expect(near[0], 'odstęp środka wybranego od sąsiada większy niż zwykły skok').toBeGreaterThan(pitch * 1.12);
  const hits = []; for (let i = 0; i < m.length; i++) for (let j = i + 1; j < m.length; j++) if (Math.hypot(m[i].x - m[j].x, m[i].y - m[j].y) < (m[i].w + m[j].w) / 2 * 0.86) hits.push([m[i].id, m[j].id]); expect(hits, 'nakładające się mini-glify').toEqual([]);
});

test('zmiana wyboru w otwartym rzędzie: nowy rośnie, stary maleje, graf się nie obraca ponownie, a rząd zostaje ten sam', async ({ page }) => {
  await openD(page); const t = T(page); const kids = await page.evaluate(pid => window.__GP_TEST.glyphs().filter(g => g.kind === 'sat' && g.parent === pid).map(g => g.id), MSWIA); await t.selectByHash(kids[2]); await page.waitForTimeout(200); const rot = (await t.state()).rot;
  const p = await t.pos(kids[6]); await page.mouse.click(p.x, p.y); await page.mouse.move(5, 5); await page.waitForTimeout(60); expect((await t.state()).fanMoving).toBe(true); await settleRot(page); await page.waitForTimeout(250);
  const m = await minis(page); expect(m.filter(x => x.big).map(x => x.id)).toEqual([kids[6]]); const s = await t.state(); expect(s.fan).toBe(MSWIA); expect(s.fanFocus).toBe(kids[6]); expect(s.rot).toBeCloseTo(rot, 3); expect(m.length).toBe(kids.length);
  const q = await t.pos(kids[6]); const hit = await page.evaluate(({ x, y }) => { const el = document.elementFromPoint(x, y); const g = el && el.closest && el.closest('g.node'); return g && g.getAttribute('data-id'); }, q); expect(hit, 'powiększony mini-glif jest tam, gdzie wskazuje uchwyt').toBe(kids[6]);
});

test('wybór rodzica nie powiększa żadnego mini-glifu, a odznaczenie zamyka rząd od razu i przywraca kropki', async ({ page }) => {
  await openD(page); const t = T(page); const before = await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => g.kind === 'sat').length); await t.selectByHash(MSWIA); await page.waitForTimeout(200);
  expect((await minis(page)).filter(x => x.big)).toEqual([]); expect((await t.state()).fanFocus).toBe(null);
  await t.selectByHash(null); await page.waitForTimeout(450); const s = await t.state(); expect(s.fan).toBe(null); expect(s.fanMoving).toBe(false); expect((await minis(page)).length).toBe(0); expect(await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => g.kind === 'sat').length)).toBe(before);
});

test('ograniczony ruch (prefers-reduced-motion): rząd od razu w układzie końcowym, linie widoczne', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } }); const page = await ctx.newPage(); await openD(page);
  const dot = await page.evaluate(pid => { const a = window.__GP_TEST.glyphs().filter(g => g.kind === 'sat' && g.parent === pid); return a[1]; }, MSWIA); await page.mouse.click(dot.x, dot.y); await page.waitForTimeout(80);
  const s = await T(page).state(); expect(s.fanMoving).toBe(false); expect(s.selected).toBe(dot.id); const a = spanOf(await minis(page)); await page.waitForTimeout(500); expect(Math.abs(spanOf(await minis(page)) - a)).toBeLessThan(2); await ctx.close();
});

test('wybrany glif organu rośnie płynnie o ok. 30% (oryginał: 14 → 18,2 j.), po odznaczeniu wraca', async ({ page }) => {
  await openD(page); const t = T(page); const w = () => page.evaluate(() => { const m = getComputedStyle(document.querySelector('g.node[data-id="pl-nik"] .glyph')).transform; if (!m || m === 'none') return 1; const v = m.match(/matrix\(([^)]+)\)/)[1].split(',').map(Number); return Math.hypot(v[0], v[1]); }); // skala z macierzy: ramka ekranowa zmienia się przy obrocie grafu
  const w0 = await w(); const p = await t.pos('pl-nik'); await page.mouse.click(p.x, p.y); await page.mouse.move(5, 5); await page.waitForTimeout(120); const wMid = await w(); await settleRot(page); await page.waitForTimeout(900); const w1 = await w();
  expect(wMid, 'wzrost jest animowany, nie skokowy').toBeLessThan(w0 * 1.2); expect(w1 / w0).toBeGreaterThan(1.2); expect(w1 / w0).toBeLessThan(1.45);
  await t.selectByHash(null); await page.waitForTimeout(1000); expect(Math.abs((await w()) / w0 - 1)).toBeLessThan(0.06);
});

// Zgłoszenie właściciela 17.09.2026 (#node=pl-rady-konsultacyjno-doradcze-przy-prezydencie-rp): klik w kwadracik klasy zbiorczej nie rozwijał jej,
// bo rząd podjednostek brał tylko kropki. W oryginale kwadraciki wchodzą do rzędu razem z kropkami.
test('klasa zbiorcza (rząd kwadracików) po kliknięciu wchodzi do rzędu jako powiększony mini-glif z podwójnym obrysem', async ({ page }) => {
  await openD(page); const t = T(page); const ID = 'pl-rady-konsultacyjno-doradcze-przy-prezydencie-rp';
  const p = await t.pos(ID); expect(p.kind).toBe('row'); await page.mouse.click(p.x, p.y); await page.mouse.move(5, 5); await settleRot(page); await page.waitForTimeout(300);
  const s = await t.state(); expect(s.selected).toBe(ID); expect(s.fan).toBe('pl-prezydent-rp'); expect(s.fanFocus).toBe(ID);
  const el = await page.evaluate(id => { const g = document.querySelector(`g.node[data-id="${id}"]`); return { mini: g.classList.contains('k-mini'), big: g.classList.contains('big'), multi: g.classList.contains('k-multi'), back: !!g.querySelector('.glyph.back'), n: document.querySelectorAll('g.node.k-mini').length }; }, ID);
  expect(el).toEqual({ mini: true, big: true, multi: true, back: true, n: 6 });
});

test('każda klasa zbiorcza w grafie daje się wybrać kliknięciem i rozwija się; po odznaczeniu wszystkie rzędy kwadracików wracają', async ({ page }) => {
  await openD(page); const t = T(page); const rows = await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => g.kind === 'row').map(g => g.id)); expect(rows.length).toBeGreaterThan(10);
  const bad = await page.evaluate(ids => { const G = window.__GP_TEST, out = []; for (const id of ids) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate')); const s = G.state(); const g = document.querySelector(`g.node[data-id="${id}"]`);
      if (s.selected !== id) out.push({ id, why: 'nie wybrany' }); else if (!s.fan) out.push({ id, why: 'rząd się nie otworzył' }); else if (s.fanFocus !== id) out.push({ id, why: 'nie jest powiększony', focus: s.fanFocus }); else if (!g || !g.classList.contains('k-mini') || !g.classList.contains('big')) out.push({ id, why: 'brak mini-glifu' }); } return out; }, rows);
  expect(bad.slice(0, 6), `klasy zbiorcze z usterką: ${bad.length} z ${rows.length}`).toEqual([]);
  await t.selectByHash(null); await page.waitForTimeout(500); const after = await page.evaluate(() => ({ rows: window.__GP_TEST.glyphs().filter(g => g.kind === 'row').length, drawn: document.querySelectorAll('g.node.k-row').length, minis: document.querySelectorAll('g.node.k-mini').length }));
  expect(after.rows).toBe(rows.length); expect(after.drawn).toBe(rows.length); expect(after.minis).toBe(0);
});
