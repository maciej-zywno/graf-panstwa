// Runda 4 (2026-09-17): cztery funkcje oryginału. B1 obrót na godz. 6, B2 wachlarz podjednostek, B3 legenda jako filtr, B4 wypełnienie łańcucha władzy.
const { test, expect } = require('@playwright/test');
const { openD, T, settleRot } = require('./helpers');
const MSWIA = 'pl-ministerstwo-spraw-wewnetrznych-i-administracji', KGP = 'pl-komenda-glowna-policji';
// kąt węzła względem środka grafu w stopniach, zgodnie z zegarem: 0 = godz. 12, 180 = godz. 6
const openLegend = async page => { if (!(await page.evaluate(() => window.__GP_TEST.state().legendOpen))) await page.click('#legend-toggle'); };
const clockAngle = (page, id) => page.evaluate(i => { const G = window.__GP_TEST, a = G.screenPos(i), c = G.screenPos('pl-narod'); return (Math.atan2(a.x - c.x, -(a.y - c.y)) * 180 / Math.PI + 360) % 360; }, id);

test.describe('B1: obrót do godziny szóstej', () => {
  for (const id of ['pl-nik', MSWIA, 'pl-sejm', 'pl-wojewoda-mazowiecki']) test(`${id} po wyborze staje na godz. 6, po odznaczeniu graf wraca`, async ({ page }) => {
    await openD(page); const t = T(page); const ref = await t.pos('pl-sad-najwyzszy'); const k0 = (await t.state()).k;
    await t.selectByHash(id); const ang = await clockAngle(page, id); expect(Math.abs(ang - 180), `kąt ${ang.toFixed(1)}°`).toBeLessThanOrEqual(4);
    expect((await t.state()).k, 'obrót nie zmienia skali').toBeCloseTo(k0, 5);
    await t.selectByHash(null); const s = await t.state(); expect(Math.abs(s.rot)).toBeLessThan(0.01); const back = await t.pos('pl-sad-najwyzszy');
    expect(Math.hypot(back.x - ref.x, back.y - ref.y), 'graf wraca do położenia wyjściowego').toBeLessThan(2);
  });

  test('klik obraca płynnie i kończy na godz. 6; wejście z linku jest od razu obrócone', async ({ page }) => {
    await openD(page); const t = T(page); const p = await t.pos('pl-nik'); await page.mouse.click(p.x, p.y); await page.waitForTimeout(120);
    const mid = await t.state(); expect(mid.selected).toBe('pl-nik'); expect(mid.rotating, 'obrót trwa (animacja)').toBe(true);
    await settleRot(page); expect(Math.abs(await clockAngle(page, 'pl-nik') - 180)).toBeLessThanOrEqual(4);
    const page2 = await page.context().newPage(); await openD(page2, '#node=pl-sejm'); const s = await T(page2).state(); expect(s.selected).toBe('pl-sejm'); expect(s.rotating, 'z linku bez animacji').toBe(false); expect(Math.abs(await clockAngle(page2, 'pl-sejm') - 180)).toBeLessThanOrEqual(4);
  });

  test('wybór podjednostki albo kółka szefa węzła stojącego na godz. 6 nie obraca ponownie', async ({ page }) => {
    await openD(page); const t = T(page); await t.selectByHash(MSWIA); const rot = (await t.state()).rot;
    let p = await t.pos(KGP); await page.mouse.click(p.x, p.y); await page.waitForTimeout(150); let s = await t.state();
    expect(s.selected).toBe(KGP); expect(s.rotating).toBe(false); expect(s.rot).toBeCloseTo(rot, 3);
    p = await t.pos('pl-minister-spraw-wewnetrznych-i-administracji'); await page.mouse.click(p.x, p.y); await page.waitForTimeout(150); s = await t.state();
    expect(s.selected).toBe('pl-minister-spraw-wewnetrznych-i-administracji'); expect(s.rotating).toBe(false); expect(s.rot).toBeCloseTo(rot, 3);
  });

  test('napisy po obrocie nie stoją do góry nogami (sektory, pierścienie, Parlament, pasma, pieczęć)', async ({ page }) => {
    await openD(page); const t = T(page);
    const tilt = () => page.evaluate(() => { const out = {}; const norm = d => ((d + 180) % 360 + 360) % 360 - 180;
      for (const el of document.querySelectorAll('.arc-labels text')) { const tp = el.querySelector('textPath'); const id = tp.getAttribute('href').slice(1); const n = el.getNumberOfChars(); if (!n) continue; const m = el.getScreenCTM(); const ctmRot = Math.atan2(m.b, m.a) * 180 / Math.PI; out[id] = Math.round(norm(el.getRotationOfChar(Math.floor(n / 2)) + ctmRot)); }
      const sm = document.querySelector('.seal-txt').getScreenCTM(); out.seal = Math.round(norm(Math.atan2(sm.b, sm.a) * 180 / Math.PI)); return out; });
    for (const id of ['pl-sejm', 'pl-nik', 'pl-wojewoda-mazowiecki', MSWIA]) { await t.selectByHash(id); const r = await tilt();
      expect(Object.keys(r).length).toBeGreaterThan(8);
      for (const [k, v] of Object.entries(r)) expect(Math.abs(v), `${id}: napis ${k} obrócony o ${v}°`).toBeLessThanOrEqual(96);
      expect(Math.abs(r.seal), 'tekst pieczęci poziomo').toBeLessThanOrEqual(1); }
  });

  test('klik w glif po obrocie nadal wybiera ten glif (20 losowych)', async ({ page }) => {
    await openD(page); const t = T(page); await t.selectByHash('pl-sejm'); const bad = [];
    const targets = await page.evaluate(() => { const g = window.__GP_TEST.glyphs().filter(x => !['root', 'parlring', 'parl'].includes(x.kind)); let seed = 23; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const pick = new Set(); while (pick.size < 20) pick.add(g[Math.floor(rnd() * g.length)].id); return [...pick]; });
    for (const id of targets) { await t.selectByHash('pl-sejm'); const p = await t.pos(id); await page.mouse.click(p.x, p.y); await page.waitForTimeout(60); const got = (await t.state()).selected; if (got !== id) bad.push(`${id}: ${got}`); }
    expect(bad, `nietrafione: ${bad.length} z 20`).toEqual([]);
  });

  test('zoom i przesuwanie działają na obróconym grafie, „Dopasuj” nie kasuje obrotu', async ({ page }) => {
    await openD(page); const t = T(page); await t.selectByHash('pl-nik'); const rot = (await t.state()).rot; const st = await page.evaluate(() => window.__GP_TEST.stageRect());
    await page.mouse.move(st.x + st.w / 2, st.y + st.h / 2); await page.mouse.wheel(0, -400); await page.waitForTimeout(300); expect((await t.state()).k).toBeGreaterThan(0.6);
    await page.click('#btn-fit'); await page.waitForTimeout(900); const s = await t.state(); expect(s.rot).toBeCloseTo(rot, 3); expect(s.selected).toBe('pl-nik'); expect(Math.abs(await clockAngle(page, 'pl-nik') - 180)).toBeLessThanOrEqual(4);
  });
});

