const D_URL = '/viewer/variants/D-styl-civlab/index.html?data=../../../data/pl/graph.json';
const SWITCHER_URL = '/dist/graf-panstwa.local.html';
const IGNORED_CONSOLE = [/favicon/i, /Failed to load resource.*fonts/i];
async function openD(page, hash = '') {
  const errors = [];
  page.on('console', m => { if (m.type() === 'error' && !IGNORED_CONSOLE.some(r => r.test(m.text()))) errors.push(m.text()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  await page.goto(D_URL + hash);
  await page.waitForFunction(() => window.__GP_TEST && document.querySelector('#status') && document.querySelector('#status').hidden, null, { timeout: 30000 });
  await settle(page);
  return errors;
}
// czeka, aż skończy się animacja dopasowania widoku (skala i pozycja stabilne przez 400 ms)
async function settle(page) {
  let last = null, stable = 0;
  for (let i = 0; i < 40 && stable < 2; i++) { const cur = await page.evaluate(() => { const s = window.__GP_TEST.state(); const p = window.__GP_TEST.screenPos('pl-narod'); return `${s.k.toFixed(4)}|${p.x.toFixed(1)}|${p.y.toFixed(1)}`; }); stable = cur === last ? stable + 1 : 0; last = cur; await page.waitForTimeout(200); }
}
// B1: czeka, aż skończy się obrót grafu po wyborze węzła kliknięciem (wybór z adresu obraca od razu) i dosunie się widok
async function settleRot(page) { await page.waitForFunction(() => { const s = window.__GP_TEST.state(); return !s.rotating && !s.fanMoving; }, null, { timeout: 6000 }); await page.waitForTimeout(300); }
const T = page => ({
  state: () => page.evaluate(() => window.__GP_TEST.state()),
  pos: id => page.evaluate(i => window.__GP_TEST.screenPos(i), id),
  node: id => page.evaluate(i => window.__GP_TEST.node(i), id),
  // wybór przez adres, tak jak robi to link: bez zależności od trafienia myszą
  selectByHash: id => page.evaluate(i => { location.hash = i ? '#node=' + encodeURIComponent(i) : ''; window.dispatchEvent(new PopStateEvent('popstate')); return window.__GP_TEST.state(); }, id),
});
module.exports = { D_URL, SWITCHER_URL, openD, T, settle, settleRot };
