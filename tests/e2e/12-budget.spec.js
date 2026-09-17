// Widok „Budżet” wzorowany na graph.civlab.org/sf: przełącznik Graf | Budżet, dwa pierścienie (grupy i części budżetowe), suma w środku,
// najechanie pokazuje nazwę i kwotę, klik wybiera organ dysponenta i obraca segment na godz. 6, w panelu jest zakładka „Budżet”.
// Dane: data/pl/budget.json (obok graph.json). GP_BUDGET_URL pozwala podstawić inny plik przy pracy nad widokiem.
const { test, expect } = require('@playwright/test');
const { D_URL, openD, T } = require('./helpers');
const BQ = process.env.GP_BUDGET_URL ? '&budget=' + encodeURIComponent(process.env.GP_BUDGET_URL) : '';
const open = async (page, hash = '') => { const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts/i.test(m.text())) errors.push(m.text()); }); await page.goto(D_URL + BQ + hash); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden, null, { timeout: 30000 }); await page.waitForTimeout(700); return errors; };
const B = page => page.evaluate(() => window.__GP_TEST.budget());
const settleB = page => page.waitForFunction(() => !window.__GP_TEST.budget().rotating, null, { timeout: 6000 }).then(() => page.waitForTimeout(200));
test.use({ viewport: { width: 1512, height: 803 } });
test.beforeEach(() => { test.skip(!process.env.GP_BUDGET_URL && !require('fs').existsSync(require('path').join(__dirname, '../../data/pl/budget.json')), 'brak data/pl/budget.json: widok budżetu jest wtedy wyłączony'); });

test('dane budżetu są spójne: części sumują się do całości, grupy pokrywają wszystkie części, przypisane węzły istnieją', async ({ page }) => {
  await open(page); const b = await B(page); expect(b.available, 'plik budget.json jest obok graph.json').toBe(true);
  const sum = b.segments.reduce((a, s) => a + s.value, 0); expect(Math.abs(sum - b.total) / b.total).toBeLessThan(1e-9); expect(b.groups.reduce((a, g) => a + g.value, 0)).toBeCloseTo(b.total, 0);
  expect(b.count).toBeGreaterThanOrEqual(30); expect(b.groups.length).toBeGreaterThanOrEqual(6); expect(b.groups.length).toBeLessThanOrEqual(12);
  const ids = new Set(await page.evaluate(() => window.__GP_TEST.ids())); const bad = b.segments.filter(s => s.nodeId && !ids.has(s.nodeId)).map(s => s.code); expect(bad, 'części wskazujące nieistniejący węzeł').toEqual([]);
  const mapped = b.segments.filter(s => s.nodeId).reduce((a, s) => a + s.value, 0) / b.total; test.info().annotations.push({ type: 'pokrycie', description: `${(mapped * 100).toFixed(1)}% kwoty ma przypisany węzeł grafu` });
});

test('przełącznik pokazuje pierścień zamiast grafu i z powrotem; suma jest w środku; adres pamięta widok', async ({ page }) => {
  const errors = await open(page); expect(await page.isVisible('#mode-toggle')).toBe(true);
  await page.click('#mode-toggle [data-mode=budget]'); await page.waitForTimeout(500);
  const v = await page.evaluate(() => ({ vp: getComputedStyle(document.querySelector('svg .vp')).display, segs: document.querySelectorAll('svg .budget path.bpart').length, groups: document.querySelectorAll('svg .budget path.bgroup').length, center: [...document.querySelectorAll('svg .bcenter text')].map(t => t.textContent), legend: getComputedStyle(document.querySelector('#legend')).display, zoomer: getComputedStyle(document.querySelector('.zoomer')).display, hash: location.hash }));
  const b = await B(page); expect(v.vp).toBe('none'); expect(v.segs).toBe(b.count); expect(v.groups).toBe(b.groups.length); expect(v.center[0]).toBe('Budżet państwa'); expect(v.center[1]).toMatch(/mld zł$/); expect(v.legend).toBe('none'); expect(v.zoomer).toBe('none'); expect(v.hash).toBe('#view=budget');
  const box = await page.evaluate(() => { const r = document.querySelector('svg .budget .brot').getBoundingClientRect(); const st = window.__GP_TEST.stageRect(); return { top: r.top - st.y, bottom: st.y + st.h - r.bottom, left: r.left - st.x, right: st.x + st.w - r.right, share: r.height / st.h }; });
  expect(box.top).toBeGreaterThanOrEqual(0); expect(box.left).toBeGreaterThanOrEqual(0); expect(box.right).toBeGreaterThanOrEqual(0); expect(box.bottom).toBeGreaterThanOrEqual(40); expect(box.share, 'pierścień wypełnia scenę podobnie jak koło grafu').toBeGreaterThan(0.8);
  await page.click('#mode-toggle [data-mode=graph]'); await page.waitForTimeout(500); expect(await page.evaluate(() => getComputedStyle(document.querySelector('svg .vp')).display)).not.toBe('none'); expect(await page.evaluate(() => location.hash)).toBe(''); expect(errors).toEqual([]);
});

