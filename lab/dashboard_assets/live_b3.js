/* ==================== B3: ao vivo na conta REAL da Clear (botões de controle) ====================
   Inlined after demo_b3.js (same script scope: it reuses its db* formatters). Owner, 2026-11-17: "os bots vao abrir as
   ordens e eu vou administrar o risco e ganho pelos botoes". GET /api/real-b3 lists live/config/live-b3-*.json with the
   same fields as the demo plus the per-run control token; the buttons POST /api/control, which only drops a command
   file the robot's own ENGINE executes and journals (the page never talks to the broker). Strings become text nodes. */

const RL = { data: null, at: 0, loading: false, error: null, sig: '', arm: null, armTimer: null, busy: false, msg: null, sel: null, els: {} };
const RL_ACTIONS = {
  close: { label: 'Fechar posição', ask: 'Confirmar: fechar a posição agora?', cls: 'btn', done: 'Pedido de fechamento enviado.' },
  pause: { label: 'Pausar entradas', ask: 'Confirmar: pausar novas entradas?', cls: 'btn', done: 'Pausa enviada: o robô não abre novas posições.' },
  resume: { label: 'Retomar entradas', ask: 'Confirmar: retomar as entradas?', cls: 'btn', done: 'Retomada enviada.' },
  start: { label: 'Ligar robô', ask: 'Confirmar: ligar o robô agora?', cls: 'btn primary', done: 'Robô ligado.' },
  stop: { label: 'Desligar robô', ask: 'Confirmar: fechar a posição e DESLIGAR o robô?', cls: 'btn', done: 'Desligamento enviado: o robô fecha a posição, se houver, e encerra.' },
  close_stop: { label: 'Fechar e parar', ask: 'Confirmar: fechar a posição E pausar o robô?', cls: 'btn primary', done: 'Fechamento e pausa enviados.' },
};
const RL_RESULT = { closed: 'posição fechada', nothing_to_close: 'não havia posição', paused: 'entradas pausadas', resumed: 'entradas retomadas',
  'closed+paused': 'posição fechada e entradas pausadas', 'nothing_to_close+paused': 'sem posição; entradas pausadas', 'close_failed': 'o fechamento falhou: confira o terminal',
  'close_failed+paused': 'o fechamento falhou (confira o terminal); entradas pausadas',
  stopped: 'robô desligado', 'closed+stopped': 'posição fechada e robô desligado', 'nothing_to_close+stopped': 'sem posição; robô desligado' };
const RL_ACT_NAME = { start: 'ligar', stop: 'desligar', close: 'fechar posição', pause: 'pausar entradas', resume: 'retomar entradas', close_stop: 'fechar e parar' };

