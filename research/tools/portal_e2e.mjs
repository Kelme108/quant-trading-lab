// End-to-end check of the portal in a real (headless) Chrome, driven over the DevTools protocol (Node >= 22, no packages).
//   node research/tools/portal_e2e.mjs [http://127.0.0.1:8765]
// Needs the dashboard server running (python -m lab.dashboard serve). Exit code 1 if any check fails.
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const BASE = process.argv[2] || 'http://127.0.0.1:8765';
import { existsSync } from 'node:fs';
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
const go = async (hash) => { await js(`location.hash = ${JSON.stringify(hash)}`); await sleep(500); };
const open = async (hash) => { await send('Page.navigate', { url: `${BASE}/${hash}` }); await sleep(1800); };

let failed = 0;
const check = (name, ok, detail = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); if (!ok) failed++; };
const rowsIds = () => js(`[...document.querySelectorAll('table.lb tbody tr')].map((r) => r.dataset.key)`);

// Only live strategies reach the page: archived ones are never sent, so there is no toggle to bring them back.
await open('#/leaderboard');
const onlyCand = await rowsIds();
check('only live strategies are listed', onlyCand.length >= 1, onlyCand.join(','));
const archivedLabel = await js(`document.querySelector('[data-fkey="showall"]').textContent`);
check('header says how many are archived', /\d+ no arquivo/.test(archivedLabel), archivedLabel);
let ids = await rowsIds();
check('ranking lists strategies', ids.length >= 1, `${ids.length} rows`);
check('default sort is by evidence (desc)', JSON.stringify(await js(`[...document.querySelectorAll('table.lb tbody tr .score-n')].map((e) => Number(e.textContent))`)) === JSON.stringify((await js(`[...document.querySelectorAll('table.lb tbody tr .score-n')].map((e) => Number(e.textContent)).sort((a, b) => b - a)`))));
await js(`document.querySelector('[data-fkey="lbth:roi"]').click()`); await sleep(300);
let roi = await js(`[...document.querySelectorAll('table.lb tbody td.c-roi')].map((e) => parseFloat(e.textContent.replace(/\\./g, '').replace(',', '.').replace('−', '-')))`);
check('sorting by ROI orders the rows', roi.every((v, i) => i === 0 || roi[i - 1] >= v) || roi.every((v, i) => i === 0 || roi[i - 1] <= v), roi.slice(0, 4).join(' '));
await js(`document.querySelector('[data-fkey="lbth:roi"]').click()`); await sleep(300);
const roi2 = await js(`[...document.querySelectorAll('table.lb tbody td.c-roi')].map((e) => parseFloat(e.textContent.replace(/\\./g, '').replace(',', '.').replace('−', '-')))`);
check('clicking again reverses the order', roi2[0] !== roi[0]);
await js(`(() => { const s = document.querySelector('[data-fkey="sel:lb-status"]'); s.value = 'pass'; s.dispatchEvent(new Event('change')); })()`); await sleep(300);
ids = await rowsIds();
check('filter "passou nos gates" narrows the list', ids.length > 0 && ids.length < 10, `${ids.length} rows`);
const allPass = await js(`[...document.querySelectorAll('table.lb tbody tr')].every((r) => r.textContent.includes('Passou nos gates'))`);
check('every remaining row passed the gates', allPass);
await js(`(() => { const s = document.querySelector('[data-fkey="sel:lb-status"]'); s.value = 'all'; s.dispatchEvent(new Event('change')); })()`); await sleep(300);
await js(`(() => { const i = document.querySelector('[data-fkey="lb-q"]'); i.value = 'H-009'; i.dispatchEvent(new Event('input')); })()`); await sleep(300);
check('search filters by id', (await rowsIds()).length === 1);
await js(`document.querySelector('[data-fkey="lb-clear"]').click()`); await sleep(500);
check('clear restores the full list', (await rowsIds()).length >= 5);
await js(`document.querySelector('[data-fkey="lb-more"]').click()`); await sleep(300);
check('"Mais métricas" adds columns', await js(`!!document.querySelector('table.lb td.c-net') && !!document.querySelector('table.lb td.c-sharpe')`));
await js(`document.querySelector('[data-fkey="lbsel:H-009"]').click()`); await sleep(500);
await js(`document.querySelector('[data-fkey="lbsel:H-016"]').click()`); await sleep(500);
check('selecting two strategies enables Comparar', await js(`!!document.querySelector('[data-fkey="lb-compare"]') && document.querySelector('[data-fkey="lb-compare"]').textContent === 'Comparar'`));
await js(`document.querySelector('[data-fkey="lb-compare"]').click()`); await sleep(900);
check('compare page opens with both strategies', await js(`location.hash.startsWith('#/compare') && document.querySelectorAll('table.cmp thead th').length === 3`), await js('location.hash'));
check('compare draws the curves, scatter and tables', await js(`document.querySelectorAll('svg').length >= 2 && !!document.querySelector('table.cmp td.best')`));
await go('#/compare?stage=validation');
check('compare with nothing selected asks for a choice', await js(`document.body.textContent.includes('Escolha duas ou mais')`));

