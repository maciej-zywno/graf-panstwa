// Mapa władzy formalnej: odpowiednik „power map” z oryginału (siatka dwudziestu osób z liniami powołań), ale liczony wyłącznie
// z relacji z podstawą prawną w grafie, bez newsów (decyzja właściciela z 17 i 18.09.2026).
const { test, expect } = require('@playwright/test');
const { D_URL } = require('./helpers');
test.use({ viewport: { width: 1512, height: 803 } });
const open = async (page, hash = '') => { const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts|ERR_/i.test(m.text())) errors.push(m.text()); }); await page.goto(D_URL + hash); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden, null, { timeout: 30000 }); return errors; };

test('ranking: 20 kafli z osobą, stanowiskiem i liczbami relacji; na czele Prezydent albo Prezes Rady Ministrów; bez słów o newsach', async ({ page }) => {
  const errors = await open(page); const pw = await page.evaluate(() => window.__GP_TEST.power());
  expect(pw.available).toBe(true); expect(pw.tiles.length).toBe(20); expect(pw.edges).toBeGreaterThan(500);
  for (let i = 0; i < pw.tiles.length; i++) { const t = pw.tiles[i]; expect(t.rank).toBe(i + 1); expect(t.position.length).toBeGreaterThan(3); if (i) expect(t.score).toBeLessThanOrEqual(pw.tiles[i - 1].score); expect(Object.keys(t.counts).length).toBeGreaterThan(0); }
  expect(['pl-prezydent-rp', 'pl-prezes-rady-ministrow']).toContain(pw.tiles[0].id.replace(/-rzeczypospolitej-polskiej$/, '-rp'));
  expect(pw.tiles.filter(t => t.name).length).toBeGreaterThanOrEqual(17);
  await page.click('#mode-toggle [data-mode="power"]'); await page.waitForTimeout(500);
  const txt = await page.evaluate(() => document.querySelector('#power').textContent + document.querySelector('#power-card').textContent);
  expect(txt).not.toMatch(/artyku|w mediach|w prasie|In the news/i); expect(txt).toMatch(/Bez newsów/);
  expect(errors).toEqual([]);
});

test('przełącznik i adres: trzeci tryb rysuje kafle bez nakładania i linie powołań; #view=power wraca do tego widoku; powrót do grafu chowa mapę', async ({ page }) => {
  await open(page); await page.click('#mode-toggle [data-mode="power"]'); await page.waitForTimeout(500);
  const r = await page.evaluate(() => { const pw = window.__GP_TEST.power(); const rects = [...document.querySelectorAll('#power .ptile')].map(el => el.getBoundingClientRect()); const stage = document.querySelector('#stage').getBoundingClientRect(); let overlaps = 0;
    for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) { const a = rects[i], b = rects[j]; if (a.left < b.right - 6 && b.left < a.right - 6 && a.top < b.bottom - 6 && b.top < a.bottom - 6) overlaps++; }
    return { hash: location.hash, drawn: pw.drawn, lines: pw.lines, links: pw.links, overlaps, inside: rects.every(q => q.left >= stage.left && q.right <= stage.right && q.top >= stage.top && q.bottom <= stage.bottom + 1), graphHidden: getComputedStyle(document.querySelector('#graph .vp')).display === 'none', pressed: document.querySelector('#mode-toggle [data-mode="power"]').getAttribute('aria-pressed') }; });
  expect(r.hash).toBe('#view=power'); expect(r.drawn).toBe(20); expect(r.lines).toBe(r.links); expect(r.lines).toBeGreaterThan(5); expect(r.overlaps, 'kafle nie nakładają się na siebie').toBe(0); expect(r.inside, 'wszystkie kafle mieszczą się na scenie bez przewijania').toBe(true); expect(r.graphHidden).toBe(true); expect(r.pressed).toBe('true');
  await page.reload(); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden, null, { timeout: 30000 }); await page.waitForTimeout(300);
  expect(await page.evaluate(() => window.__GP_TEST.power().mode)).toBe('power');
  await page.click('#mode-toggle [data-mode="graph"]'); await page.waitForTimeout(300);
  expect(await page.evaluate(() => ({ hidden: document.querySelector('#power').hidden, hash: location.hash, mode: window.__GP_TEST.power().mode }))).toEqual({ hidden: true, hash: '', mode: 'graph' });
});

test('kafel: klik wybiera węzeł (panel, adres), podświetla jego linie i przygasza resztę; ponowny klik odznacza; karta na stronie głównej otwiera mapę', async ({ page }) => {
  await open(page); await page.click('#power-card [data-open-power]'); await page.waitForTimeout(500);
  expect(await page.evaluate(() => window.__GP_TEST.power().mode)).toBe('power');
  const second = await page.evaluate(() => window.__GP_TEST.power().tiles[1]);
  await page.click(`#power .ptile[data-pid="${second.id}"]`); await page.waitForTimeout(500);
  const r = await page.evaluate(() => { const pw = window.__GP_TEST.power(); const on = document.querySelectorAll('#power .p-lines path.on').length; const dim = [...document.querySelectorAll('#power .ptile:not(.on)')].length; return { sel: window.__GP_TEST.state().selected, selTile: pw.selTile, hash: location.hash, on, dim, focus: document.querySelector('#power').classList.contains('has-focus'), title: document.querySelector('#view-node .node-name').textContent }; });
  expect(r.sel).toBe(second.id); expect(r.selTile).toBe(second.id); expect(r.hash).toBe(`#node=${encodeURIComponent(second.id)}&view=power`); expect(r.focus).toBe(true); expect(r.on).toBeGreaterThan(0); expect(r.dim, 'kafle bez relacji z wybranym są przygaszone').toBeGreaterThan(0); expect(r.title.length).toBeGreaterThan(3);
  await page.click(`#power .ptile[data-pid="${second.id}"]`); await page.mouse.move(4, 4); await page.waitForTimeout(400); // kursor zjeżdża z kafla: podświetlenie z najazdu ma zniknąć razem z wyborem
  expect(await page.evaluate(() => ({ sel: window.__GP_TEST.state().selected, focus: document.querySelector('#power').classList.contains('has-focus'), hash: location.hash }))).toEqual({ sel: null, focus: false, hash: '#view=power' });
});

test('telefon 390 px: mapa w dwóch kolumnach przewija się, kafle nie nakładają się, a koło jednostki samorządu nie ma tego trybu', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await open(page, '#view=power'); await page.waitForTimeout(500);
  const r = await page.evaluate(() => { const rects = [...document.querySelectorAll('#power .ptile')].map(el => el.getBoundingClientRect()); let overlaps = 0; for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) { const a = rects[i], b = rects[j]; if (a.left < b.right - 6 && b.left < a.right - 6 && a.top < b.bottom - 6 && b.top < a.bottom - 6) overlaps++; } const box = document.querySelector('#power'); return { drawn: rects.length, overlaps, scrolls: box.scrollHeight > box.clientHeight, cols: new Set(rects.map(q => Math.round(q.left / 20))).size, wide: rects.every(q => q.right <= 391) }; });
  expect(r.drawn).toBe(20); expect(r.overlaps).toBe(0); expect(r.scrolls).toBe(true); expect(r.wide).toBe(true);
  await page.goto(D_URL + '&jst=102000'); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden, null, { timeout: 30000 });
  expect(await page.evaluate(() => ({ available: window.__GP_TEST.power().available, toggle: document.querySelector('#mode-toggle').hidden }))).toEqual({ available: false, toggle: true });
});
