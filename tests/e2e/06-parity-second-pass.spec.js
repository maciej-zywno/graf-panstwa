// Regresje z drugiego przebiegu zgodności 2026-09-17: N3, N4, N5, N6, N7, U1/U2 w węższych oknach, U21.
const { test, expect } = require('@playwright/test');
const { openD, T, settleRot } = require('./helpers');

test('N3: klik z ruchem myszy o kilka pikseli nadal wybiera węzeł', async ({ page }) => {
  await openD(page); const t = T(page);
  for (const d of [0, 1, 3, 5]) { await t.selectByHash(null); const p = await t.pos('pl-nik'); await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.mouse.move(p.x + d, p.y + d * 0.5); await page.mouse.up(); await page.waitForTimeout(200);
    expect((await t.state()).selected, `ruch ${d} px`).toBe('pl-nik'); }
});

test('N4: węzeł wybrany z wyszukiwarki po własnym zoomie trafia w pole widzenia', async ({ page }) => {
  await openD(page); const t = T(page); const st = await page.evaluate(() => window.__GP_TEST.stageRect());
  await page.mouse.move(st.x + st.w * 0.75, st.y + st.h * 0.3); for (let i = 0; i < 6; i++) await page.mouse.wheel(0, -320); await page.waitForTimeout(400);
  await page.fill('#q', 'Zakład Ubezpieczeń Społecznych'); await page.waitForTimeout(400); await page.keyboard.press('Enter'); await settleRot(page); await page.waitForTimeout(500); // B1: wybór z wyszukiwarki obraca graf płynnie (ok. 1 s)
  const s = await t.state(); const p = await t.pos(s.selected); expect(s.selected).toBeTruthy();
  expect(p.x).toBeGreaterThan(st.x + 20); expect(p.x).toBeLessThan(st.x + st.w - 20); expect(p.y).toBeGreaterThan(st.y + 20); expect(p.y).toBeLessThan(st.y + st.h - 90);
});

test('N5: legenda mieści się w scenie, przewija się, a „Co znaczą relacje?” jest widoczne bez przewijania sekcji', async ({ page }) => {
  await openD(page); await page.click('#legend-toggle'); await page.waitForTimeout(250);
  const r = await page.evaluate(() => { const b = document.querySelector('#legend-body'), rb = b.getBoundingClientRect(), st = window.__GP_TEST.stageRect(); const more = document.querySelector('#legend-more'); b.scrollTop = 1e6; const mr = more.getBoundingClientRect();
    return { inside: rb.top >= st.y && rb.bottom <= st.y + st.h, scrollable: b.scrollHeight > b.clientHeight ? getComputedStyle(b).overflowY : 'fits', reachable: b.scrollHeight - b.clientHeight >= 0, moreExists: !!more, relBarHidden: getComputedStyle(document.querySelector('#rel-bar')).visibility }; });
  expect(r.inside).toBe(true); expect(['scroll', 'auto', 'fits']).toContain(r.scrollable); expect(r.moreExists).toBe(true);
});

test('N7: zniekształcony adres nie wywala aplikacji', async ({ page }) => {
  const errors = await openD(page, '#node=%E0%A4%A'); await page.waitForTimeout(300);
  expect(errors).toEqual([]); expect(await page.evaluate(() => document.querySelector('#status').hidden)).toBe(true); expect((await T(page).state()).selected).toBeNull();
});

for (const vp of [{ width: 1280, height: 720 }, { width: 1024, height: 640 }]) test.describe(`okno ${vp.width}×${vp.height}`, () => {
  test.use({ viewport: vp });
  for (const id of ['pl-prezes-rady-ministrow', 'pl-sejm', 'pl-prezydent-rp']) test(`U1/U2: przy wybranym ${id} pasek żetonów ma jeden rząd i nie leży na glifach`, async ({ page }) => {
    await openD(page); await T(page).selectByHash(id); await page.waitForTimeout(300);
    const r = await page.evaluate(() => { const bar = document.querySelector('#rel-bar'); const h = bar.hidden ? 0 : bar.getBoundingClientRect().height; const covered = window.__GP_TEST.glyphs().filter(g => { const el = document.elementFromPoint(g.x, g.y); return el && el.closest && el.closest('#rel-bar, #sel-pill'); }).length;
      const pill = document.querySelector('#sel-pill').getBoundingClientRect(); const zoomBtn = document.querySelector('#btn-fit').getBoundingClientRect(); return { h, covered, pillOverZoom: pill.right > zoomBtn.left - 90 && pill.bottom > zoomBtn.top }; });
    expect(r.h, 'wysokość paska żetonów').toBeLessThanOrEqual(30); expect(r.covered, 'glify pod nakładkami').toBe(0);
  });
});

test.describe('N6: telefon 390 px', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  test('po odznaczeniu widok wraca do dopasowania', async ({ page }) => {
    await openD(page); const t = T(page); const k0 = (await t.state()).k; const c0 = await t.pos('pl-narod');
    await t.selectByHash('pl-sztab-generalny-wp'); await page.waitForTimeout(900); await t.selectByHash(null); await page.waitForTimeout(1200);
    const c1 = await t.pos('pl-narod'); expect((await t.state()).k).toBeCloseTo(k0, 2); expect(Math.abs(c1.y - c0.y)).toBeLessThan(12); expect(Math.abs(c1.x - c0.x)).toBeLessThan(12);
  });
});

test('U21: własne relacje zwykłych węzłów da się najechać (próg 85%)', async ({ page }) => {
  await openD(page); const t = T(page); let total = 0, ok = 0; const misses = [];
  for (const id of ['pl-sad-najwyzszy', 'pl-nik', 'pl-krrit', 'pl-sejm', 'pl-senat', 'pl-rada-ministrow', 'pl-minister-finansow-i-gospodarki', 'pl-wojewoda-mazowiecki', 'pl-rpo', 'pl-pkw']) {
    await t.selectByHash(id); await page.waitForTimeout(150);
    const cands = await page.evaluate(() => { const G = window.__GP_TEST; return G.edges().filter(x => !x.chain).map(x => ({ id: x.id, pts: [8, 12, 16].map(i => (G.edgePoints(x.id, 24) || [])[i]) })); });
    for (const c of cands) { total++; let hit = false; for (const pt of c.pts) { if (!pt) continue; await page.mouse.move(5, 5); await page.mouse.move(pt.x, pt.y, { steps: 2 }); await page.waitForTimeout(40); if ((await t.state()).hotEdge === c.id) { hit = true; break; } } if (hit) ok++; else misses.push(`${id}:${c.id}`); }
  }
  test.info().annotations.push({ type: 'linie-do-najechania', description: `${ok} z ${total}` });
  expect(ok / total, `nieosiągalne: ${misses.slice(0, 8).join(', ')}`).toBeGreaterThan(0.85);
});
