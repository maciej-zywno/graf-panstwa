// Parytet z oryginałem (strona organu, np. /us/commissions/us-commodity-futures-trading-commission, okno 1512×803):
// koło wypełnia wysokość sceny, panel ma 40% szerokości, box zaczyna się od tytułu 30 px, osoby stoją w siatce z „Zobacz wszystkich”.
const { test, expect } = require('@playwright/test');
const { openD, T, SWITCHER_URL } = require('./helpers');
test.use({ viewport: { width: 1512, height: 803 } });

const plate = page => page.evaluate(() => { const r = [...document.querySelectorAll('#stage svg path.plate')].map(e => e.getBoundingClientRect()); const x0 = Math.min(...r.map(a => a.left)), x1 = Math.max(...r.map(a => a.right)), y0 = Math.min(...r.map(a => a.top)), y1 = Math.max(...r.map(a => a.bottom)); const st = window.__GP_TEST.stageRect(); return { w: x1 - x0, h: y1 - y0, top: y0 - st.y, bottom: st.y + st.h - y1, stageH: st.h, stageW: st.w }; });

test('koło: płyty zajmują co najmniej 84% wysokości sceny (oryginał 84,6%) i nie wychodzą poza nią', async ({ page }) => {
  await openD(page); const p = await plate(page);
  test.info().annotations.push({ type: 'kolo', description: `${Math.round(p.w)}×${Math.round(p.h)} w scenie ${Math.round(p.stageW)}×${Math.round(p.stageH)}` });
  expect(p.h / p.stageH, 'udział wysokości płyt w scenie').toBeGreaterThanOrEqual(0.84); expect(p.top).toBeGreaterThanOrEqual(0); expect(p.bottom).toBeGreaterThanOrEqual(40);
});

test('powłoka prototypu nie zabiera wysokości: ramka skórki ma pełną wysokość okna, przycisk motywu stoi w rogu i nie zasłania glifów', async ({ page }) => {
  await page.goto(SWITCHER_URL); const frame = page.frameLocator('#stage'); await expect(frame.locator('#stage svg path.plate').first()).toBeVisible({ timeout: 30000 });
  const fr = await page.evaluate(() => { const r = document.querySelector('#stage').getBoundingClientRect(); return { y: r.y, h: r.height, vh: innerHeight }; }); expect(fr.y).toBe(0); expect(fr.h).toBe(fr.vh);
  const f = page.frames().find(x => x !== page.mainFrame()); await f.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.state().k > 0); await page.waitForTimeout(1500);
  const theme = await f.evaluate(() => { const r = document.querySelector('#btn-theme').getBoundingClientRect(); return { right: innerWidth - r.right }; }); expect(theme.right, 'bez przełącznika przycisk motywu wraca do rogu').toBeLessThanOrEqual(16);
  for (const id of [null, 'pl-knf', 'pl-sejm', 'pl-prezes-rady-ministrow']) { if (id) { await f.evaluate(i => { location.hash = '#node=' + i; window.dispatchEvent(new PopStateEvent('popstate')); }, id); await page.waitForTimeout(500); }
    const hit = await f.evaluate(() => window.__GP_TEST.glyphs().filter(g => { const el = document.elementFromPoint(g.x, g.y); return el && el.closest && el.closest('#btn-theme, .search'); }).map(g => g.id)); expect(hit, `glify pod przyciskami przy ${id}`).toEqual([]); }
});

test('panel: 40% szerokości okna, box zaczyna się od tytułu 30 px / 600, opis 16 px, etykiety pod podstawą prawną', async ({ page }) => {
  await openD(page, '#node=pl-knf');
  const r = await page.evaluate(() => { const card = document.querySelector('#view-node .card'); const h = card.querySelector('.node-name'), d = card.querySelector('p.desc'); const hs = getComputedStyle(h), ds = getComputedStyle(d); const kids = [...card.children].map(e => e.className.split(' ')[0]);
    return { panelW: document.querySelector('#panel').getBoundingClientRect().width, vw: innerWidth, first: card.firstElementChild === h, title: [hs.fontSize, hs.fontWeight], desc: ds.fontSize, order: kids, pad: getComputedStyle(card).padding, radius: getComputedStyle(card).borderRadius }; });
  expect(Math.round(r.panelW)).toBe(Math.round(r.vw * 0.4)); expect(r.first, 'tytuł jest pierwszym elementem boxu').toBe(true); expect(r.title).toEqual(['30px', '600']); expect(r.desc).toBe('16px'); expect(r.pad).toBe('24px 24px 28px'); expect(r.radius).toBe('12px');
  expect(r.order.indexOf('node-meta'), 'etykiety typu stoją po linkach i podstawie prawnej').toBeGreaterThan(r.order.indexOf('linkrow'));
});