test.describe('B2: wachlarz podjednostek', () => {
  test('po wyborze organu grono kropek rozwija się w mini-glify, które się nie nakładają i są klikalne', async ({ page }) => {
    await openD(page); const t = T(page); const s = await t.selectByHash(MSWIA); expect(s.fan).toBe(MSWIA); const kids = (await t.node(MSWIA)).children;
    const fan = await page.evaluate(() => { const g = window.__GP_TEST.glyphs(); const minis = g.filter(x => x.kind === 'mini'); const hits = [];
      for (let i = 0; i < minis.length; i++) for (let j = i + 1; j < minis.length; j++) { const a = minis[i], b = minis[j]; if (Math.hypot(a.x - b.x, a.y - b.y) < (a.r + b.r) * 0.95) hits.push(a.id + '×' + b.id); }
      const st = window.__GP_TEST.stageRect(); return { minis: minis.map(m => m.id), hits, heads: g.filter(x => x.kind === 'head' && minis.some(m => m.id === x.headOf)).length, inside: minis.every(m => m.x > st.x && m.x < st.x + st.w && m.y > st.y && m.y < st.y + st.h - 84) }; });
    expect(fan.minis.length).toBeGreaterThanOrEqual(8); expect(fan.minis.length).toBeLessThanOrEqual(kids + 4); expect(fan.hits, 'nakładające się mini-glify').toEqual([]); expect(fan.heads, 'kółka szefów przy mini-glifach').toBeGreaterThan(3); expect(fan.inside, 'wachlarz w scenie, nad pasem nakładek').toBe(true);
    expect(await page.locator('.fan-lines path').count(), 'przerywane łączniki do rodzica').toBe(fan.minis.length);
    const rot = (await t.state()).rot; const bad = [];
    for (const id of fan.minis) { await t.selectByHash(MSWIA); const p = await t.pos(id); expect(p.kind).toBe('mini'); await page.mouse.click(p.x, p.y); await page.waitForTimeout(80); const st = await t.state(); if (st.selected !== id || st.fan !== MSWIA || Math.abs(st.rot - rot) > 0.01) bad.push(`${id}: ${st.selected}, fan ${st.fan}, rot ${st.rot}`); }
    expect(bad, 'każdy mini-glif klikalny, bez ponownego obrotu, wachlarz zostaje').toEqual([]);
  });

  test('wybrana KGP to wypełniony mini-glif, rodzic jasny, linie celują w mini-glif; odznaczenie zwija wachlarz', async ({ page }) => {
    await openD(page); const t = T(page); await t.selectByHash(MSWIA); const rest = await page.evaluate(i => getComputedStyle(document.querySelector(`g.node[data-id="${i}"] .glyph`)).fill, KGP);
    let p = await t.pos(KGP); await page.mouse.move(p.x, p.y); await page.waitForTimeout(150); expect((await t.state()).hoverPill, 'pigułka przy najechaniu na mini-glif').toBe('Komenda Główna Policji');
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(200); await page.mouse.move(5, 5); await page.waitForTimeout(150); const s = await t.state(); expect(s.selected).toBe(KGP); expect(s.fan).toBe(MSWIA);
    const r = await page.evaluate(([kgp, par]) => { const G = window.__GP_TEST; const f = id => getComputedStyle(document.querySelector(`g.node[data-id="${id}"] .glyph`)).fill; const c = G.screenPos(kgp); const k = G.state().k;
      const ends = G.edges().filter(e => !e.chain).map(e => { const pts = G.edgePoints(e.id, 30); const a = pts[0], b = pts[pts.length - 1]; return Math.min(Math.hypot(a.x - c.x, a.y - c.y), Math.hypot(b.x - c.x, b.y - c.y)) / k; });
      return { mini: f(kgp), parent: f(par), parentNb: document.querySelector(`g.node[data-id="${par}"]`).classList.contains('nb'), ends, kind: c.kind }; }, [KGP, MSWIA]);
    expect(r.kind).toBe('mini'); expect(r.mini, 'wybrany mini-glif wypełniony').not.toBe(rest); expect(r.parentNb, 'rodzic z jasnym wypełnieniem').toBe(true); expect(r.ends.length).toBeGreaterThan(0);
    for (const d of r.ends) expect(d, 'koniec linii przy mini-glifie (jednostki sceny)').toBeLessThan(16);
    await t.selectByHash(null); const s2 = await t.state(); expect(s2.fan).toBeNull(); expect((await t.pos(KGP)).kind).toBe('sat'); expect(await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => g.kind === 'mini').length)).toBe(0);
    await t.selectByHash('pl-nik'); await t.selectByHash('pl-minister-spraw-wewnetrznych-i-administracji'); expect((await t.state()).fan, 'kółko szefa też rozwija wachlarz organu').toBe(MSWIA);
    await t.selectByHash('pl-ministerstwo-zdrowia'); expect((await t.state()).fan, 'inny organ: nowy wachlarz').toBe('pl-ministerstwo-zdrowia'); expect((await t.pos(KGP)).kind).toBe('sat');
  });
});

