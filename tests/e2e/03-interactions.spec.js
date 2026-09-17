const { test, expect } = require('@playwright/test');
const { openD, T, settleRot } = require('./helpers');
const VERBS = ['powołuje', 'wybiera', 'zatwierdza', 'wnioskuje', 'nadzoruje', 'zasiada z urzędu', 'doradza', 'administruje', 'kieruje', 'przewodniczy'];
const SAMPLE = ['pl-nik', 'pl-uodo', 'pl-sad-najwyzszy', 'pl-ministerstwo-zdrowia', 'pl-prezes-rady-ministrow', 'pl-komenda-glowna-policji', 'pl-wojewoda-mazowiecki', 'pl-krrit', 'pl-narod'];

for (const id of SAMPLE) test(`najazd: nad ${id} pojawia się pigułka z samą nazwą, w scenie, w kolorze sektora`, async ({ page }) => {
  await openD(page); const t = T(page); const p = await t.pos(id); const n = await t.node(id); expect(p, 'pozycja węzła').not.toBeNull();
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(150);
  const r = await page.evaluate(() => { const g = document.querySelector('g.hov-label'); if (!g) return null; const b = g.getBoundingClientRect(); const rect = g.querySelector('rect'); const st = window.__GP_TEST.stageRect();
    return { text: g.querySelector('text').textContent, fill: getComputedStyle(rect).fill, textFill: getComputedStyle(g.querySelector('text')).fill, inside: b.left >= st.x - 1 && b.right <= st.x + st.w + 1 && b.top >= st.y - 1 && b.bottom <= st.y + st.h + 1, lines: g.querySelectorAll('text').length }; });
  expect(r, 'pigułka po najechaniu').not.toBeNull();
  expect(r.text.replace('…', '')).toBe(n.name.length > 64 ? n.name.slice(0, 63) : n.name);
  expect(r.lines, 'tylko jedna linia tekstu').toBe(1); expect(r.inside, 'pigułka w obrębie sceny').toBe(true);
  expect(r.fill).not.toMatch(/^rgb\(255, 255, 255\)$/); expect(r.textFill).toMatch(/255, 255, 255/);
  await page.mouse.move(5, 5); await page.waitForTimeout(150); expect((await t.state()).hoverPill).toBeNull();
});

test('wybór: klik nie zmienia skali, podświetla, ustawia adres; klik w pustą scenę odznacza', async ({ page }) => {
  await openD(page); const t = T(page); const before = await t.state(); const p = await t.pos('pl-nik');
  await page.mouse.click(p.x, p.y); await page.waitForTimeout(250); const s = await t.state();
  expect(s.selected).toBe('pl-nik'); expect(s.k).toBeCloseTo(before.k, 5); expect(s.selPill, 'nad wybranym węzłem nie ma stałej pigułki (jak w oryginale)').toBeNull(); expect(s.bottomPill).toBe('Najwyższa Izba Kontroli');
  // B1 (runda 4): po kliknięciu graf obraca się i węzeł odjeżdża spod kursora na godz. 6, więc najeżdżamy w jego nowym położeniu
  await settleRot(page); const p2 = await t.pos('pl-nik'); await page.mouse.move(p2.x + 1, p2.y + 1); await page.waitForTimeout(150); expect((await t.state()).hoverPill, 'najazd na wybrany węzeł pokazuje pigułkę').toBe('Najwyższa Izba Kontroli');
  expect(s.ownEdgesDrawn).toBeGreaterThan(0); expect(page.url()).toContain('#node=pl-nik');
  const st = await page.evaluate(() => window.__GP_TEST.stageRect()); await page.mouse.click(st.x + 14, st.y + st.h / 2); await page.waitForTimeout(200);
  expect((await t.state()).selected).toBeNull();
});