test('panel: osoby w siatce dwóch kolumn, szef pierwszy i bez dubla, „Zobacz wszystkich (N)” rozwija i zwija', async ({ page }) => {
  await openD(page, '#node=pl-knf');
  const grid = () => page.evaluate(() => { const g = document.querySelector('#view-node .pgrid'); const cards = [...g.querySelectorAll('.head-card')]; const vis = cards.filter(c => c.offsetParent !== null); const names = cards.map(c => c.querySelector('.name').textContent.trim()); return { total: cards.length, visible: vis.length, cols: new Set(vis.map(c => Math.round(c.getBoundingClientRect().left))).size, lead: cards.filter(c => c.classList.contains('lead')).length, leadFirst: cards[0].classList.contains('lead'), dup: names.length - new Set(names).size, label: document.querySelector('#view-node .sect-label').textContent.trim(), btn: document.querySelector('[data-seeall]').textContent.trim() }; });
  const a = await grid(); expect(a.visible).toBe(4); expect(a.cols).toBe(2); expect(a.lead).toBe(1); expect(a.leadFirst).toBe(true); expect(a.dup, 'ta sama osoba dwa razy').toBe(0); expect(a.label).toMatch(/^13 miejsc/); expect(a.btn).toBe(`Zobacz wszystkich (${a.total})`);
  await page.click('[data-seeall]'); const b = await grid(); expect(b.visible).toBe(b.total); expect(b.btn).toBe('Zwiń listę'); await page.click('[data-seeall]'); expect((await grid()).visible).toBe(4);
});

test('każdy węzeł z osobami pokazuje kartę, nazwy kart się nie dublują, a długie tytuły mieszczą się w boxie', async ({ page }) => {
  await openD(page);
  const bad = await page.evaluate(() => { const G = window.__GP_TEST, out = []; for (const id of G.ids()) { location.hash = '#node=' + id; window.dispatchEvent(new PopStateEvent('popstate')); const card = document.querySelector('#view-node .card'); const h = card.querySelector('.node-name'); if (h.scrollWidth > h.clientWidth + 1) out.push({ id, why: 'tytuł wystaje' });
      for (const g of card.querySelectorAll('.pgrid')) { const names = [...g.querySelectorAll('.head-card:not(.vacant) .name:not(.ph)')].map(x => x.textContent.trim()); if (new Set(names).size !== names.length) out.push({ id, why: 'dubel osoby' }); } if (card.scrollWidth > card.clientWidth + 1) out.push({ id, why: 'box przewija się w poziomie' }); } return out; });
  expect(bad.slice(0, 8), `węzły z usterką boxu: ${bad.length}`).toEqual([]);
});

test('wyszukiwarka jak w oryginale: ikona w lewym górnym rogu sceny, rozwija się po kliknięciu i po „/”, Esc zamyka bez odznaczania węzła', async ({ page }) => {
  await openD(page, '#node=pl-nik'); const t = T(page);
  const box = () => page.evaluate(() => { const r = document.querySelector('.search').getBoundingClientRect(); const st = window.__GP_TEST.stageRect(); return { w: Math.round(r.width), dx: Math.round(r.left - st.x), dy: Math.round(r.top - st.y) }; });
  const closed = await box(); expect(closed.w).toBe(40); expect(closed.dx).toBeGreaterThanOrEqual(8); expect(closed.dx).toBeLessThanOrEqual(24); expect(closed.dy).toBeLessThanOrEqual(24);
  await page.click('#q'); await page.waitForTimeout(350); expect((await box()).w).toBeGreaterThan(300); await page.keyboard.type('trybunal stanu'); await page.waitForTimeout(400);
  const res = await page.evaluate(() => { const r = document.querySelector('#results').getBoundingClientRect(); const first = document.querySelector('#results .result'); return { id: first && first.getAttribute('data-goto'), visible: r.height > 30, top: r.top }; }); expect(res.id).toBe('pl-trybunal-stanu'); expect(res.visible).toBe(true);
  await page.keyboard.press('Escape'); await page.waitForTimeout(350); expect((await box()).w).toBe(40); expect((await t.state()).selected, 'Esc w polu nie odznacza węzła').toBe('pl-nik');
  await page.keyboard.press('/'); await page.waitForTimeout(350); expect((await box()).w).toBeGreaterThan(300); expect(await page.evaluate(() => document.activeElement.id)).toBe('q');
});