test('B2: wachlarz izby udźwignie kilkadziesiąt podjednostek (Sejm, Senat): kilka łuków bez nakładania, komisja klikalna, klub inny niż komisja', async ({ page }) => {
  await openD(page); const t = T(page);
  for (const id of ['pl-sejm', 'pl-senat']) {
    const s = await t.selectByHash(id); expect(s.fan, `wybór izby rozwija jej wachlarz (${id})`).toBe(id); const kids = (await t.node(id)).children;
    const fan = await page.evaluate(() => { const g = window.__GP_TEST.glyphs(); const minis = g.filter(x => x.kind === 'mini'); const hits = []; const c = window.__GP_TEST.screenPos('pl-narod'), k = window.__GP_TEST.state().k;
      for (let i = 0; i < minis.length; i++) for (let j = i + 1; j < minis.length; j++) { const a = minis[i], b = minis[j]; if (Math.hypot(a.x - b.x, a.y - b.y) < (a.r + b.r) * 0.95) hits.push(a.id + '×' + b.id); }
      const others = g.filter(x => ['primary', 'blob', 'head'].includes(x.kind) && !minis.some(m => m.id === x.headOf)); const onGlyph = minis.filter(m => others.some(o => Math.hypot(m.x - o.x, m.y - o.y) < (m.r + o.r) * 0.9)).map(m => m.id);
      return { n: minis.length, heads: g.filter(x => x.kind === 'head' && minis.some(m => m.id === x.headOf)).length, hits, onGlyph, arcs: new Set(minis.map(m => Math.round(Math.hypot(m.x - c.x, m.y - c.y) / k / 6))).size, lines: document.querySelectorAll('.fan-lines path').length }; });
    expect(fan.n + fan.heads, 'mini-glifów (z kółkami szefów) tyle, ile jednostek podległych w danych').toBe(kids); expect(fan.n).toBeGreaterThan(20); expect(fan.hits, 'nakładające się mini-glify').toEqual([]); expect(fan.onGlyph, 'mini-glify na cudzych glifach').toEqual([]);
    expect(fan.arcs, 'duże grono układa się w kilku łukach').toBeGreaterThanOrEqual(2); expect(fan.arcs).toBeLessThanOrEqual(6); expect(fan.lines).toBe(fan.n);
  }
  await t.selectByHash('pl-sejm'); const rot = (await t.state()).rot; const p = await t.pos('pl-sejm-komisja-fpb'); expect(p.kind).toBe('mini');
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(150); expect((await t.state()).hoverPill).toBe('Komisja Finansów Publicznych (Sejm)');
  await page.mouse.click(p.x, p.y); await page.waitForTimeout(150); const s = await t.state(); expect(s.selected).toBe('pl-sejm-komisja-fpb'); expect(s.fan).toBe('pl-sejm'); expect(s.rot).toBeCloseTo(rot, 3);
  const shapes = await page.evaluate(() => { const G = window.__GP_TEST; const ids = G.glyphs().filter(g => g.kind === 'mini').map(g => g.id); const club = ids.find(i => G.node(i).type === 'political_group'), com = ids.find(i => G.node(i).type === 'commission');
    const d = i => { const el = document.querySelector(`g.node[data-id="${i}"] .glyph`); return { d: el.getAttribute('d'), dash: getComputedStyle(el).strokeDasharray }; }; return { club: d(club), com: d(com) }; });
  expect(shapes.club.d, 'glif klubu ma inny kształt niż glif komisji').not.toBe(shapes.com.d); expect(shapes.club.dash, 'obrys klubu przerywany').not.toBe('none'); expect(shapes.com.dash).toBe('none');
});

