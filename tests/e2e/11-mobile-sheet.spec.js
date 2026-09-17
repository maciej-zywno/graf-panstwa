// Zgłoszenie właściciela 17.09.2026: na telefonie nie dało się zwinąć części opisowej w dół, żeby zobaczyć sam graf.
// Przyczyny: uchwyt przewijał się razem z treścią, nie było gestu przeciągania, a większość nagłówka zajmował przycisk tytułu, który arkusza nie zwija.
const { test, expect } = require('@playwright/test');
const { openD } = require('./helpers');
test.use({ viewport: { width: 390, height: 780 }, isMobile: true, hasTouch: true });

const sheet = page => page.evaluate(() => { const pn = document.querySelector('#panel'); const r = pn.getBoundingClientRect(); const h = document.querySelector('#panel-top').getBoundingClientRect(); const tb = document.querySelector('#sheet-toggle'); const s = window.__GP_TEST.state(); return { open: pn.classList.contains('open'), top: Math.round(r.top), headTop: Math.round(h.top), scrollTop: Math.round(pn.scrollTop), vh: innerHeight, selected: s.selected, expanded: tb.getAttribute('aria-expanded'), label: tb.getAttribute('aria-label') }; });
async function swipe(page, x, y0, y1) { const cdp = await page.context().newCDPSession(page); await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: y0 }] }); for (let i = 1; i <= 8; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y0 + (y1 - y0) * i / 8 }] }); await page.waitForTimeout(16); } await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await page.waitForTimeout(750); }

test('nagłówek arkusza zostaje pod palcem po przewinięciu treści, a przycisk zwija arkusz i odsłania cały graf', async ({ page }) => {
  await openD(page, '#node=pl-knf'); await page.waitForTimeout(600); let s = await sheet(page); expect(s.open).toBe(true); expect(s.expanded).toBe('true');
  await page.evaluate(() => { document.querySelector('#panel').scrollTop = 600; }); await page.waitForTimeout(150); const sc = await sheet(page); expect(sc.scrollTop).toBeGreaterThan(300); expect(sc.headTop, 'nagłówek przyklejony do góry arkusza').toBe(sc.top);
  await page.tap('#sheet-toggle'); await page.waitForTimeout(900); s = await sheet(page); expect(s.open).toBe(false); expect(s.expanded).toBe('false'); expect(s.label).toBe('Rozwiń panel'); expect(s.vh - s.top, 'zostaje sam nagłówek').toBeLessThanOrEqual(80); expect(s.selected, 'wybór zostaje').toBe('pl-knf');
  const vis = await page.evaluate(() => { const G = window.__GP_TEST; const top = document.querySelector('#panel').getBoundingClientRect().top; const pr = G.glyphs().filter(g => g.kind === 'primary'); return { all: pr.length, above: pr.filter(g => g.y < top - 6 && g.y > 0 && g.x > 0 && g.x < innerWidth).length }; });
  expect(vis.above / vis.all, 'po zwinięciu widać prawie wszystkie glify organów').toBeGreaterThan(0.95);
  await page.tap('#sheet-toggle'); await page.waitForTimeout(700); expect((await sheet(page)).open).toBe(true);
});

test('przeciąganie: w dół za nagłówek zwija, w górę rozwija, w dół za treść na samej górze zwija, a przewiniętą treść po prostu przewija', async ({ page }) => {
  await openD(page, '#node=pl-knf'); await page.waitForTimeout(600); let s = await sheet(page);
  await swipe(page, 195, s.top + 14, s.top + 280); s = await sheet(page); expect(s.open, 'w dół za nagłówek').toBe(false);
  await swipe(page, 195, 748, 430); s = await sheet(page); expect(s.open, 'w górę za nagłówek').toBe(true);
  await page.evaluate(() => { document.querySelector('#panel').scrollTop = 0; }); await swipe(page, 195, s.top + 230, s.top + 480); s = await sheet(page); expect(s.open, 'w dół za treść na samej górze').toBe(false);
  await swipe(page, 195, 748, 430); await page.evaluate(() => { document.querySelector('#panel').scrollTop = 500; }); s = await sheet(page); await swipe(page, 195, s.top + 230, s.top + 420); const after = await sheet(page); expect(after.open, 'przewinięta treść nie zwija arkusza').toBe(true); expect(after.scrollTop).toBeLessThan(500);
  await swipe(page, 195, after.top + 14, after.top + 40); expect((await sheet(page)).open, 'krótkie szarpnięcie wraca na miejsce').toBe(true);
});

test('stuknięcie w tytuł nadal wraca do przeglądu, a zwinięty arkusz nie łapie fokusu', async ({ page }) => {
  await openD(page, '#node=pl-nik'); await page.waitForTimeout(600); await page.tap('#sheet-toggle'); await page.waitForTimeout(700);
  expect(await page.evaluate(() => document.querySelector('#view-node').inert)).toBe(true);
  await page.tap('#brand-title'); await page.waitForTimeout(700); const s = await sheet(page); expect(s.selected).toBe(null);
});