for (const vp of [{ width: 1512, height: 803 }, { width: 1280, height: 720 }, { width: 1024, height: 640 }]) test(`okno ${vp.width}×${vp.height}: ikona wyszukiwarki i przycisk motywu nie zasłaniają glifów przy żadnym z obrotów próby`, async ({ page }) => {
  await page.setViewportSize(vp); await openD(page); const t = T(page);
  for (const id of [null, 'pl-knf', 'pl-sejm', 'pl-senat', 'pl-prezes-rady-ministrow', 'pl-nik', 'pl-trybunal-konstytucyjny', 'pl-prezydent-rp']) { if (id) { await t.selectByHash(id); await page.waitForTimeout(250); }
    const covered = await page.evaluate(() => window.__GP_TEST.glyphs().filter(g => { const el = document.elementFromPoint(g.x, g.y); return el && el.closest && el.closest('.search, #btn-theme, #rel-bar, #sel-pill'); }).map(g => g.id)); expect(covered.slice(0, 6), `glify pod nakładkami przy ${id}`).toEqual([]); }
});

// Pomiar oryginału (okno 1512×803, koło 671 px): nazwy sektorów 1,506% średnicy koła, napisy wewnątrz koła (CONGRESS, CABINET, nazwy pierścieni) 1,369%, pieczęć 1,643%, grubość co najmniej 600.
test('napisy na scenie mają proporcje oryginału względem średnicy koła i mieszczą się w swoich łukach', async ({ page }) => {
  await openD(page);
  const r = await page.evaluate(() => { const svg = document.querySelector('#stage svg'); const pl = [...svg.querySelectorAll('path.plate')].map(e => e.getBoundingClientRect()); const D = Math.max(...pl.map(a => a.right)) - Math.min(...pl.map(a => a.left));
    const labels = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && !t.closest('g.hov-label, g.sel-label')).map(t => { const cs = getComputedStyle(t); const m = t.getScreenCTM(); const tp = t.querySelector('textPath'); const path = tp ? document.querySelector(tp.getAttribute('href')) : null; return { txt: t.textContent.trim(), cls: t.getAttribute('class'), pct: parseFloat(cs.fontSize) * Math.hypot(m.a, m.b) / D * 100, weight: +cs.fontWeight, len: tp ? tp.getComputedTextLength() : null, arc: path ? path.getTotalLength() : null }; }); return { D, labels }; });
  const want = { 'ring-label': 1.369, 'band-label': 1.369, 'vband-label': 1.369, 'parl-label': 1.369, 'sector-label': 1.506, 'seal-text': 1.643 };
  expect(r.labels.length).toBeGreaterThanOrEqual(10); expect(r.labels.map(l => l.txt)).toContain('PARLAMENT');
  for (const l of r.labels) { const w = want[l.cls]; expect(w, `nieznana klasa napisu ${l.cls} („${l.txt}”)`).toBeTruthy(); expect(Math.abs(l.pct / w - 1), `„${l.txt}”: ${l.pct.toFixed(3)}% koła, wzorzec ${w}%`).toBeLessThan(0.04); expect(l.weight, `„${l.txt}”: grubość`).toBeGreaterThanOrEqual(600);
    if (l.arc != null) expect(l.len + 10, `„${l.txt}” mieści się w łuku`).toBeLessThanOrEqual(l.arc); }
});