test.describe('B3: legenda jako filtr', () => {
  test('ukrycie typu encji i relacji, licznik, trwałość przy zmianie wyboru, „Pokaż wszystko”', async ({ page }) => {
    await openD(page); const t = T(page); const before = await page.evaluate(() => window.__GP_TEST.glyphs().length);
    await page.click('#legend-toggle'); await page.click('[data-lkey="entity:court"]'); await page.waitForTimeout(150);
    let r = await page.evaluate(() => { const G = window.__GP_TEST; const ids = new Set(G.glyphs().map(g => g.id)); return { hidden: G.state().hidden, sn: ids.has('pl-sad-najwyzszy'), tk: ids.has('pl-trybunal-konstytucyjny'), snDisplay: getComputedStyle(document.querySelector('g.node[data-id="pl-sad-najwyzszy"]')).display, n: ids.size,
      pressed: document.querySelector('[data-lkey="entity:court"]').getAttribute('aria-pressed'), count: document.querySelector('#legend-toggle').textContent.replace(/\s+/g, ' ').trim(), showAll: !document.querySelector('#legend-show').hidden, open: G.state().legendOpen }; });
    expect(r.hidden).toEqual(['entity:court']); expect(r.sn).toBe(false); expect(r.tk).toBe(false); expect(r.snDisplay).toBe('none'); expect(r.n).toBeLessThan(before); expect(r.pressed).toBe('false'); expect(r.count).toContain('1 ukryte'); expect(r.showAll).toBe(true); expect(r.open, 'klik w pozycję nie zamyka legendy').toBe(true);
    await t.selectByHash('pl-prezydent-rp'); const withAppoints = await page.evaluate(() => window.__GP_TEST.edges().filter(e => e.types.includes('appoints')).length); expect(withAppoints).toBeGreaterThan(10);
    await openLegend(page); await page.click('[data-lkey="rel:appoints"]'); await page.waitForTimeout(150);
    expect(await page.evaluate(() => window.__GP_TEST.edges().filter(e => e.types.includes('appoints')).length), 'linie „powołuje” znikają').toBe(0);
    expect((await t.state()).hidden.sort()).toEqual(['entity:court', 'rel:appoints']); expect(await page.evaluate(() => document.querySelector('#legend-toggle').textContent)).toContain('2 ukryte');
    await page.keyboard.press('Escape'); await t.selectByHash('pl-nik'); await page.waitForTimeout(100);
    r = await page.evaluate(() => { const G = window.__GP_TEST; return { hidden: G.state().hidden.length, appoints: G.edges().filter(e => e.types.includes('appoints')).length, drawn: G.state().edgesDrawn, sn: G.glyphs().some(g => g.id === 'pl-sad-najwyzszy') }; });
    expect(r.hidden, 'filtr przeżywa zmianę wyboru i zamknięcie legendy').toBe(2); expect(r.appoints).toBe(0); expect(r.sn).toBe(false);
    await page.reload(); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden); expect((await t.state()).hidden.length, 'filtr przeżywa odświeżenie (sessionStorage)').toBe(2);
    await openLegend(page); await page.click('#legend-show'); await page.waitForTimeout(150);
    r = await page.evaluate(() => { const G = window.__GP_TEST; return { hidden: G.state().hidden, n: G.glyphs().length, sn: G.glyphs().some(g => g.id === 'pl-sad-najwyzszy'), count: document.querySelector('#legend-toggle').textContent, showAll: !document.querySelector('#legend-show').hidden, appoints: G.edges().filter(e => e.types.includes('appoints')).length }; });
    expect(r.hidden).toEqual([]); expect(r.sn).toBe(true); expect(r.count).not.toContain('ukryte'); expect(r.showAll).toBe(false); expect(r.appoints).toBeGreaterThan(0);
  });

  test('„Stanowisko szefa organu” ukrywa same kółka; w liniach scalonych odpada ukryty typ', async ({ page }) => {
    await openD(page); const t = T(page); const c0 = await page.evaluate(() => { const g = window.__GP_TEST.glyphs(); return { heads: g.filter(x => x.kind === 'head').length, prim: g.filter(x => x.kind === 'primary' && !x.headOf).length }; });
    await page.click('#legend-toggle'); await page.click('[data-lkey="entity:head"]'); await page.waitForTimeout(150);
    const c1 = await page.evaluate(() => { const g = window.__GP_TEST.glyphs(); const G = window.__GP_TEST; return { heads: g.filter(x => x.kind === 'head').length, orgs: g.filter(x => x.kind === 'primary' && G.node(x.id).type !== 'dept_head').length }; });
    expect(c0.heads).toBeGreaterThan(50); expect(c1.heads).toBe(0); expect(c1.orgs).toBeGreaterThan(80);
    await page.click('#legend-show'); await page.keyboard.press('Escape'); await t.selectByHash('pl-prezes-rady-ministrow'); await page.click('#view-node [data-relkey="*"], .fchips [data-relkey="*"]'); await page.waitForTimeout(300);
    const merged = await page.evaluate(() => window.__GP_TEST.edges().filter(e => !e.chain && e.merged > 1 && e.types.includes('oversees')).length); expect(merged).toBeGreaterThan(0);
    await openLegend(page); await page.click('[data-lkey="rel:oversees"]'); await page.waitForTimeout(200);
    const after = await page.evaluate(() => { const e = window.__GP_TEST.edges().filter(x => !x.chain); return { oversees: e.filter(x => x.types.includes('oversees')).length, lines: e.length }; });
    expect(after.oversees, 'z linii scalonych odpada ukryty typ').toBe(0); expect(after.lines).toBeGreaterThan(0);
  });

  test('węzeł ukrytego typu da się znaleźć wyszukiwarką: komunikat i tymczasowe pokazanie', async ({ page }) => {
    await openD(page); const t = T(page); await page.click('#legend-toggle'); await page.click('[data-lkey="entity:court"]'); await page.keyboard.press('Escape');
    await page.fill('#q', 'Trybunał Konstytucyjny'); await page.waitForTimeout(400); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
    const r = await page.evaluate(() => { const G = window.__GP_TEST; return { sel: G.state().selected, msg: G.state().bottomPill, shown: G.glyphs().some(g => g.id === 'pl-trybunal-konstytucyjny'), otherCourt: G.glyphs().some(g => g.id === 'pl-sad-najwyzszy') }; });
    expect(r.sel).toBe('pl-trybunal-konstytucyjny'); expect(r.msg).toContain('jest ukryty w legendzie'); expect(r.msg).toContain('Sądy i trybunały'); expect(r.shown, 'wybrany węzeł pokazany tymczasowo').toBe(true); expect(r.otherCourt, 'pozostałe sądy dalej ukryte').toBe(false);
    await t.selectByHash(null); expect(await page.evaluate(() => window.__GP_TEST.glyphs().some(g => g.id === 'pl-trybunal-konstytucyjny')), 'po odznaczeniu znów ukryty').toBe(false);
  });
});

