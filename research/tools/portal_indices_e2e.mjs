// End-to-end check of the Índices (WIN/WDO) pages in a real headless Chrome or Edge, over the DevTools protocol
// (Node >= 22, no packages). Same harness as research/tools/portal_e2e.mjs.
//   node research/tools/portal_indices_e2e.mjs [http://127.0.0.1:8765]
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

const api = await (await fetch(`${BASE}/api/indices`)).json();
const t0 = Date.now(); const raw = await (await fetch(`${BASE}/api/indices`)).text(); const ms = Date.now() - t0;
check('/api/indices answers fast and small (cached)', ms < 1000 && raw.length < 1_000_000, `${ms} ms, ${Math.round(raw.length / 1024)} KB`);

await open('#/indices');
check('menu has the Índices group with 4 pages', await js(`['indices','indices-placar','indices-ciclos','indices-mercados'].every((r) => !!document.querySelector('a.nav[data-route="' + r + '"]'))`));
check('overview loads the data', await loaded());
const ov = await text();
check('overview opens with the conclusion sentence', /regras testadas em \d+ combinações/.test(ov), ov.slice(0, 160));
check('overview shows the funnel and the agent program', ov.includes('Funil') && ov.includes('Programa de agentes') && ov.includes('Regras nesta semana'));
check('overview numbers match the API', ov.includes(`${api.summary.pairs_explored}`) && ov.includes(`${api.summary.rules} regras testadas`));

await go('#/indices-placar'); await loaded();
const nRows = await js(`document.querySelectorAll('table[aria-label="Placar regra × mercado"] tbody tr:not(.sub)').length`);
check('board lists every rule x market pair', nRows === api.board.length, `${nRows} rows vs ${api.board.length}`);
check('board draws the scatter with the 3x line', await js(`[...document.querySelectorAll('#page svg text')].some((t) => t.textContent.includes('3x o custo'))`));
await js(`(() => { const s = document.querySelector('[data-fkey="sel:ix-mkt"]'); s.value = 'USTEC'; s.dispatchEvent(new Event('change')); })()`); await sleep(400);
const ustec = await js(`[...document.querySelectorAll('table[aria-label="Placar regra × mercado"] tbody tr:not(.sub)')].map((r) => r.dataset.key)`);
check('market filter narrows to USTEC', ustec.length > 0 && ustec.every((k) => k.endsWith('-USTEC')), ustec.slice(0, 4).join(','));
await js(`document.querySelector('[data-fkey="th:ix-board:nb"]').click()`); await sleep(300);
check('sorting by net return works', await js(`(() => { const v = [...document.querySelectorAll('table[aria-label="Placar regra × mercado"] tbody tr:not(.sub) td[data-label="Líquido base"]')].map((e) => parseFloat(e.textContent.replace('−', '-').replace('%', '').replace(',', '.'))).filter((x) => !isNaN(x)); return v.every((x, i) => i === 0 || v[i - 1] <= x) || v.every((x, i) => i === 0 || v[i - 1] >= x); })()`));
await js(`document.querySelector('[data-fkey^="chev:ix-board:"]').click()`); await sleep(300);
check('opening a row shows why it failed', await js(`!!document.querySelector('table[aria-label="Placar regra × mercado"] tr.sub')`));

await open('#/indices-regra/P-003'); await loaded();
const p3 = await text();
check('rule page P-003 shows the idea, the sheet and the reads', p3.includes('A ideia') && p3.includes('Ficha') && p3.includes('USTEC · Teste final'));
check('rule page shows the four cost scenarios', p3.includes('Otimista') && p3.includes('Estresse'));

const agent = api.rules.find((r) => r.origin === 'agent' && r.reads.length);
if (agent) {
  await open('#/indices-regra/' + agent.id); await loaded();
  const pa = await text();
  check(`agent rule ${agent.id} shows the mechanism and the registration proof`, pa.includes('Mecanismo') && pa.includes('registrada antes do teste'));
}
const withTrades = api.rules.find((r) => r.reads.some((x) => x.trades_file));
if (withTrades) {
  await open('#/indices-regra/' + withTrades.id); await loaded();
  await js(`[...document.querySelectorAll('details')].filter((x) => x.querySelector('summary').textContent.includes('curva de capital')).forEach((d) => { d.open = true; })`);
  await sleep(500);
  const clicked = await js(`(() => { const b = [...document.querySelectorAll('button')].find((x) => x.textContent.startsWith('Carregar as operações')); if (!b) return false; b.click(); return true; })()`);
  check(`${withTrades.id} offers its trade list`, clicked);
  if (clicked) {
    check('trade list loads and draws the equity curve', await waitFor(`document.querySelectorAll('svg[aria-label="Curva de capital, custo base"]').length > 0`, 20000));
    check('entry hour table appears', (await text()).includes('Hora de entrada'));
  }
} else console.log('SKIP  no read has a trade list yet');
await open('#/indices-regra/P-999'); await loaded();
check('unknown rule says so', (await text()).includes('Regra não encontrada'));

await open('#/indices-ciclos'); await loaded();
const cy = await text();
check('cycles page lists cycles with their cost', cy.includes('Cada ciclo') && /US\$ \d/.test(cy));
check('the P-010 usage-limit error is visible', !api.rules.some((r) => r.id === 'P-010') || cy.includes('P-010'));

await open('#/indices-mercados'); await loaded();
const mk = await text();
check('markets page shows costs, scope, moves, events and ticks', ['Mercados', 'No escopo', 'Tamanho do movimento', 'Eventos com hora marcada', 'Fidelidade em ticks'].every((s) => mk.includes(s)));

await open('#/overview'); await waitFor(`document.querySelector('#page').textContent.includes('Day trade em índices')`, 60000);
check('home page has the Índices card', (await text()).includes('Day trade em índices (WIN/WDO)'));

await js(`dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))`); await sleep(300);
await js(`(() => { const i = document.querySelector('.palette input'); i.value = 'Placar'; i.dispatchEvent(new Event('input')); })()`); await sleep(200);
await js(`document.querySelector('.palette input').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))`); await sleep(600);
check('palette finds the Índices board', (await js('location.hash')).startsWith('#/indices-placar'));

await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
for (const r of ['indices', 'indices-placar', 'indices-regra/P-003', 'indices-ciclos', 'indices-mercados']) {
  await go('#/' + r); await loaded(); await sleep(300);
  const bad = await js(`document.querySelector('#page').textContent.includes('Erro ao desenhar')`);
  const over = await js(`document.documentElement.scrollWidth - innerWidth`);
  check(`/${r} renders at phone width without horizontal scroll`, !bad && over <= 1, `overflow ${over}px`);
}
check('no console errors or uncaught exceptions', errors.length === 0, errors.slice(0, 3).join(' | '));

ws.close(); proc.kill();
console.log(failed ? `\n${failed} check(s) failed` : '\nall checks passed');
process.exit(failed ? 1 : 0);