function rlLoad(force) {
  if (!LIVE || RL.loading || (!force && RL.data && Date.now() - RL.at < 3000)) return;
  RL.loading = true;
  fetch('/api/real-b3', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((d) => { RL.data = d; RL.error = null; RL.at = Date.now(); })
    .catch((e) => { RL.error = String(e && e.message ? e.message : e); RL.at = Date.now(); })
    .finally(() => {
      RL.loading = false;
      if (route.id !== 'b3-live') return;
      const sig = rlSig();
      if (sig !== RL.sig) { RL.sig = sig; render(); } else rlLiveNumbers();
    });
}
if (LIVE) setInterval(() => { if (route.id === 'b3-live') rlLoad(true); }, 3000);
const rlSig = () => JSON.stringify((RL.data && RL.data.items || []).map((i) => [i.id, i.status, i.process_alive, i.off, i.paused, i.command_pending && i.command_pending.action,
  i.last_command && i.last_command.ts, i.killswitch, i.trades && i.trades.length, dbPosition(i) ? dbPosition(i).volume : 0, i.alerts && i.alerts.length])) +
  JSON.stringify(RL.arm) + RL.sel + DB.tf + (RL.msg ? RL.msg.text : '') + RL.busy + (RL.error || '');

function rlDisarm() { if (RL.armTimer) clearTimeout(RL.armTimer); RL.armTimer = null; RL.arm = null; }
function rlClick(it, action) {
  if (RL.busy) return;
  if (!RL.arm || RL.arm.id !== it.id || RL.arm.action !== action) {          /* first click: ask for the second, for 6 seconds */
    rlDisarm();
    RL.arm = { id: it.id, action };
    RL.armTimer = setTimeout(() => { rlDisarm(); if (route.id === 'b3-live') render(); }, 6000);
    RL.msg = null; render(); return;
  }
  rlDisarm(); RL.busy = true; RL.msg = null; render();
  fetch('/api/control', { method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json', 'X-Control-Token': RL.data.control_token },
    body: JSON.stringify({ id: it.id, action }) })
    .then((r) => r.json().then((b) => ({ s: r.status, b })))
    .then(({ s, b }) => {
      RL.msg = s === 202 ? { ok: true, id: it.id, text: RL_ACTIONS[action].done + (action === 'start' ? ' Os primeiros preços aparecem em alguns segundos.' : ' O robô executa no próximo ciclo (até 5 s).') }
        : { ok: false, id: it.id, text: s === 409 ? 'Já existe um comando esperando este robô. Aguarde ele ser executado.' : 'Não enviado (' + (b && b.error ? b.error : 'HTTP ' + s) + ')' + (b && b.detail ? ': ' + b.detail : '.') };
    })
    .catch((e) => { RL.msg = { ok: false, id: it.id, text: 'Não enviado: ' + String(e && e.message ? e.message : e) }; })
    .finally(() => { RL.busy = false; RL.at = 0; rlLoad(true); render(); });
}
function rlButton(it, action, blocked) {
  const a = RL_ACTIONS[action], armed = RL.arm && RL.arm.id === it.id && RL.arm.action === action;
  return h('button', { type: 'button', class: a.cls + (armed ? ' rl-armed' : ''), disabled: blocked || RL.busy ? '' : null, 'data-fkey': `rl:${it.id}:${action}`,
    onclick: () => rlClick(it, action) }, armed ? a.ask : a.label);
}
function rlControls(it) {
  const pos = dbPosition(it), pend = it.command_pending, on = !!it.process_alive;
  const lc = it.last_command;
  const why = it.placeholder ? 'Nenhum robô ligado ainda: os botões ativam quando o primeiro robô começar a rodar.'
    : !on ? 'O robô está desligado: use "Ligar robô". Os outros botões só funcionam com ele ligado.'
    : pend ? `Aguardando o robô executar: ${RL_ACT_NAME[pend.action] || pend.action}.` : null;
  const blocked = !!why;
  return h('div', { class: 'rx-stack' },
    h('div', { class: 'rl-bar' },
      on ? rlButton(it, 'stop', it.placeholder || !!pend) : rlButton(it, 'start', !!it.placeholder),
      rlButton(it, 'close', blocked), rlButton(it, it.paused ? 'resume' : 'pause', blocked), rlButton(it, 'close_stop', blocked)),
    h('p', { class: 'sub rl-state', 'aria-live': 'polite' },
      h('b', null, on ? 'Robô ligado. ' : 'Robô desligado. '),
      on ? h('b', null, it.paused ? 'Entradas pausadas. ' : 'Entradas liberadas. ') : '',
      pos ? 'Há posição aberta. ' : 'Sem posição aberta. ',
      why ? h('span', { class: 'warn' }, why + ' ') : '',
      lc ? `Último comando (${dbDayTime(lc.ts)}): ${RL_ACT_NAME[lc.action] || lc.action}, ${RL_RESULT[lc.result] || lc.result}.` : 'Nenhum comando enviado ainda.'),
    RL.msg && RL.msg.id === it.id ? h('div', { class: 'notice ' + (RL.msg.ok ? 'info' : ''), role: 'status' }, RL.msg.text) : null);
}
function rlLiveNumbers() {
  for (const it of (RL.data && RL.data.items) || []) {
    const e = RL.els[it.id];
    if (!e) continue;
    const pos = dbPosition(it), last = dbLast(it);
    e.last.textContent = dbPx(it, last);
    e.open.replaceChildren(pos && ok(pos.open_result_brl) ? h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)) : dash);
    e.upd.textContent = it.feed ? 'preço lido às ' + dbSecs(it.feed.updated_at) : '';
  }
  dbLive(RL.data);                       /* moves the forming candle of the selected robot's chart */
}
function rlItem(it, withChart) {
  if (it.error) return card(it.id, null, notAvailable('Robô real', it.error));
  const pos = dbPosition(it), last = dbLast(it), st = !it.process_alive && !it.placeholder ? { icon: '○', cls: 'info', label: 'desligado' } : (DB_STATUS[it.status] || DB_STATUS['sem dados']);
  const e = RL.els[it.id] = { last: h('span', null, dbPx(it, last)), upd: h('span', null, it.feed ? 'preço lido às ' + dbSecs(it.feed.updated_at) : ''),
    open: h('span', null, pos && ok(pos.open_result_brl) ? h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)) : dash) };
  const kpis = h('div', { class: 'kpis' },
    kpi('Robô', h('span', null, badge(st), it.paused ? [' ', badge({ icon: '❚❚', cls: 'warn', label: 'pausado' })] : ''), DB_PHASE[it.phase] || '', e.upd),
    kpi('Último preço', e.last, it.feed && ok(it.feed.bid) ? `compra ${dbPx(it, it.feed.bid)} · venda ${dbPx(it, it.feed.ask)}` : it.symbol),
    kpi('Posição agora', pos ? (pos.volume > 0 ? 'Comprado ' : 'Vendido ') + nf0.format(Math.abs(pos.volume)) : 'Zerado',
      pos ? h('span', null, `entrada ${dbPx(it, pos.entry_price)}, stop ${dbPx(it, pos.stop)} · resultado aberto `, e.open) : 'sem posição aberta'),
    kpi('Hoje', nf0.format(it.trades_today.length) + ' ' + plural(it.trades_today.length, 'operação', 'operações'),
      dbBrl(it.trades_today.reduce((s, t) => s + t.pnl_brl, 0)) + ' fechado'),
    kpi('Resultado fechado', h('span', { class: tone(it.pnl_total_brl) }, dbBrl(it.pnl_total_brl)), `${dbPts(it.points_total)}, ${nf0.format(it.volume || 1)} contrato`));
  const table = it.trades.length ? dataTable({ id: 'rl-trades-' + it.id, label: 'Operações reais', rows: it.trades.map((t, i) => ({ ...t, key: String(i) })), sort0: { key: 'in', dir: -1 },
    cols: [{ key: 'in', label: 'Entrada', val: (t) => t.entry_time, cell: (t) => dbDayTime(t.entry_time) },
      { key: 'side', label: 'Lado', val: (t) => t.side, cell: (t) => t.side },
      { key: 'pin', label: 'Preço de entrada', num: true, val: (t) => t.entry_price, cell: (t) => dbPx(it, t.entry_price) },
      { key: 'pout', label: 'Preço de saída', num: true, val: (t) => t.exit_price, cell: (t) => dbPx(it, t.exit_price) },
      { key: 'why', label: 'Motivo da saída', val: (t) => t.exit_reason, cell: (t) => t.exit_reason === 'manual_close' ? 'fechado por você' : dbReason(t.exit_reason) },
      { key: 'brl', label: 'Resultado', num: true, val: (t) => t.pnl_brl, cell: (t) => h('span', { class: tone(t.pnl_brl) }, dbBrl(t.pnl_brl)) }] })
    : emptyState('Nenhuma operação ainda.', '');
  const tfs = segmented('Tempo gráfico', 'rl-tf', DB.tf, [['1m', '1 min'], ['5m', '5 min'], ['15m', '15 min']], (v) => { DB.tf = v; render(); });
  const chartEl = h('div', { class: 'trchart', role: 'img', 'aria-label': `Candles de ${DB.tf.replace('m', ' minutos')} do ${it.symbol} hoje, ao vivo, com as entradas e saídas` });
  const hasBars = dbCandles(it, DB.tf).length > 0;
  if (withChart && hasBars) queueMicrotask(() => { if (chartEl.isConnected) dbDraw(chartEl, it, DB.tf); });
  const chartBlock = !withChart ? h('button', { type: 'button', class: 'btn', 'data-fkey': 'rl-sel:' + it.id, onclick: () => { RL.sel = it.id; render(); } }, 'Ver o gráfico deste robô')
    : hasBars ? h('div', null, h('div', { class: 'filters' }, tfs), chartEl, h('div', { class: 'sub', style: 'margin-top:6px' }, 'Candles do pregão de hoje, horário de Brasília, atualizados a cada poucos segundos (o último está em formação). Linha amarela: fechamento de ontem; azul: entrada; vermelha: stop. Setas: entradas; círculos: saídas com o resultado. ',
      h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'Gráficos por TradingView Lightweight Charts™')))
      : loadingState('O gráfico aparece quando o robô gravar os primeiros candles.');
  const alerts = it.alerts.length ? h('ul', { class: 'sub' }, it.alerts.map((a) => h('li', null, dbDayTime(a.ts) + ': ' + a.message))) : null;
  return h('div', { class: 'rx-stack' },
    card(it.placeholder ? 'Painel de controle (aguardando o primeiro robô)' : `${it.rule || 'Robô'} no ${it.symbol} (${dbName(it)}), ${it.mode === 'live' ? 'conta REAL' : 'conta DEMO da Clear'}`,
      'Os botões não falam com a corretora: eles pedem ao robô, que fecha pela própria rotina e registra no diário.',
      h('div', { class: 'rx-stack' }, kpis, rlControls(it), chartBlock,
        it.killswitch ? h('div', { class: 'notice warn', role: 'note' }, h('b', null, 'Kill switch ligado: '), 'o robô zera e não abre nada até o arquivo ser apagado.') : null,
        alerts ? h('div', null, h('b', null, 'Avisos do robô'), alerts) : null)),
    card('Operações', 'Resultados em reais.', table));
}
function pageRealB3() {
  dbDrop();
  RL.els = {};
  const head = rxHeader('B3: WIN e WDO', 'Ao vivo na conta real da Clear',
    'Os robôs da seção ao vivo e os botões para você administrar: ligar e desligar o robô, fechar a posição, pausar as entradas ou fechar e parar. Nada liga sozinho: só quando você clica em Ligar.');
  const anyReal = ((RL.data && RL.data.items) || []).some((i) => i.mode === 'live');
  const warn = anyReal ? h('div', { class: 'notice warn rl-real', role: 'note' }, h('b', null, 'CONTA REAL. '), 'Cada clique pede uma segunda confirmação. Ordens e perdas aqui são de verdade.')
    : h('div', { class: 'notice info', role: 'note' }, h('b', null, 'Hoje estes robôs operam na conta DEMO da Clear. '), 'A conta real ainda não está conectada: é um passo à parte (credenciais, limites de risco e a liberação do robô). Cada clique pede uma segunda confirmação.');
  if (!LIVE) return h('div', { class: 'rx rx-stack' }, head, card('Ao vivo', null, notAvailable('Conta real', 'o snapshot estático não controla robôs. Abra o painel com python -m lab.dashboard serve.')));
  rlLoad(false);
  if (!RL.data) return h('div', { class: 'rx rx-stack' }, head, warn, RL.error ? emptyState('Não foi possível ler os robôs reais.', RL.error) : loadingState('Lendo os robôs reais…'));
  const items = (RL.data.items || []).slice().sort((a, b) => String(a.id).localeCompare(String(b.id)));
  if (!items.length) {                      /* the screen is ready before the first robot: same layout, nothing running */
    const demo = { id: 'aguardando', placeholder: true, rule: null, market: 'WIN', symbol: 'WINZ26', status: 'sem dados', phase: 'unknown', paused: false, trades: [], trades_today: [],
      pnl_total_brl: 0, points_total: 0, volume: 1, alerts: [], feed: null, snapshot: null, killswitch: false, command_pending: null, last_command: null, risk: {} };
    return h('div', { class: 'rx rx-stack' }, head, warn, rlItem(demo, true),
      card('Para ligar o primeiro robô', 'Nada aqui é ligado por esta página. Quando você escolher o robô:',
        h('ol', null,
          h('li', null, 'Credenciais da conta real da Clear em live/.env (você mesmo digita; não passam pelo chat).'),
          h('li', null, 'Um arquivo live/config/live-b3-<nome>.json com a regra, o contrato, journal e magic próprios e os limites de risco (perda por dia e por semana, contratos, stop obrigatório).'),
          h('li', null, 'O robô entra neste painel sozinho, com preço, posição, gráfico, operações e os botões ativos.'))));
  }
  if (!RL.sel || !items.some((i) => i.id === RL.sel)) RL.sel = items[0].id;
  return h('div', { class: 'rx rx-stack' }, head, warn, ...items.map((i) => rlItem(i, i.id === RL.sel)));
}
(() => {
  const st = document.createElement('style');
  st.textContent = '.rl-bar{display:flex;flex-wrap:wrap;gap:10px}.rl-bar .btn[disabled]{opacity:.45;cursor:not-allowed}'
    + '.rl-armed{outline:2px solid var(--bad);outline-offset:2px}.rl-real{border-color:var(--bad);background:var(--bad-bg)}';
  document.head.append(st);
})();