test('B4: węzły łańcucha władzy i pieczęć suwerena dostają jasne wypełnienie (oba motywy)', async ({ page }) => {
  await openD(page); const t = T(page);
  const fills = () => page.evaluate(() => ({ seal: getComputedStyle(document.querySelector('g.node.k-root .seal')).fill, prez: getComputedStyle(document.querySelector('g.node[data-id="pl-prezydent-rp"] .glyph')).fill, chain: window.__GP_TEST.edges().filter(e => e.chain).map(e => e.from + '>' + e.to), all: window.__GP_TEST.edges().map(e => e.from + '>' + e.to) }));
  for (const theme of ['light', 'dark']) {
    if (theme === 'dark') { await t.selectByHash(null); await page.click('#btn-theme'); await page.waitForTimeout(200); }
    await t.selectByHash(null); const rest = await fills(); await t.selectByHash('pl-minister-zdrowia'); await page.waitForTimeout(250); const sel = await fills();
    expect(sel.chain, `${theme}: łańcuch umocowania sięga suwerena`).toContain('pl-narod>pl-prezydent-rp'); expect(sel.all, `${theme}: Prezydent → minister`).toContain('pl-prezydent-rp>pl-minister-zdrowia');
    expect(sel.seal, `${theme}: pieczęć`).not.toBe(rest.seal); expect(sel.prez, `${theme}: Prezydent`).not.toBe(rest.prez);
  }
});
