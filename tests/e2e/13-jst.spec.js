// Samorząd: jedno koło na jednostkę (adres ?jst=<TERYT>). Rama krajowa z arkuszy PKW 2024 i szablonów ustrojowych ze sprawdzonymi cytatami ustaw.
// Pilot: województwo łódzkie (decyzja właściciela z 18.09.2026); radni widoczni z nazwiska od początku.
const { test, expect } = require('@playwright/test');
const { D_URL } = require('./helpers');
test.use({ viewport: { width: 1512, height: 803 } });
const open = async (page, teryt, hash = '') => { const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error' && !/favicon|fonts/i.test(m.text())) errors.push(m.text()); }); await page.goto(D_URL + (teryt ? '&jst=' + teryt : '') + hash); await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status').hidden, null, { timeout: 30000 }); await page.waitForTimeout(800); return errors; };
const sel = (page, id) => page.evaluate(i => { location.hash = '#node=' + i; window.dispatchEvent(new PopStateEvent('popstate')); }, id);

for (const u of [{ t: '100000', kind: 'wojewodztwo', name: 'Województwo łódzkie', seats: 33, lead: 'lider' }, { t: '102000', kind: 'powiat', name: 'Powiat zgierski', lead: 'lider' }, { t: '106101', kind: 'mnpp', name: 'Miasto Łódź', lead: 'wojt' }, { t: '102003', kind: 'gmina', name: 'Miasto Zgierz', lead: 'wojt' }])
  test(`${u.name}: koło jednostki z trzema sektorami, rada ma tylu radnych, ile mandatów, każda relacja ma przepis`, async ({ page }) => {
    const errors = await open(page, u.t); const r = await page.evaluate(() => { const G = window.__GP_TEST; return { j: G.jst(), labels: [...document.querySelectorAll('#stage svg text.sector-label')].map(x => x.textContent), title: document.querySelector('#title').textContent, seal: [...document.querySelectorAll('#stage svg .seal-text')].map(x => x.textContent).join(' '), toggle: !document.querySelector('#mode-toggle').hidden }; });
    expect(r.j.kind).toBe(u.kind); expect(r.j.name).toBe(u.name); expect(r.title).toBe(u.name); expect(r.labels).toEqual(['STANOWIĄCA I KONTROLNA', 'WYKONAWCZA', 'NADZÓR I KONTROLA']); expect(r.seal).toMatch(/^Mieszkańcy /); expect(r.toggle, 'widok budżetu jest tylko dla budżetu państwa').toBe(false);
    await sel(page, `jst-${u.t}-rada`); await page.waitForTimeout(400); const c = await page.evaluate(() => { const n = window.__GP_TEST.node(window.__GP_TEST.state().selected); const label = document.querySelector('#view-node .sect-label').textContent; const headPeople = n.head ? (window.__GP_TEST.node(n.head).people || 0) : 0; return { people: n.people, headPeople, label, cards: document.querySelectorAll('#view-node .pgrid .head-card').length, cardNames: [...document.querySelectorAll('#view-node .pgrid .head-card .name')].map(x => x.textContent.trim()), rows: [...document.querySelectorAll('#view-node .row[data-eid] .r-cite')].map(x => x.textContent) }; });
    expect(c.people).toBeGreaterThanOrEqual(15); if (u.seats) expect(c.people).toBe(u.seats); expect(c.label).toContain(`${c.people} miejsc`); expect(c.cards, 'karty: wszyscy radni, plus przewodniczący nad listą, jeśli jest znany i nie jest już na liście').toBeGreaterThanOrEqual(c.people); expect(c.cards).toBeLessThanOrEqual(c.people + c.headPeople); expect(new Set(c.cardNames).size, 'żadna osoba nie ma dwóch kart').toBe(c.cardNames.length); expect(c.rows.length).toBeGreaterThan(3); for (const x of c.rows) expect(x).toMatch(/art\. \d+/);
    expect(errors).toEqual([]);
  });