await open('#/strategy/H-009');
check('explorer shows the six headline metrics', await js(`document.querySelectorAll('.metrics .metric').length === 6`));
const roiAll = await js(`document.querySelector('.metrics .metric .val').textContent`);
await js(`[...document.querySelectorAll('button')].find((b) => b.textContent.trim().endsWith('BTC')).click()`); await sleep(700);
const roiBtc = await js(`document.querySelector('.metrics .metric .val').textContent`);
check('choosing a pair changes the metrics', roiAll !== roiBtc, `${roiAll} -> ${roiBtc}`);
check('pair selection is in the URL', (await js('location.hash')).includes('pair=BTC'));
check('explorer draws equity, drawdown and distribution charts', await js(`document.querySelectorAll('.sx svg').length >= 3`));
await open('#/strategy/H-016?stage=validation');
check('explorer opens a validation stage', await js(`document.body.textContent.includes('Validação')`));
check('train vs validation table appears when both exist', await js(`document.body.textContent.includes('Exploração × validação') && !!document.querySelector('.sx table')`));

await open('#/backtests');
const runsBefore = await js(`document.querySelectorAll('table[aria-label="Execuções de backtest"] tbody tr').length`);
await js(`(() => { const s = document.querySelector('[data-fkey="sel:bt-h"]'); s.value = 'H-009'; s.dispatchEvent(new Event('change')); })()`); await sleep(400);
const runsAfter = await js(`document.querySelectorAll('table[aria-label="Execuções de backtest"] tbody tr').length`);
check('backtests filter by hypothesis', runsAfter > 0 && runsAfter < runsBefore, `${runsBefore} -> ${runsAfter}`);
await go('#/backtests?origin=real');
check('real-trades tab says there are none', await js(`document.body.textContent.includes('Nenhuma operação real')`));
await go('#/backtests?origin=dryrun');
check('dry-run tab is separate from backtests', await js(`document.body.textContent.includes('Forward test')`));

await open('#/overview');
check('overview shows the featured strategy and quick answers', await js(`document.body.textContent.includes('Em destaque') && document.body.textContent.includes('Respostas rápidas')`));
await open('#/data');
check('system page shows the status tiles', await js(`document.querySelectorAll('.tile').length >= 5`));
await open('#/dryrun');
check('dry-run page shows the fixed label, the freeze status and no profit', await js(`(() => { const t = document.querySelector('#page').textContent; return t.includes('NÃO validada') && t.includes('Congelamento') && t.includes('Esteira de ideias') && !t.includes('Lucro'); })()`));
await open('#/trades');
check('trades page still works', await js(`document.body.textContent.includes('Operações de backtest')`));

await open('#/overview');
await js(`dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))`); await sleep(300);
check('Ctrl+K opens the command palette', await js(`!!document.querySelector('.palette') && !document.querySelector('.palette').hidden`));
await js(`(() => { const i = document.querySelector('.palette input'); i.value = 'H-016'; i.dispatchEvent(new Event('input')); })()`); await sleep(200);
await js(`document.querySelector('.palette input').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))`); await sleep(700);
check('palette navigates to a strategy', (await js('location.hash')).startsWith('#/strategy/H-016'));
await js(`document.querySelector('[data-fkey="density"]').click()`); await sleep(200);
check('density toggle switches to compact', await js(`document.documentElement.dataset.density === 'compact'`));
await js(`document.querySelector('[data-fkey="theme"]').click()`); await sleep(300);
check('theme toggle works', await js(`['light', 'dark'].includes(document.documentElement.dataset.theme)`));
for (const route of ['overview', 'leaderboard', 'strategy/H-005', 'compare?ids=H-005,H-009', 'backtests', 'trades', 'experiments', 'research', 'strategies', 'risk', 'data', 'dryrun']) {
  await go('#/' + route); await sleep(300);
  const bad = await js(`document.querySelector('#page .empty b') && document.querySelector('#page').textContent.includes('Erro ao desenhar')`);
  check(`route /${route} renders without a page error`, !bad);
}
check('no console errors or uncaught exceptions', errors.length === 0, errors.slice(0, 3).join(' | '));

ws.close(); proc.kill();
console.log(failed ? `\n${failed} check(s) failed` : '\nall checks passed');
process.exit(failed ? 1 : 0);
