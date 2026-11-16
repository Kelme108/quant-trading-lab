// End-to-end check of the universe sections (Cripto, B3: WIN e WDO, Substitutos) of the Resultados pages in a real headless Chrome or Edge, over the DevTools protocol
// (Node >= 22, no packages). Same harness as research/tools/portal_e2e.mjs.
//   node research/tools/portal_universes_e2e.mjs [http://127.0.0.1:8765]
// Needs the dashboard server running (python -m lab.dashboard serve). Exit code 1 if any check fails.
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const chrome = process.env.CHROME || ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(existsSync);
if (!chrome) { console.log('SKIP: no Chrome/Edge found'); process.exit(0); }

const port = 9300 + Math.floor(Math.random() * 500);
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'e2e-'))}`, '--window-size=1600,1000', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch { /* not up yet */ } await sleep(200); }
const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
await new Promise((r) => { ws.onopen = r; });
let id = 0; const pending = new Map(); const errors = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === 'Runtime.exceptionThrown') errors.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
  if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') errors.push(d.params.args.map((a) => a.value || a.description).join(' '));
};
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || 'eval failed'); return r.result.result.value; };
await send('Runtime.enable'); await send('Page.enable');
const text = () => js(`document.querySelector('#page').textContent`);
const waitFor = async (expr, ms = 60000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await js(expr)) return true; await sleep(400); } return false; };
const open = async (hash) => { await send('Page.navigate', { url: `${BASE}/${hash}` }); await waitFor(`!!document.querySelector('#page') && document.readyState === 'complete'`); };
const go = async (hash) => { await js(`location.hash = ${JSON.stringify(hash)}`); await sleep(400); };
const loaded = () => waitFor(`!document.querySelector('#page .loading')`);

let failed = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); if (!ok) failed++; };


const setWidth = async (w) => { await send('Emulation.setDeviceMetricsOverride', { width: w, height: 900, deviceScaleFactor: 1, mobile: w < 700 }); await sleep(300); };
const noHScroll = () => js(`document.documentElement.scrollWidth <= innerWidth + 1`);
const U = {};
for (const u of ['b3', 'proxies']) U[u] = await (await fetch(`${BASE}/api/universe?id=${u}`)).json();
check('api: b3 universe has rules and rows', (U.b3.hypotheses || []).length > 5 && (U.b3.strategies || []).length > 5, `${(U.b3.hypotheses || []).length} rules`);
check('api: proxies universe has rules', (U.proxies.hypotheses || []).length > 3);
const ti = await (await fetch(`${BASE}/api/trade-index?universe=b3`)).json();
check('api: b3 trade index', (ti.trades || []).length > 1000, `${(ti.trades || []).length} trades`);

await open('#/overview'); await loaded();
check('nav: Cripto, B3 and Substitutos groups', await js(`[...document.querySelectorAll('.sbh .lbl')].map(x=>x.textContent).join('|')`).then((t) => /Cripto/.test(t) && /B3: WIN e WDO/.test(t) && /Substitutos/.test(t)));
check('nav: only the current page group is open, labels visible', await js(`(() => { const open = [...document.querySelectorAll('.sbg.open .sbh .lbl')].map((x) => x.textContent); const lbl = document.querySelector('.sbi[aria-current=page] .lbl'); return open.includes('Cripto') && !open.includes('Substitutos') && !!lbl && lbl.getBoundingClientRect().width > 20; })()`));
check('crypto home still renders with tabs', await waitFor(`!!document.querySelector('.ux-tabs') && /ideias/.test(document.querySelector('#page').textContent)`));

for (const u of ['b3', 'proxies']) {
  await go(`#/${u}`); await loaded();
  check(`${u}: home renders`, await waitFor(`/ideias/.test(document.querySelector('#page').textContent) && !!document.querySelector('.ux-note')`), (await text()).slice(0, 80));
  check(`${u}: tab marks the universe`, await js(`(document.querySelector('.ux-tab[aria-current=page]')||{}).textContent || ''`).then((t) => t.length > 1));
  await go(`#/${u}-leaderboard`); await loaded();
  const id0 = (U[u].strategies[0] || {}).id;
  check(`${u}: ranking lists a rule`, await waitFor(`document.querySelector('#page').textContent.includes(${JSON.stringify(id0)})`), id0);
  check(`${u}: ranking links stay in the universe`, await js(`[...document.querySelectorAll('#page a[href*="strategy/"]')].every(a => a.getAttribute('href').startsWith('#/${u}-strategy/'))`));
  await go(`#/${u}-trades`); await loaded();
  check(`${u}: operations page loads its index`, await waitFor(`/opera/i.test(document.querySelector('#page').textContent) && !document.querySelector('#page .loading')`, 90000));
  await go(`#/${u}-compare`); await loaded();
  check(`${u}: compare renders`, await waitFor(`document.querySelector('#page').textContent.length > 200`));
  await go(`#/${u}-strategy/${encodeURIComponent(id0)}`); await loaded();
  check(`${u}: strategy report`, await waitFor(`/Relatório da prova/.test(document.querySelector('#page').textContent)`), id0);
  const exp = (U[u].experiments.items || [])[0];
  await go(`#/${u}-chart/${encodeURIComponent(exp.id)}`);
  check(`${u}: candle chart with trades`, await waitFor(`!!document.querySelector('#page svg') && /Opera/.test(document.querySelector('#page').textContent) && !document.querySelector('#page .loading')`, 90000), exp.id);
  check(`${u}: chart offers 1, 5 and 15 minutes`, await waitFor(`['1m','5m','15m'].every((t) => !!document.querySelector('[data-fkey="seg:tr-tf:' + t + '"]'))`, 60000));
  await js(`document.querySelector('[data-fkey="seg:tr-tf:1m"]').click()`);
  check(`${u}: 1-minute session chart`, await waitFor(`document.querySelector('[data-fkey="seg:tr-tf:1m"]') && document.querySelector('[data-fkey="seg:tr-tf:1m"]').getAttribute('aria-pressed') === 'true' && !!document.querySelector('#page .trchart canvas')`, 60000));
  const day0 = await js(`(document.querySelector('[data-fkey="sel:tr-day"]') || {}).value || ''`);
  await js(`(document.querySelector('[data-fkey="tr-prev"]') || {click(){}}).click()`);
  check(`${u}: previous session loads`, await waitFor(`((document.querySelector('[data-fkey="sel:tr-day"]') || {}).value || '') !== ${JSON.stringify(day0)} && !!document.querySelector('#page .trchart canvas')`, 60000), day0);
  await setWidth(390); await go(`#/${u}-leaderboard`); await loaded(); await sleep(600);
  check(`${u}: no horizontal scroll at 390 px`, await noHScroll());
  await setWidth(1600);
}
await go('#/leaderboard'); await loaded();
check('back on crypto: crypto rules and periods, not B3 ones', await waitFor(`document.querySelector('#page').textContent.includes('2017 a jul/2024') && !document.querySelector('#page').textContent.includes('C-SessionHighBreakRetest')`));
check('no JavaScript errors', errors.length === 0, errors.slice(0, 3).join(' | '));
// --- B3 demonstration on the Clear demo (lab/demo_b3.py, demo_b3.js) ---
await setWidth(1600);
await go('#/b3-demo');
await waitFor(`document.querySelector('#page').textContent.includes('Demonstração na conta demo da Clear') && !document.querySelector('#page .loading')`, 30000);
const dt = await text();
check('demo page: WIN card, status and research verdict', /P-004 no WIN/.test(dt) && /Robô/.test(dt) && /Validação/.test(dt), dt.slice(0, 160));
check('demo page: both contracts in the strip', /WIN · WIN/.test(dt) && /WDO · WDO/.test(dt));
await js(`document.querySelector('[data-fkey="db-sel:demo-b3-p004-wdo"]').click()`); await sleep(600);
check('demo page: WDO card opens', /P-004 no WDO/.test(await text()));
await js(`document.querySelector('[data-fkey="db-sel:demo-b3-p004-win"]').click()`); await sleep(600);
check('demo page: menu entry under B3', await js(`[...document.querySelectorAll('a')].some((a) => a.getAttribute('href') === '#/b3-demo')`));
const hasSnap = await js(`fetch('/api/demo-b3').then((r) => r.json()).then((d) => d.items.some((i) => i.snapshot && i.snapshot.bars.length))`);
if (hasSnap) check('demo page: candle chart drawn', await waitFor(`!!document.querySelector('#page .trchart canvas')`, 15000));
if (hasSnap) {
  const n1 = await js(`__demoB3().n`);
  await js(`[...document.querySelectorAll('#page button, #page [role=radio], #page label')].find((b) => b.textContent.trim() === '5 min').click()`); await sleep(800);
  const n5 = await js(`__demoB3().n`);
  check('demo page: 1 min opens first and 5 min has about a fifth of the candles', n1 > 0 && n5 > 0 && n5 < n1 && n5 >= Math.floor(n1 / 5), `${n1} vs ${n5}`);
  const before = await js(`__demoB3().chart ? 1 : 0`);
  await sleep(6500);
  check('demo page: live poll keeps the chart in place', before === 1 && await js(`__demoB3().chart`));
}
await setWidth(390);
check('demo page: no horizontal scroll on a phone', await noHScroll());
check('nav on a phone: list hidden until Menu is pressed', await js(`getComputedStyle(document.getElementById('navlist')).display === 'none'`));
await js(`document.querySelector('.menubtn').click()`); await sleep(300);
check('nav on a phone: Menu opens the groups', await js(`getComputedStyle(document.getElementById('navlist')).display !== 'none' && document.querySelector('.sbi[aria-current=page]').getBoundingClientRect().height > 0`));
await js(`document.querySelector('.menubtn').click()`); await sleep(200);
await setWidth(1600);
check('demo page: no script errors', !errors.length, errors.slice(0, 3).join(' | '));
if (process.env.SHOT) { const sh = await send('Page.captureScreenshot', { format: 'png' }); (await import('node:fs')).writeFileSync(process.env.SHOT, Buffer.from(sh.result.data, 'base64')); }

console.log(failed ? `${failed} FAILED` : 'ALL PASSED');
proc.kill(); ws.close();
process.exit(failed ? 1 : 0);
