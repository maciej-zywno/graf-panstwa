// Runda 3 (2026-09-17): kapsuła Parlamentu jako etykieta grupy + domknięcie 12 usterek z raportu zgodności.
const { test, expect } = require('@playwright/test');
const { openD, T, settleRot } = require('./helpers');

test('kapsuła Parlamentu jest etykietą grupy: bez najazdu i kliknięcia, Zgromadzenie Narodowe dostępne z wyszukiwarki', async ({ page }) => {
  await openD(page); const t = T(page);
  const mid = await page.evaluate(() => { const a = window.__GP_TEST.screenPos('pl-sejm'), b = window.__GP_TEST.screenPos('pl-senat'); return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; });
  await page.mouse.move(5, 5); await page.mouse.move(mid.x, mid.y, { steps: 3 }); await page.waitForTimeout(200); expect((await t.state()).hoverPill, 'brak pigułki między izbami').toBeNull();
  await page.mouse.click(mid.x, mid.y); await page.waitForTimeout(200); expect((await t.state()).selected).toBeNull();
  for (const id of ['pl-sejm', 'pl-senat']) { const p = await t.pos(id); await page.mouse.click(p.x, p.y); await settleRot(page); expect((await t.state()).selected, 'izba nadal klikalna').toBe(id); } // B1: po kliknięciu graf się obraca, położenie drugiej izby czytamy po obrocie
  await page.fill('#q', 'Zgromadzenie Narodowe'); await page.waitForTimeout(400); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  expect((await t.state()).selected).toBe('pl-zgromadzenie-narodowe'); expect(await page.evaluate(() => document.querySelector('g.k-parl').classList.contains('sel')), 'kapsuła podświetlona').toBe(true);
  expect(await page.evaluate(() => document.querySelectorAll('g.k-parl[tabindex], g.k-parl.node').length)).toBe(0);
  const fill = await page.evaluate(() => getComputedStyle(document.querySelector('g.k-parl .glyph')).fill); expect(fill, 'kapsuła ma jasne wypełnienie, nie domyślną czerń SVG').not.toMatch(/^rgb\(0, 0, 0\)$/);
});

test('U11: klik w pustą scenę przy otwartej legendzie zamyka legendę, ale nie kasuje wyboru', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-nik'); await page.click('#legend-toggle'); const st = await page.evaluate(() => window.__GP_TEST.stageRect());
  await page.mouse.click(st.x + st.w - 30, st.y + 300); await page.waitForTimeout(250); let s = await t.state(); expect(s.legendOpen).toBe(false); expect(s.selected).toBe('pl-nik');
  await page.waitForTimeout(800); await page.mouse.click(st.x + st.w - 30, st.y + 300); await page.waitForTimeout(250); expect((await t.state()).selected, 'drugi klik odznacza').toBeNull();
});

test('U15, N12, U19: breadcrumb, podpis wybranego węzła i etykiety źródeł nie są ucięte ani zdublowane (wszystkie węzły)', async ({ page }) => {
  await openD(page);
  const r = await page.evaluate(() => { const G = window.__GP_TEST, crumb = document.querySelector('#crumb'), pill = document.querySelector('#sel-pill'); const out = { crumb: [], pill: [], srcs: [] };
    for (const id of G.ids()) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate'));
      if (crumb.scrollWidth > crumb.clientWidth + 1) out.crumb.push(id); if (pill.scrollHeight > pill.clientHeight + 2) out.pill.push(id);
      const tab = document.querySelector('[data-tab="meta"], [data-tab="src"], [data-tab="sources"]'); if (tab) tab.click(); const labels = [...document.querySelectorAll('#view-node .srcs a')].map(a => a.textContent.trim()); if (new Set(labels).size !== labels.length) out.srcs.push(id); const back = document.querySelector('[data-tab="conn"]'); if (back) back.click(); }
    return { crumb: out.crumb.length, pill: out.pill.length, srcs: out.srcs.length, ex: [out.crumb[0], out.pill[0], out.srcs[0]] }; });
  expect(r, JSON.stringify(r.ex)).toMatchObject({ crumb: 0, pill: 0, srcs: 0 });
});