test('wstecz: historia przeglądarki cofa wybór węzła', async ({ page }) => {
  await openD(page); const t = T(page);
  for (const id of ['pl-nik', 'pl-sejm']) { const p = await t.pos(id); await page.mouse.click(p.x, p.y); await settleRot(page); } // B1: czekamy na koniec obrotu, zanim odczytamy położenie następnego glifu
  expect((await t.state()).selected).toBe('pl-sejm'); await page.goBack(); await page.waitForTimeout(250); expect((await t.state()).selected).toBe('pl-nik');
  await page.goBack(); await page.waitForTimeout(250); expect((await t.state()).selected).toBeNull();
});

test('linia: najazd pokazuje jedno słowo zgodne z typem, klik przewija panel do tej relacji', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-nik');
  const WORD = { appoints: 'powołuje', elects: 'wybiera', confirms: 'zatwierdza', nominates: 'wnioskuje', oversees: 'nadzoruje', ex_officio: 'zasiada z urzędu', advises: 'doradza', administers: 'administruje', dept_head: 'kieruje', office: 'przewodniczy' };
  const cands = await page.evaluate(() => { const G = window.__GP_TEST; return G.edges().filter(x => !x.chain).flatMap(x => { const pts = G.edgePoints(x.id, 20) || []; return [6, 10, 14].map(i => ({ id: x.id, type: x.type, pt: pts[i] })); }); });
  let hit = null; for (const c of cands) { await page.mouse.move(5, 5); await page.mouse.move(c.pt.x, c.pt.y, { steps: 3 }); await page.waitForTimeout(120); const s = await t.state(); if (s.hotEdge === c.id) { hit = { c, s }; break; } }
  expect(hit, 'da się najechać na własną relację wybranego węzła').not.toBeNull();
  expect(hit.s.edgeTip, 'słowo zgodne z typem relacji').toContain(WORD[hit.c.type]);
  await page.mouse.click(hit.c.pt.x, hit.c.pt.y); await page.waitForTimeout(800);
  const row = await page.evaluate(id => { const r = document.querySelector(`.row[data-eid="${CSS.escape(id)}"]`); if (!r) return null; const b = r.getBoundingClientRect(); return { visible: b.top >= 0 && b.bottom <= innerHeight }; }, hit.c.id);
  expect(row, 'wiersz relacji w panelu').not.toBeNull(); expect(row.visible, 'wiersz przewinięty w pole widzenia').toBe(true); expect((await t.state()).selected).toBe('pl-nik');
});

test('linia cudza: klik w relację szefa organu przechodzi do jej adresata i pokazuje ją w panelu', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-nik');
  const cands = await page.evaluate(() => { const G = window.__GP_TEST; return G.edges().filter(x => x.chain).flatMap(x => { const pts = G.edgePoints(x.id, 20) || []; return [6, 10, 14].map(i => ({ id: x.id, to: x.to, from: x.from, pt: pts[i] })); }); });
  test.skip(cands.length === 0, 'brak linii spoza własnych relacji');
  let hit = null; for (const c of cands) { await page.mouse.move(5, 5); await page.mouse.move(c.pt.x, c.pt.y, { steps: 3 }); await page.waitForTimeout(120); if ((await t.state()).hotEdge === c.id) { hit = c; break; } }
  expect(hit, 'da się najechać na linię łańcucha').not.toBeNull();
  await page.mouse.click(hit.pt.x, hit.pt.y); await page.waitForTimeout(800); const s = await t.state();
  expect([hit.to, hit.from]).toContain(s.selected); expect(s.selected).not.toBe('pl-nik');
  expect(await page.evaluate(id => !!document.querySelector(`.row[data-eid="${CSS.escape(id)}"]`), hit.id), 'wiersz tej relacji w panelu adresata').toBe(true);
});