test('gmina: wójt, burmistrz albo prezydent z danych PKW ma nazwisko, komitet i rok wyboru; stanowisko bez rejestru pokazuje „Brak danych”, nie „Wakat”', async ({ page }) => {
  await open(page, '102003', '#node=jst-102003-wojt'); await page.waitForTimeout(500);
  const w = await page.evaluate(() => ({ title: document.querySelector('#view-node .node-name').textContent, name: document.querySelector('#view-node .head-card .name').textContent.trim(), when: document.querySelector('#view-node .head-card .when').textContent, src: document.querySelector('#view-node .head-card .src').href })); expect(w.title).toBe('Prezydent Miasta Zgierza'); expect(w.name.split(' ').length).toBeGreaterThanOrEqual(2); expect(w.when).toContain('Wybrany 2024'); expect(w.src).toContain('pkw.gov.pl');
  await sel(page, 'jst-102003-skarbnik'); await page.waitForTimeout(400); const s = await page.evaluate(() => { const c = document.querySelector('#view-node .head-card'); return c ? c.textContent : ''; }); const hasPerson = await page.evaluate(() => window.__GP_TEST.node('jst-102003-skarbnik').people > 0); if (!hasPerson) { expect(s).toContain('Brak danych o obsadzie'); expect(s).not.toContain('Wakat'); }
});

test('nawigacja: województwo pokazuje powiaty i miasta, powiat gminy; okruszki prowadzą w górę i do grafu państwa; organ nadzoru ma przejście do grafu państwa', async ({ page }) => {
  await open(page, '100000'); const kids = await page.evaluate(() => [...document.querySelectorAll('#jst-card .jst-kid')].map(a => ({ n: a.querySelector('b').textContent, h: a.getAttribute('href') }))); expect(kids.length).toBe(24); expect(kids.map(k => k.n)).toContain('Powiat zgierski'); expect(kids.map(k => k.n)).toContain('Miasto Łódź');
  await page.click('#jst-card .jst-kid:has-text("Powiat zgierski")'); await page.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.jst() && window.__GP_TEST.jst().teryt === '102000'); const p = await page.evaluate(() => ({ kids: document.querySelectorAll('#jst-card .jst-kid').length, crumb: [...document.querySelectorAll('#crumb a')].map(a => a.textContent) })); expect(p.kids).toBe(9); expect(p.crumb).toEqual(['PL', 'łódzkie']);
  await sel(page, 'jst-102000-wojewoda'); await page.waitForTimeout(400); const x = await page.evaluate(() => { const a = document.querySelector('#view-node .xref a'); return { href: a && a.getAttribute('href'), name: document.querySelector('#view-node .node-name').textContent }; }); expect(x.name).toBe('Wojewoda Łódzki'); expect(x.href).toContain('#node=pl-wojewoda-lodzki'); expect(x.href).not.toContain('jst=');
  await page.click('#crumb a:has-text("PL")'); await page.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.jst() === null); expect(await page.evaluate(() => window.__GP_TEST.ids().length)).toBeGreaterThan(500);
});

test('graf państwa: wyszukiwarka znajduje miejscowość, karta „Samorząd” ma 16 województw, wojewoda prowadzi do swojego województwa', async ({ page }) => {
  await open(page); await page.waitForSelector('#jst-entry', { timeout: 10000 }); expect(await page.locator('#jst-entry .jst-kid').count()).toBe(16);
  await page.click('#q'); await page.waitForTimeout(600); await page.keyboard.type('Zgierz'); await page.waitForTimeout(700); const res = await page.evaluate(() => [...document.querySelectorAll('#results .jst-result .r-name')].map(x => x.textContent)); expect(res.length).toBeGreaterThanOrEqual(2); expect(res.join(' | ')).toContain('Miasto Zgierz'); expect(res.join(' | ')).toContain('Powiat zgierski');
  await page.click('#results .jst-result:has-text("Miasto Zgierz")'); await page.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.jst() && window.__GP_TEST.jst().teryt === '102003');
  await open(page, null, '#node=pl-wojewoda-lodzki'); await page.waitForTimeout(500); await page.click('[data-jst-woj]'); await page.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.jst() && window.__GP_TEST.jst().teryt === '100000');
});

