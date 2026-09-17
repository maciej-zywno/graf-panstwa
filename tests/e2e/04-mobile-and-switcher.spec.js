const { test, expect } = require('@playwright/test');
const { openD, T, SWITCHER_URL } = require('./helpers');

test.describe('telefon 390 px', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  test('brak poziomego przewijania, graf widoczny, wybór otwiera arkusz', async ({ page }) => {
    const errors = await openD(page); const t = T(page);
    const m = await page.evaluate(() => ({ sw: document.scrollingElement.scrollWidth, iw: innerWidth, glyphsInView: window.__GP_TEST.glyphs().filter(g => g.x > 0 && g.x < innerWidth && g.y > 0 && g.y < innerHeight).length }));
    expect(errors).toEqual([]); expect(m.sw, 'szerokość dokumentu').toBeLessThanOrEqual(m.iw + 1); expect(m.glyphsInView).toBeGreaterThan(100);
    await t.selectByHash('pl-nik'); await page.waitForTimeout(300);
    const sheet = await page.evaluate(() => { const p = document.querySelector('#panel'); const b = p.getBoundingClientRect(); return { open: p.classList.contains('open'), top: b.top, h: innerHeight }; });
    expect(sheet.open, 'arkusz otwarty po wyborze').toBe(true); expect(sheet.top).toBeLessThan(sheet.h - 120);
  });
});

test.describe('powłoka prototypu (artefakt): jedna skórka D, bez przełącznika', () => {
  test('skórka ładuje się w ramce z danymi i bez błędów, węzeł z adresu trafia do widoku, przełącznika nie widać', async ({ page }) => {
    const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts/i.test(m.text())) errors.push(m.text()); });
    await page.goto(SWITCHER_URL + '#node=pl-nik');
    const frame = await (await page.waitForSelector('#stage')).contentFrame();
    await frame.waitForFunction(() => window.GRAPH_DATA && window.__GP_TEST && document.querySelectorAll('svg path, svg circle, svg rect').length > 50, null, { timeout: 30000 }); await page.waitForTimeout(900);
    const info = await frame.evaluate(() => ({ hash: location.hash, title: (document.querySelector('.node-name') || {}).textContent || null, skin: window.__GP_TEST.skin }));
    expect(info.hash).toContain('pl-nik'); expect(info.title).toContain('Najwyższa Izba Kontroli');
    expect(await page.isVisible('.bar'), 'przełącznik skórek jest ukryty').toBe(false); expect(await page.locator('#skin-select option').count()).toBe(1);
    const fr = await page.evaluate(() => { const r = document.querySelector('#stage').getBoundingClientRect(); return { y: r.y, h: r.height, vh: innerHeight }; }); expect(fr.y).toBe(0); expect(fr.h).toBe(fr.vh);
    expect(errors, 'błędy konsoli w powłoce').toEqual([]);
  });
  test('wybór węzła w ramce trafia do adresu powłoki (link do skopiowania)', async ({ page }) => {
    await page.goto(SWITCHER_URL); const frame = await (await page.waitForSelector('#stage')).contentFrame(); await frame.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.state().k > 0, null, { timeout: 30000 });
    await frame.evaluate(() => { location.hash = '#node=pl-sejm'; window.dispatchEvent(new PopStateEvent('popstate')); }); await page.waitForTimeout(900); expect(page.url()).toContain('node=pl-sejm');
  });
});
