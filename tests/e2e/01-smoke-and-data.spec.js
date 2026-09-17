const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const path = require('path');
const { openD, T } = require('./helpers');
const ROOT = path.resolve(__dirname, '../..');

test('dane: graph.json przechodzi walidator schematu', () => {
  const out = execFileSync('python3', ['scripts/validate-chunk.py', 'data/pl/graph.json'], { cwd: ROOT }).toString();
  expect(out).toContain('WYNIK: OK');
});

test('start: skórka D ładuje się bez błędów konsoli i rysuje graf', async ({ page }) => {
  const t0 = Date.now(); const errors = await openD(page); const ms = Date.now() - t0;
  const info = await page.evaluate(() => ({ glyphs: window.__GP_TEST.glyphs().length, ids: window.__GP_TEST.ids().length, st: window.__GP_TEST.state() }));
  expect(errors, 'błędy konsoli').toEqual([]);
  expect(info.ids).toBeGreaterThan(400); expect(info.glyphs).toBeGreaterThan(250);
  expect(info.st.selected).toBeNull(); expect(info.st.legendOpen).toBe(false);
  expect(ms, 'czas do gotowości [ms]').toBeLessThan(6000);
  test.info().annotations.push({ type: 'czas-ladowania-ms', description: String(ms) });
});

test('linki: każdy z węzłów otwiera się przez #node=<id>, panel pokazuje jego nazwę i wszystkie relacje', async ({ page }) => {
  await openD(page);
  const res = await page.evaluate(async () => {
    const G = window.__GP_TEST, bad = [];
    for (const id of G.ids()) {
      location.hash = '#node=' + encodeURIComponent(id); window.dispatchEvent(new PopStateEvent('popstate'));
      const s = G.state(), n = G.node(id);
      if (s.selected !== id) bad.push({ id, why: 'nie wybrano', got: s.selected });
      else if ((s.panelTitle || '').trim() !== n.name.trim()) bad.push({ id, why: 'tytuł panelu', got: s.panelTitle, want: n.name });
      else if (s.relRows !== n.inCount + n.outCount) bad.push({ id, why: 'liczba wierszy relacji', got: s.relRows, want: n.inCount + n.outCount });
      else if (!s.bottomPill || s.bottomPill.trim() !== n.name.trim()) bad.push({ id, why: 'dolna pigułka', got: s.bottomPill });
    }
    return { total: G.ids().length, bad };
  });
  test.info().annotations.push({ type: 'sprawdzone-wezly', description: String(res.total) });
  expect(res.bad.slice(0, 25), `niezgodne węzły: ${res.bad.length} z ${res.total}`).toEqual([]);
});

test('wydajność: wybranie największego huba (Premier) trwa poniżej 600 ms', async ({ page }) => {
  await openD(page);
  const ms = await page.evaluate(() => { const t = performance.now(); location.hash = '#node=pl-prezes-rady-ministrow'; window.dispatchEvent(new PopStateEvent('popstate')); return performance.now() - t; });
  test.info().annotations.push({ type: 'wybor-premiera-ms', description: ms.toFixed(0) });
  expect(ms).toBeLessThan(600);
});
