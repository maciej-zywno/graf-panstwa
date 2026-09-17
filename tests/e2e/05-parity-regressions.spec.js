// Regresje z raportu zgodności 2026-09-17 (tests/parity/report-2026-09-17.md): U1, U2, U3, U8, U9, U13, U17.
const { test, expect } = require('@playwright/test');
const { openD, T } = require('./helpers');

for (const id of ['pl-prezes-ipn', 'pl-sejm', 'pl-prezes-rady-ministrow', 'pl-nik']) test(`U1: przy wybranym ${id} żaden glif nie leży pod nakładką sceny`, async ({ page }) => {
  await openD(page); await T(page).selectByHash(id); await page.waitForTimeout(250);
  const covered = await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => { const el = document.elementFromPoint(g.x, g.y); return el && el.closest && el.closest('#rel-bar, #sel-pill, #legend, #btn-theme'); }).map(g => g.id));
  expect(covered.slice(0, 10), `glify pod nakładkami: ${covered.length}`).toEqual([]);
});

test('U2: dla każdego węzła pigułka i glif wybranego węzła są widoczne (nie pod żetonami ani podpisem)', async ({ page }) => {
  await openD(page);
  const bad = await page.evaluate(() => { const G = window.__GP_TEST, out = []; const hit = (a, b) => !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
    for (const id of G.ids()) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate'));
      const bars = [...document.querySelectorAll('#rel-bar .fchip'), document.querySelector('#sel-pill')].filter(Boolean).map(e => e.getBoundingClientRect()).filter(r => r.width);
      const pill = document.querySelector('g.sel-label'); const pr = pill ? pill.getBoundingClientRect() : null; const sp = G.screenPos(id); const gp = sp ? { left: sp.x - 4, right: sp.x + 4, top: sp.y - 4, bottom: sp.y + 4 } : null;
      if ((pr && bars.some(r => hit(pr, r))) || (gp && bars.some(r => hit(gp, r)))) out.push(id); }
    return out; });
  expect(bad.slice(0, 10), `węzły zasłonięte po wybraniu: ${bad.length}`).toEqual([]);
});

test.describe('U3: telefon 390 px', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  for (const id of ['pl-ministerstwo-spraw-wewnetrznych-i-administracji', 'pl-sztab-generalny-wp', 'pl-nik']) test(`wybrany ${id} jest widoczny nad arkuszem`, async ({ page }) => {
    await openD(page, '#node=' + id); await page.waitForTimeout(900);
    const r = await page.evaluate(i => { const sp = window.__GP_TEST.screenPos(i); const top = document.querySelector('#panel').getBoundingClientRect().top; return { y: sp.y, x: sp.x, top, w: innerWidth }; }, id);
    expect(r.y, 'węzeł nad arkuszem').toBeLessThan(r.top - 20); expect(r.y).toBeGreaterThan(20); expect(r.x).toBeGreaterThan(10); expect(r.x).toBeLessThan(r.w - 10);
  });
});

test('U8: tytuł karty pokazuje wybrany węzeł i wraca po odznaczeniu', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-nik'); expect(await page.title()).toBe('Najwyższa Izba Kontroli · Graf Państwa Polskiego');
  await t.selectByHash(null); expect(await page.title()).toBe('Graf Państwa Polskiego');
});

test('U9 i U13: Naród nie ma sektora, a żaden węzeł nie ma zdublowanych etykiet', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-narod');
  const narod = await page.evaluate(() => ({ crumb: document.querySelector('#crumb').textContent.trim(), chips: [...document.querySelectorAll('#view-node .chip')].map(c => c.textContent.trim()) }));
  expect(narod.crumb).toContain('Suweren'); expect(narod.chips).toEqual(['Suweren']);
  const dups = await page.evaluate(() => { const G = window.__GP_TEST, out = []; for (const id of G.ids()) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate')); const c = [...document.querySelectorAll('#view-node .chip')].map(x => x.textContent.trim()); if (new Set(c).size !== c.length) out.push({ id, c }); } return out; });
  expect(dups.slice(0, 8), `węzły ze zdublowanymi etykietami: ${dups.length}`).toEqual([]);
});

test('U17: nieistniejący adres węzła daje komunikat i czyści adres', async ({ page }) => {
  await openD(page, '#node=pl-nie-istnieje'); await page.waitForTimeout(300);
  const r = await page.evaluate(() => ({ hash: location.hash, sel: window.__GP_TEST.state().selected, msg: document.querySelector('#sel-pill').hidden ? null : document.querySelector('#sel-pill').textContent }));
  expect(r.sel).toBeNull(); expect(r.hash).toBe(''); expect(r.msg).toContain('Nie ma węzła');
});