test('legenda: klik poza zamyka i od razu wybiera; Esc najpierw zamyka legendę; przeciąganie zamyka', async ({ page }) => {
  await openD(page); const t = T(page);
  await page.click('#legend-toggle'); expect((await t.state()).legendOpen).toBe(true);
  const share = await page.evaluate(() => { const lb = document.querySelector('#legend-body').getBoundingClientRect(); const st = window.__GP_TEST.stageRect(); return lb.width * lb.height / (st.w * st.h); });
  expect(share, 'legenda zakrywa najwyżej 20% sceny').toBeLessThan(0.20);
  const target = await page.evaluate(() => { const lb = document.querySelector('#legend').getBoundingClientRect(); const G = window.__GP_TEST;
    const c = G.glyphs().filter(g => g.kind === 'primary' && !(g.x > lb.left - 20 && g.x < lb.right + 20 && g.y > lb.top - 20 && g.y < lb.bottom + 20)); const g = c.find(x => x.id === 'pl-sejm') || c[0]; return { id: g.id, x: g.x, y: g.y, covered: G.glyphs().filter(z => z.kind === 'primary').length - c.length }; });
  test.info().annotations.push({ type: 'glify-zasloniete-przez-legende', description: String(target.covered) });
  await page.mouse.click(target.x, target.y); await page.waitForTimeout(300);
  let s = await t.state(); expect(s.legendOpen, 'legenda zamknięta po kliknięciu w glif').toBe(false); expect(s.selected, 'jedno kliknięcie wybiera').toBe(target.id);
  await page.click('#legend-toggle'); await page.keyboard.press('Escape'); s = await t.state(); expect(s.legendOpen).toBe(false); expect(s.selected, 'pierwszy Esc nie odznacza').toBe(target.id);
  await page.keyboard.press('Escape'); expect((await t.state()).selected).toBeNull();
  await page.click('#legend-toggle'); const st = await page.evaluate(() => window.__GP_TEST.stageRect());
  await page.mouse.move(st.x + st.w - 60, st.y + 120); await page.mouse.down(); await page.mouse.move(st.x + st.w - 120, st.y + 170, { steps: 5 }); await page.mouse.up();
  expect((await t.state()).legendOpen, 'legenda zamknięta po przeciągnięciu sceny').toBe(false);
  await page.click('#legend-toggle'); await page.mouse.move(st.x + st.w / 2, st.y + st.h / 2); await page.mouse.wheel(0, -240); await page.waitForTimeout(250);
  expect((await t.state()).legendOpen, 'legenda zamknięta po zoomie kółkiem').toBe(false);
});

test('filtr typów (zwykły węzeł): żeton zostawia na scenie tylko swój typ, drugi klik przywraca wszystkie', async ({ page }) => {
  // węzeł dobierany z danych: pierwszy z listy, który nie jest hubem i ma co najmniej dwa typy relacji (Sejm po dojściu komisji i klubów stał się hubem)
  await openD(page); const t = T(page); let s0 = null; for (const id of ['pl-senat', 'pl-nik', 'pl-krrit', 'pl-sad-najwyzszy', 'pl-rada-ministrow']) { s0 = await t.selectByHash(id); if (!s0.hub && await page.locator('.fchips [data-relkey]:not([data-relkey="*"])').count() >= 2) break; }
  expect(s0.hub).toBe(false); expect(s0.relFilter).toBeNull(); const all = s0.ownEdgesDrawn;
  const key = await page.evaluate(() => document.querySelector('.fchips [data-relkey]:not([data-relkey="*"])').getAttribute('data-relkey'));
  const chip = page.locator(`.fchips [data-relkey="${key}"]`).first(); await chip.click(); await page.waitForTimeout(250);
  const s = await t.state(); const kinds = await page.evaluate(() => [...new Set(window.__GP_TEST.edges().filter(e => !e.chain).map(e => e.type))]);
  expect(s.relFilter).toBe(key); expect(kinds).toEqual([key.split(':')[0]]); expect(s.ownEdgesDrawn).toBeLessThan(all);
  await chip.click(); await page.waitForTimeout(250); expect((await t.state()).ownEdgesDrawn).toBe(all);
});