test('najechanie na segment pokazuje nazwę, kwotę i udział; klik w część z organem wybiera ten organ, obraca segment na godz. 6 i otwiera zakładkę „Budżet”', async ({ page }) => {
  await open(page, '#view=budget'); const t = T(page); let b = await B(page); expect(b.mode).toBe('budget');
  const seg = b.segments.filter(s => s.nodeId && s.span > 0.05).sort((x, y) => y.value - x.value)[0]; expect(seg, 'jest duża część z przypisanym węzłem').toBeTruthy();
  await page.mouse.move(seg.x, seg.y); await page.waitForTimeout(250); const tip = await page.evaluate(() => { const e = document.querySelector('#btip'); return { hidden: e.hidden, text: e.textContent }; }); expect(tip.hidden).toBe(false); expect(tip.text).toMatch(/zł/); expect(tip.text).toMatch(/%/);
  await page.mouse.click(seg.x, seg.y); await settleB(page); b = await B(page); const s = await t.state(); expect(s.selected).toBe(seg.nodeId); expect(b.selectedPart).toBe(seg.code);
  const now = b.segments.find(x => x.code === seg.code); const geo = await page.evaluate(() => { const r = document.querySelector('svg .budget .bcenter').getBoundingClientRect(); return { cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; }); expect(Math.abs(now.x - geo.cx), 'segment stoi na godz. 6').toBeLessThan(12); expect(now.y).toBeGreaterThan(geo.cy);
  const ui = await page.evaluate(() => ({ tab: document.querySelector('[role=tab][aria-selected=true]').textContent.trim(), pane: !document.querySelector('[data-pane=budget]').hidden, big: document.querySelector('[data-pane=budget] .bp-big').textContent, labels: [...document.querySelectorAll('svg .budget .blabel')].map(x => x.textContent).length, hash: location.hash }));
  expect(ui.tab).toBe('Budżet'); expect(ui.pane).toBe(true); expect(ui.big).toMatch(/zł$/); expect(ui.labels).toBe(4); expect(ui.hash).toBe(`#node=${seg.nodeId}&view=budget`);
  await page.click('#mode-toggle [data-mode=graph]'); await page.waitForTimeout(600); expect((await t.state()).selected, 'wybór przechodzi do widoku grafu').toBe(seg.nodeId);
});

test('część bez własnego organu (np. obsługa długu, subwencje) pokazuje kartę części zamiast węzła, a link z adresu ją odtwarza', async ({ page }) => {
  await open(page, '#view=budget'); let b = await B(page); const seg = b.segments.filter(s => !s.effNodeId).sort((x, y) => y.value - x.value)[0]; test.skip(!seg, 'wszystkie części mają węzeł własny albo części macierzystej');
  // takie części bywają cienkie jak włos, więc klik idzie wprost w element (tak samo działa Enter na segmencie z fokusem)
  await page.evaluate(c => document.querySelector(`svg .budget path.bpart[data-part="${CSS.escape(c)}"]`).dispatchEvent(new MouseEvent('click', { bubbles: true })), seg.code); await settleB(page); const ui = await page.evaluate(() => ({ sel: window.__GP_TEST.state().selected, title: document.querySelector('#view-node .node-name').textContent, crumb: document.querySelector('#crumb').textContent, hash: location.hash, big: document.querySelector('#view-node .bp-big').textContent }));
  expect(ui.sel).toBe(null); expect(ui.crumb).toContain('Budżet'); expect(ui.hash).toBe('#view=budget&part=' + encodeURIComponent(seg.code)); expect(ui.big).toMatch(/zł$/);
  await page.goto('about:blank'); await open(page, ui.hash); b = await B(page); expect(b.mode).toBe('budget'); expect(b.selectedPart).toBe(seg.code); expect(await page.textContent('#view-node .node-name')).toBe(ui.title);
});

test('każdy organ z częścią budżetową ma zakładkę „Budżet” z kwotą; organ bez części jej nie ma; żaden segment nie psuje strony po kliknięciu', async ({ page }) => {
  const errors = await open(page); const r = await page.evaluate(() => { const G = window.__GP_TEST, b = G.budget(), out = { with: 0, bad: [] }; const ids = [...new Set(b.segments.map(s => s.nodeId).filter(Boolean))];
    for (const id of ids) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate')); const tab = document.querySelector('[data-tab=budget]'); const big = document.querySelector('[data-pane=budget] .bp-big'); if (!tab || !big || !/zł/.test(big.textContent)) out.bad.push(id); else out.with++; }
    location.hash = '#node=pl-narod'; window.dispatchEvent(new PopStateEvent('popstate')); out.narod = !!document.querySelector('[data-tab=budget]'); return out; });
  expect(r.bad.slice(0, 5), 'organy z częścią budżetową bez zakładki').toEqual([]); expect(r.with).toBeGreaterThan(10); expect(r.narod).toBe(false);
  await page.evaluate(() => { location.hash = '#view=budget'; window.dispatchEvent(new PopStateEvent('popstate')); }); await page.waitForTimeout(400);
  const codes = (await B(page)).segments.map(s => s.code); await page.evaluate(cs => { for (const c of cs) { const el = document.querySelector(`svg .budget path.bpart[data-part="${CSS.escape(c)}"]`); el.dispatchEvent(new MouseEvent('click', { bubbles: true })); } }, codes); await page.waitForTimeout(400); expect(errors).toEqual([]);
});

test.describe('telefon 390 px', () => { test.use({ viewport: { width: 390, height: 780 }, isMobile: true, hasTouch: true });
  test('przełącznik jest dostępny, pierścień mieści się nad arkuszem, stuknięcie w segment otwiera arkusz z budżetem', async ({ page }) => {
    await open(page); await page.tap('#mode-toggle [data-mode=budget]'); await page.waitForTimeout(600); const box = await page.evaluate(() => { const r = document.querySelector('svg .budget .brot').getBoundingClientRect(); return { l: r.left, r: innerWidth - r.right, b: r.bottom, sheetTop: document.querySelector('#panel').getBoundingClientRect().top, sx: document.documentElement.scrollWidth > innerWidth }; });
    expect(box.l).toBeGreaterThanOrEqual(0); expect(box.r).toBeGreaterThanOrEqual(0); expect(box.b).toBeLessThanOrEqual(box.sheetTop + 2); expect(box.sx).toBe(false);
    const seg = (await B(page)).segments.filter(s => s.nodeId && s.span > 0.08)[0]; await page.touchscreen.tap(seg.x, seg.y); await page.waitForTimeout(1500); const s = await page.evaluate(() => ({ open: document.querySelector('#panel').classList.contains('open'), tab: (document.querySelector('[role=tab][aria-selected=true]') || {}).textContent })); expect(s.open).toBe(true); expect(s.tab).toBe('Budżet');
  });
});
