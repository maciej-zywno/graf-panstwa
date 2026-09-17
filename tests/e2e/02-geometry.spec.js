const { test, expect } = require('@playwright/test');
const { openD, T } = require('./helpers');

test('geometria: w spoczynku żadne dwa glify organów się nie nakładają', async ({ page }) => {
  await openD(page);
  const hits = await page.evaluate(() => {
    const g = window.__GP_TEST.glyphs().filter(x => ['primary', 'blob', 'head'].includes(x.kind)); const out = [];
    for (let i = 0; i < g.length; i++) for (let j = i + 1; j < g.length; j++) { const a = g[i], b = g[j];
      if (a.headOf === b.id || b.headOf === a.id) continue;                     // kółko szefa jest doklejone celowo
      if (a.headOf && a.headOf === b.headOf) continue;                           // dwa kółka przy tym samym organie
      const d = Math.hypot(a.x - b.x, a.y - b.y); if (d < (a.r + b.r) * 0.80) out.push({ a: a.id, b: b.id, d: +d.toFixed(1), need: +((a.r + b.r) * 0.80).toFixed(1) }); }
    return out;
  });
  expect(hits.slice(0, 15), `nakładające się pary: ${hits.length}`).toEqual([]);
});

test('geometria: wszystkie glify mieszczą się w scenie po dopasowaniu', async ({ page }) => {
  await openD(page);
  const out = await page.evaluate(() => { const r = window.__GP_TEST.stageRect(); return window.__GP_TEST.glyphs().filter(g => g.x - g.r < r.x - 1 || g.x + g.r > r.x + r.w + 1 || g.y - g.r < r.y - 1 || g.y + g.r > r.y + r.h + 1).map(g => g.id); });
  expect(out.slice(0, 15), `glify poza sceną: ${out.length}`).toEqual([]);
});

const NODES = ['pl-prezydent-rp', 'pl-sejm', 'pl-senat', 'pl-nik', 'pl-ministerstwo-spraw-wewnetrznych-i-administracji', 'pl-wojewoda-mazowiecki', 'pl-krrit', 'pl-sad-najwyzszy', 'pl-rada-ministrow', 'pl-minister-finansow-i-gospodarki', 'pl-prezes-rady-ministrow', 'pl-minister-spraw-wewnetrznych-i-administracji'];
for (const id of NODES) test(`linie: relacje węzła ${id} nie wyglądają, jakby wychodziły z cudzego glifu`, async ({ page }) => {
  await openD(page); await T(page).selectByHash(id);
  if (await page.evaluate(() => window.__GP_TEST.state().hub)) { await page.click('#view-node [data-relkey="*"], .fchips [data-relkey="*"]'); await page.waitForTimeout(300); }
  const res = await page.evaluate(sel => {
    const G = window.__GP_TEST, st = G.state(), glyphs = G.glyphs(), byId = Object.fromEntries(glyphs.map(g => [g.id, g])), edges = G.edges().filter(e => !e.chain);
    const lit = new Set([sel]); edges.forEach(e => { lit.add(e.from); lit.add(e.to); });
    let obstacles = [...lit].map(i => byId[i]).filter(g => g && ['primary', 'blob'].includes(g.kind)); const src = G.screenPos(sel);
    // hub rysuje proste promienie pod glifami (jak oryginał); pilnujemy tylko glifów stojących tuż przy źródle, bo tam linia myli
    if (st.hub) obstacles = obstacles.filter(o => Math.hypot(o.x - src.x, o.y - src.y) < 90 * st.k);
    const bad = [];
    for (const e of edges) { const pts = G.edgePoints(e.id, 40); if (!pts) continue;
      for (const o of obstacles) { if (o.id === e.from || o.id === e.to) continue; const fa = byId[e.from], ta = byId[e.to];
        if ((fa && (fa.headOf === o.id || o.headOf === fa.id)) || (ta && (ta.headOf === o.id || o.headOf === ta.id))) continue;
        if (pts.some(p => Math.hypot(p.x - o.x, p.y - o.y) < o.r * 0.85)) { bad.push({ edge: e.id, through: o.id }); break; } } }
    return { hub: st.hub, drawn: edges.length, bad, blocked: st.blockedEdges };
  }, id);
  test.info().annotations.push({ type: 'linie', description: `${res.hub ? 'hub, ' : ''}${res.drawn} narysowanych, ${res.bad.length} mylących, blockedEdges=${res.blocked}` });
  expect(res.bad.slice(0, 10), `linie mylące: ${res.bad.length} z ${res.drawn}`).toEqual([]);
});

const HUBS = ['pl-prezes-rady-ministrow', 'pl-prezydent-rp', 'pl-minister-spraw-wewnetrznych-i-administracji'];
for (const id of HUBS) test(`hub ${id}: domyślnie jeden typ, proste promienie, jedna linia na organ`, async ({ page }) => {
  await openD(page); const t = T(page); const s0 = await t.selectByHash(id); await page.waitForTimeout(200); const nd = await t.node(id); const rels = nd.inCount + nd.outCount;
  expect(s0.hub, 'tryb huba').toBe(true); expect(s0.relFilter, 'domyślnie dominujący typ').toBeTruthy();
  const def = await page.evaluate(() => { const e = window.__GP_TEST.edges().filter(x => !x.chain); return { lines: e.length, types: [...new Set(e.flatMap(x => x.types))], straight: e.filter(x => x.straight).length }; });
  expect(def.types.length, 'jeden typ relacji na scenie').toBe(1); expect(def.lines).toBeLessThanOrEqual(110); expect(def.straight / def.lines).toBeGreaterThan(0.7);
  expect(await page.locator('#rel-bar .fchip').count(), 'pasek żetonów na scenie mieści się w jednym rzędzie').toBeLessThanOrEqual(6);
  await page.click('#view-node [data-relkey="*"], .fchips [data-relkey="*"]'); await page.waitForTimeout(300);
  const all = await page.evaluate(() => { const e = window.__GP_TEST.edges().filter(x => !x.chain); return { lines: e.length, merged: e.filter(x => x.merged > 1).length, relFilter: window.__GP_TEST.state().relFilter, covered: e.reduce((a, x) => a + x.merged, 0) }; });
  expect(all.relFilter).toBeNull(); expect(all.covered, 'scalone linie pokrywają wszystkie relacje').toBeGreaterThanOrEqual(rels - 3); expect(all.lines, 'mniej linii niż relacji').toBeLessThan(all.covered);
  test.info().annotations.push({ type: 'hub', description: `domyślnie ${def.lines} linii (${def.types[0]}), wszystkie: ${all.lines} linii na ${all.covered} relacji, scalonych ${all.merged}` });
});