test('hub: dymek na scalonej linii łączy słowa, klik prowadzi do relacji w panelu', async ({ page }) => {
  await openD(page); const t = T(page); await t.selectByHash('pl-prezes-rady-ministrow'); await page.click('#view-node [data-relkey="*"], .fchips [data-relkey="*"]'); await page.waitForTimeout(300);
  const cands = await page.evaluate(() => { const G = window.__GP_TEST; return G.edges().filter(x => !x.chain && x.merged > 1).slice(0, 25).map(x => ({ id: x.id, types: x.types, pt: (G.edgePoints(x.id, 20) || [])[16] })); });
  let hit = null; for (const c of cands) { await page.mouse.move(5, 5); await page.mouse.move(c.pt.x, c.pt.y, { steps: 3 }); await page.waitForTimeout(120); const s = await t.state(); if (s.hotEdge === c.id) { hit = { c, s }; break; } }
  expect(hit, 'da się najechać na scaloną linię').not.toBeNull(); expect(hit.s.edgeTip).toContain(' · ');
  await page.mouse.click(hit.c.pt.x, hit.c.pt.y); await page.waitForTimeout(700);
  expect(await page.evaluate(id => { const r = document.querySelector(`.row[data-eid="${CSS.escape(id)}"]`); return !!r && r.getBoundingClientRect().bottom <= innerHeight; }, hit.c.id)).toBe(true);
});

test('szukaj: skrót, brak polskich znaków i Enter', async ({ page }) => {
  await openD(page); const t = T(page);
  await page.fill('#q', 'NIK'); await page.waitForTimeout(400); expect(await page.locator('#results .result').first().getAttribute('data-goto')).toBe('pl-nik');
  await page.fill('#q', 'minister finansow'); await page.waitForTimeout(400);
  const ids = await page.locator('#results .result').evaluateAll(els => els.map(e => e.getAttribute('data-goto'))); expect(ids).toContain('pl-minister-finansow-i-gospodarki');
  await page.fill('#q', 'trybunal konst'); await page.waitForTimeout(400); await page.keyboard.press('Enter'); await page.waitForTimeout(250); expect((await t.state()).selected).toBe('pl-trybunal-konstytucyjny');
});

test('szukaj: każdy z 60 losowych węzłów da się znaleźć po pełnej nazwie', async ({ page }) => {
  await openD(page);
  const miss = await page.evaluate(async () => { const G = window.__GP_TEST, ids = G.ids(), q = document.querySelector('#q'), out = []; let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 60; i++) { const id = ids[Math.floor(rnd() * ids.length)], n = G.node(id); q.value = n.name; q.dispatchEvent(new Event('input', { bubbles: true })); await new Promise(r => setTimeout(r, 220));
      const got = [...document.querySelectorAll('#results .result')].map(e => e.getAttribute('data-goto')); if (!got.includes(id)) out.push({ id, name: n.name, got: got.slice(0, 3) }); }
    return out; });
  expect(miss.slice(0, 10), `nieznalezione: ${miss.length} z 60`).toEqual([]);
});

test('panel: próbka 80 węzłów ma podstawę prawną z linkiem, a organy z obsadą mają kartę osoby', async ({ page }) => {
  await openD(page);
  const bad = await page.evaluate(() => { const G = window.__GP_TEST, ids = G.ids(), out = []; let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 80; i++) { const id = ids[Math.floor(rnd() * ids.length)]; location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate')); const n = G.node(id);
      const links = [...document.querySelectorAll('#view-node a[href^="http"], #panel a[href^="http"]')].map(a => a.href); const legal = links.some(h => /eli\.gov\.pl|sejm\.gov\.pl|dziennikustaw|monitorpolski/.test(h));
      if (n.type !== 'constituency' && !legal) out.push({ id, why: 'brak linku do podstawy prawnej' });
      if (n.people && n.people > 0 && !document.querySelector('#panel .head-card, #panel .person, #panel [class*="person"]')) out.push({ id, why: 'brak karty osoby' }); }
    return out; });
  expect(bad.slice(0, 10), `braki w panelu: ${bad.length}`).toEqual([]);
});

test('motyw: przełącznik zmienia tło, zapisuje wybór i przeżywa odświeżenie', async ({ page }) => {
  await openD(page); const bg = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor); const light = await bg();
  await page.click('#btn-theme'); await page.waitForTimeout(200); const dark = await bg(); expect(dark).not.toBe(light);
  expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe('dark'); await page.reload(); await page.waitForFunction(() => window.__GP_TEST);
  expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe('dark');
});