test('nakładka łódzkie: starosta, zarząd, prezydium rady, sekretarz i skarbnik mają nazwiska ze źródłem BIP; gmina w tym samym powiecie ich nie dziedziczy', async ({ page }) => {
  const errors = await open(page, '102000');
  const r = await page.evaluate(() => { const G = window.__GP_TEST; const n = k => G.node('jst-102000-' + k); return { lider: n('lider').people, zarzad: n('zarzad').people, przew: n('przew').people, wice: n('wiceprzew').people, sekretarz: n('sekretarz').people, skarbnik: n('skarbnik').people }; });
  expect(r.lider).toBe(1); expect(r.zarzad).toBeGreaterThanOrEqual(3); expect(r.przew).toBe(1); expect(r.wice).toBeGreaterThanOrEqual(1); expect(r.sekretarz).toBe(1); expect(r.skarbnik).toBe(1);
  await sel(page, 'jst-102000-lider'); await page.waitForTimeout(500);
  const h = await page.evaluate(() => { const c = document.querySelector('#view-node .head-card'); return { text: c.textContent, src: c.querySelector('.src') ? c.querySelector('.src').href : '', vacancy: /Brak danych o obsadzie|Wakat/.test(document.querySelector('#view-node').textContent) }; });
  expect(h.text).toMatch(/Starosta/); expect(h.src).toMatch(/^https:\/\/(www\.)?powiat/); expect(h.vacancy).toBe(false);
  await page.goto(D_URL + '&jst=102003'); await page.waitForFunction(() => window.__GP_TEST && window.__GP_TEST.jst() && window.__GP_TEST.jst().teryt === '102003', null, { timeout: 20000 });
  const g = await page.evaluate(() => { const G = window.__GP_TEST; return { sekretarz: G.node('jst-102003-sekretarz').people, skarbnik: G.node('jst-102003-skarbnik').people, przew: G.node('jst-102003-przew').people }; });
  expect(g, 'gmina Zgierz nie ma jeszcze nakładki, więc stanowiska muszą być puste, nie przepisane z powiatu').toEqual({ sekretarz: 0, skarbnik: 0, przew: 0 });
  expect(errors).toEqual([]);
});

test('nieistniejący kod jednostki daje czytelny komunikat, a nie pustą stronę', async ({ page }) => {
  await page.goto(D_URL + '&jst=109999'); await page.waitForTimeout(2500); const st = await page.evaluate(() => ({ hidden: document.querySelector('#status').hidden, msg: document.querySelector('#status-msg').textContent })); expect(st.hidden).toBe(false); expect(st.msg).toContain('109999');
});

test('losowe jednostki z całej Polski składają się bez błędów (po jednej z każdego województwa)', async ({ page }) => { test.setTimeout(240000);
  await open(page); const picks = await page.evaluate(async () => { const base = new URLSearchParams(location.search).get('data').replace(/pl\/graph\.json.*$/, 'jst/'); const ix = await (await fetch(base + 'index.json')).json(); const by = {}; ix.units.forEach(u => { (by[u.t.slice(0, 2)] = by[u.t.slice(0, 2)] || []).push(u); }); let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; return Object.values(by).map(a => a[Math.floor(rnd() * a.length)]).map(u => ({ t: u.t, s: u.s, n: u.n })); });
  expect(picks.length).toBe(16); const bad = [];
  for (const u of picks) { const errors = await open(page, u.t); const r = await page.evaluate(t => { const G = window.__GP_TEST; return { j: G.jst(), seats: G.node(`jst-${t}-rada`).people }; }, u.t); if (errors.length || !r.j || r.j.teryt !== u.t || r.seats !== u.s) bad.push({ u, r, errors: errors.slice(0, 2) }); }
  expect(bad).toEqual([]);
});