test('U20: strzałki w wynikach wyszukiwania', async ({ page }) => {
  await openD(page); const t = T(page); await page.fill('#q', 'minister'); await page.waitForTimeout(400);
  await page.keyboard.press('ArrowDown'); await page.keyboard.press('ArrowDown'); const second = await page.evaluate(() => { const a = document.querySelector('#results .result.active'); return a ? { id: a.getAttribute('data-goto'), sel: a.getAttribute('aria-selected'), idx: [...document.querySelectorAll('#results .result')].indexOf(a) } : null; });
  expect(second).not.toBeNull(); expect(second.idx).toBe(1); expect(second.sel).toBe('true'); await page.keyboard.press('ArrowUp'); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  const first = await page.evaluate(() => window.__GP_TEST.state().selected); expect(first).toBeTruthy(); expect(first).not.toBe(second.id);
});

test('N2: żaden żeton typu relacji nie zostawia pustej sceny (wszystkie węzły)', async ({ page }) => {
  test.setTimeout(240000); await openD(page);
  const r = await page.evaluate(() => { const G = window.__GP_TEST; let chips = 0; const empty = []; for (const id of G.ids()) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate'));
      const keys = [...document.querySelectorAll('.fchips [data-relkey]')].map(c => c.getAttribute('data-relkey')).filter(k => k !== '*');
      for (const k of keys) { const c = document.querySelector(`.fchips [data-relkey="${k}"]`); if (!c) continue; if (G.state().relFilter !== k) c.click(); chips++; if (G.edges().filter(e => !e.chain).length === 0) empty.push(id + ' ' + k); } } return { chips, empty: empty.length, ex: empty.slice(0, 6) }; });
  test.info().annotations.push({ type: 'zetony', description: `${r.chips} żetonów, pustych ${r.empty}` }); expect(r.ex, `puste: ${r.empty} z ${r.chips}`).toEqual([]);
});

test('N14: klik w środek glifu wybiera ten glif, także przy narysowanych liniach huba i na drobnych kropkach', async ({ page }) => {
  test.setTimeout(240000); await openD(page); const t = T(page); const bad = [];
  for (const sel of ['pl-prezes-rady-ministrow', 'pl-sad-najwyzszy']) {
    const targets = await page.evaluate(() => { const g = window.__GP_TEST.glyphs().filter(x => !['root', 'parlring', 'parl'].includes(x.kind)); let seed = 5; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const pick = []; for (let i = 0; i < 40; i++) pick.push(g[Math.floor(rnd() * g.length)].id); return [...new Set(pick)]; });
    for (const id of targets) { await t.selectByHash(sel); await page.evaluate(() => { const a = document.querySelector('.fchips [data-relkey="*"]'); if (a && window.__GP_TEST.state().relFilter) a.click(); }); const p = await t.pos(id); await page.mouse.click(p.x, p.y); await page.waitForTimeout(60); const got = (await t.state()).selected; if (got !== id) bad.push(`${sel} → ${id}: ${got}`); }
  }
  expect(bad.slice(0, 8), `nietrafione: ${bad.length}`).toEqual([]);
});

test.describe('telefon 390 px', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  test('N13: zwinięty arkusz jest poza kolejnością Tab, otwarty wraca', async ({ page }) => {
    await openD(page); const st = () => page.evaluate(() => ({ open: document.querySelector('#panel').classList.contains('open'), inert: document.querySelector('#view-home').inert }));
    let s = await st(); expect(s.open).toBe(false); expect(s.inert).toBe(true); await T(page).selectByHash('pl-nik'); await page.waitForTimeout(300); s = await page.evaluate(() => ({ open: document.querySelector('#panel').classList.contains('open'), inert: document.querySelector('#view-node').inert })); expect(s.open).toBe(true); expect(s.inert).toBe(false);
  });
});
