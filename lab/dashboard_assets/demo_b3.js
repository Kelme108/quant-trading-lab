/* ==================== B3: demonstração na conta DEMO da Clear ====================
   Inlined into the page's script by lab.dashboard.render_page. Strings only become text nodes.
   Owner, 2026-11-16: "quero apenas demonstração de como está se portando no demo". The data comes from GET /api/demo-b3
   (lab/demo_b3.py): the engine's snapshot (today's 5-minute bars, position, last decision), its journal (fills, vetoes,
   alerts) and what the research already decided about the same rule. A demonstration is NOT evidence. */

const DB = { data: null, at: 0, loading: false, error: null, sig: '', refs: [] };
function dbLoad(force) {
  if (!LIVE || DB.loading || (!force && DB.data && Date.now() - DB.at < 15000)) return;
  DB.loading = true;
  fetch('/api/demo-b3', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((d) => { DB.data = d; DB.error = null; DB.at = Date.now(); })
    .catch((e) => { DB.error = String(e && e.message ? e.message : e); DB.at = Date.now(); })
    .finally(() => {
      DB.loading = false;
      if (route.id !== 'b3-demo') return;
      const sig = JSON.stringify((DB.data && DB.data.items || []).map((i) => [i.last_event, i.snapshot && i.snapshot.updated_at, i.status])) + DB.error;
      if (sig !== DB.sig) { DB.sig = sig; render(); }
    });
}
if (LIVE) setInterval(() => { if (route.id === 'b3-demo') dbLoad(true); }, 15000);

const dbBrl = (v) => ok(v) ? (v < 0 ? MINUS : v > 0 ? '+' : '') + 'R$ ' + nf2.format(Math.abs(v)) : dash;
const dbPts = (v) => ok(v) ? (v < 0 ? MINUS : v > 0 ? '+' : '') + nf0.format(Math.abs(v)) + ' pts' : dash;
const dbTime = (iso) => iso ? new Date(String(iso).replace(/(\.\d{3})\d+/, '$1')).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const dbDayTime = (iso) => iso ? new Date(String(iso).replace(/(\.\d{3})\d+/, '$1')).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const DB_STATUS = { rodando: { icon: '●', cls: 'good', label: 'rodando' }, parado: { icon: '!', cls: 'bad', label: 'parado' },
  'aguardando o próximo candle': { icon: '…', cls: 'info', label: 'aguardando o próximo candle' }, 'sem dados': { icon: '?', cls: 'warn', label: 'sem dados' } };
const DB_PHASE = { closed: 'mercado fechado', no_entry: 'pregão aberto, fora da janela de entrada', entry: 'janela de entrada aberta', flatten: 'zerando antes do fechamento', unknown: 'sem pregão hoje' };
const DB_REASON = { end_of_day_flatten: 'zeragem do fim do dia', killswitch: 'kill switch', loss_limit: 'limite de perda', stop_loss: 'stop', day_up_so_far: 'dia em alta até aqui', day_down_so_far: 'dia em baixa até aqui' };
const dbReason = (r) => { const s = String(r || ''); if (s.startsWith('server:')) return 'stop ou saída no servidor'; return DB_REASON[s] || s || dash; };

function dbRuleText(it) {
  if (it.rule === 'P-004') return 'P-004 (momento do resto do dia): 30 minutos antes do fechamento, compra se o WIN está acima do fechamento de ontem e vende se está abaixo; stop a 1% e zera 5 minutos antes do fechamento. Uma operação por dia, no máximo.';
  return `${it.rule} em ${it.market}.`;
}

function dbDraw(el, it) {
  const LW = window.LightweightCharts, s = it.snapshot;
  if (!LW) { el.replaceChildren(notAvailable('Gráfico', 'a biblioteca de gráficos não carregou.')); return; }
  const chart = LW.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: cssVar('--panel') }, textColor: cssVar('--ink2'), fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', attributionLogo: true },
    grid: { vertLines: { color: cssVar('--line') }, horzLines: { color: cssVar('--line') } },
    rightPriceScale: { borderColor: cssVar('--line2') }, timeScale: { borderColor: cssVar('--line2'), timeVisible: true, secondsVisible: false },
    localization: { locale: 'pt-BR', priceFormatter: (p) => nf0.format(p), timeFormatter: (t) => new Date(t * 1000).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) },
    crosshair: { mode: LW.CrosshairMode.Normal },
  });
  const sp = (t) => t - 3 * 3600;      /* the chart's axis shows Sao Paulo time (UTC-3, no DST since 2019) */
  const candle = chart.addSeries(LW.CandlestickSeries, { upColor: cssVar('--good'), downColor: cssVar('--bad'), wickUpColor: cssVar('--good'), wickDownColor: cssVar('--bad'), borderVisible: false });
  candle.setData(s.bars.map(([t, o, hi, lo, c]) => ({ time: sp(t), open: o, high: hi, low: lo, close: c })));
  if (ok(s.prev_close)) candle.createPriceLine({ price: s.prev_close, color: cssVar('--warn'), lineStyle: 2, lineWidth: 1, axisLabelVisible: true, title: 'fechamento de ontem' });
  if (s.position && ok(s.position.stop)) candle.createPriceLine({ price: s.position.stop, color: cssVar('--bad'), lineStyle: 0, lineWidth: 1, axisLabelVisible: true, title: 'stop' });
  if (s.position && ok(s.position.entry_price)) candle.createPriceLine({ price: s.position.entry_price, color: cssVar('--info'), lineStyle: 0, lineWidth: 1, axisLabelVisible: true, title: 'entrada' });
  const step = (s.timeframe_min || 5) * 60, snap = (iso) => sp(Math.floor(new Date(String(iso).replace(/(\.\d{3})\d+/, '$1')).getTime() / 1000 / step) * step);
  const day = s.day, marks = [];
  for (const t of it.trades) {
    if (!String(t.entry_time).startsWith(day) && !String(t.exit_time).startsWith(day)) continue;
    const buy = t.side === 'compra';
    marks.push({ time: snap(t.entry_time), position: buy ? 'belowBar' : 'aboveBar', shape: buy ? 'arrowUp' : 'arrowDown', color: cssVar('--info'), text: buy ? 'compra' : 'venda' });
    marks.push({ time: snap(t.exit_time), position: buy ? 'aboveBar' : 'belowBar', shape: 'circle', color: t.pnl_brl > 0 ? cssVar('--good') : cssVar('--bad'), text: 'saída ' + dbBrl(t.pnl_brl) });
  }
  if (it.open_entry) { const buy = it.open_entry.side === 'buy'; marks.push({ time: snap(it.open_entry.fill_time || it.open_entry.ts), position: buy ? 'belowBar' : 'aboveBar', shape: buy ? 'arrowUp' : 'arrowDown', color: cssVar('--info'), text: (buy ? 'compra' : 'venda') + ' (aberta)' }); }
  LW.createSeriesMarkers(candle, marks.sort((a, b) => a.time - b.time));
  chart.timeScale().fitContent();
  DB.refs.push(chart);
}

function dbItem(it) {
  if (it.error) return card(it.id, null, notAvailable('Demonstração', it.error));
  const s = it.snapshot, st = DB_STATUS[it.status] || DB_STATUS['sem dados'], pos = s && s.position;
  const ind = s && s.indicators ? s.indicators : {}, ls = s && s.last_signal;
  const dayMove = s && ok(s.prev_close) && s.bars.length ? (s.bars[s.bars.length - 1][4] / s.prev_close - 1) * 100 : null;
  const val = it.research.find((r) => r.split === 'validation'), exp = it.research.find((r) => r.split === 'exploration');
  const decPt = { passed: 'passou', rejected: 'reprovou', inconclusive: 'inconclusiva' };
  const kpis = h('div', { class: 'kpis' },
    kpi('Robô', badge(st), DB_PHASE[it.phase] || '', s ? 'último candle às ' + dbTime(new Date(s.last_signal.bar * 1000 + (s.timeframe_min || 5) * 60000).toISOString()) : ''),
    kpi('Posição agora', pos ? (pos.volume > 0 ? 'Comprado ' : 'Vendido ') + nf0.format(Math.abs(pos.volume)) : 'Zerado', pos ? `entrada ${nf0.format(pos.entry_price)}, stop ${ok(pos.stop) ? nf0.format(pos.stop) : dash}` : it.symbol),
    kpi('Hoje no WIN', ok(dayMove) ? signedSpan(dayMove, 2) : dash, s && ok(s.prev_close) ? `contra o fechamento de ontem (${nf0.format(s.prev_close)})` : ''),
    kpi('Operações da demonstração', nf0.format(it.trades.length), `${nf0.format(it.wins)} com ganho; hoje ${nf0.format(it.trades_today.length)}`),
    kpi('Resultado somado', h('span', { class: tone(it.pnl_total_brl) }, dbBrl(it.pnl_total_brl)), `${dbPts(it.points_total)}, ${nf0.format(it.volume || 1)} contrato, conta demo`));
  const chartEl = h('div', { class: 'trchart', role: 'img', 'aria-label': `Candles de 5 minutos do ${it.symbol} hoje, com as entradas e saídas da demonstração` });
  if (s && s.bars.length) queueMicrotask(() => { if (chartEl.isConnected) dbDraw(chartEl, it); });
  const decision = ls ? h('p', { class: 'sub' }, `Última decisão (candle das ${dbTime(new Date(ls.bar * 1000).toISOString())}): `,
    h('b', null, ls.action === 'hold' ? 'aguardar' : ls.action === 'enter' ? 'comprar' : ls.action === 'enter_short' ? 'vender' : 'sair'),
    ok(ind.rod_ret) ? `; variação desde o fechamento de ontem ${nf2.format(ind.rod_ret * 100).replace('-', MINUS)}%` : '',
    it.rule === 'P-004' && s.session ? `. A regra decide no candle que fecha às ${dbTime(new Date(new Date(s.session.close).getTime() - 30 * 60000).toISOString())} e zera às ${dbTime(s.session.flatten_at)}.` : '.') : null;
  const table = it.trades.length ? dataTable({ id: 'db-trades-' + it.id, label: 'Operações da demonstração', rows: it.trades.map((t, i) => ({ ...t, key: String(i) })).reverse(), sort0: { key: 'in', dir: -1 },
    cols: [{ key: 'in', label: 'Entrada', val: (t) => t.entry_time, cell: (t) => dbDayTime(t.entry_time) },
      { key: 'side', label: 'Lado', val: (t) => t.side, cell: (t) => t.side },
      { key: 'pin', label: 'Preço de entrada', num: true, val: (t) => t.entry_price, cell: (t) => nf0.format(t.entry_price) },
      { key: 'out', label: 'Saída', val: (t) => t.exit_time, cell: (t) => dbTime(t.exit_time) },
      { key: 'pout', label: 'Preço de saída', num: true, val: (t) => t.exit_price, cell: (t) => nf0.format(t.exit_price) },
      { key: 'why', label: 'Motivo da saída', val: (t) => t.exit_reason, cell: (t) => dbReason(t.exit_reason) },
      { key: 'pts', label: 'Pontos', num: true, val: (t) => t.points, cell: (t) => h('span', { class: tone(t.points) }, dbPts(t.points)) },
      { key: 'brl', label: 'Resultado', num: true, val: (t) => t.pnl_brl, cell: (t) => h('span', { class: tone(t.pnl_brl) }, dbBrl(t.pnl_brl)) }] })
    : emptyState('Nenhuma operação ainda.', it.rule === 'P-004' ? 'A P-004 opera no máximo uma vez por dia, 30 minutos antes do fechamento.' : '');
  const alerts = it.alerts.length || it.vetoes.length ? h('ul', { class: 'sub' },
    it.alerts.map((a) => h('li', null, dbDayTime(a.ts) + ': ' + a.message)),
    it.vetoes.map((v) => h('li', null, dbDayTime(v.ts) + ': ordem barrada pelo controle de risco (' + (v.reasons || []).join(', ') + ')'))) : null;
  return h('div', { class: 'rx-stack' },
    card(`${it.rule} no ${it.symbol} (${it.timeframe_min} min)`, dbRuleText(it), h('div', { class: 'rx-stack' }, kpis, decision,
      s && s.bars.length ? h('div', null, chartEl, h('div', { class: 'sub', style: 'margin-top:6px' }, 'Candles de 5 minutos do pregão de hoje, horário de Brasília. Linha amarela: fechamento de ontem. Setas: entradas; círculos: saídas. ', h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'Gráficos por TradingView Lightweight Charts™')))
        : loadingState('O gráfico aparece depois do primeiro candle fechado com o robô ligado.'),
      it.killswitch ? h('div', { class: 'notice warn', role: 'note' }, h('b', null, 'Kill switch ligado: '), 'o arquivo live/STOP existe; o robô zera e não abre nada até ele ser apagado.') : null)),
    card('Operações', 'Preços e resultados da conta demo da Clear, em reais, já com as taxas que ela cobrar.', table),
    card('O que a pesquisa já disse desta regra', 'A demonstração não muda nada disto: ela não entra nos critérios nem conta como teste.',
      h('div', { class: 'rx-stack' }, h('ul', null,
        h('li', null, 'Exploração (2021-11 a 2024-06): ', h('b', null, exp ? decPt[exp.decision] || exp.decision : 'não lida'), '.'),
        h('li', null, 'Validação (2024-07 a 2025-09): ', h('b', null, val ? decPt[val.decision] || val.decision : 'não lida'), val && val.decision !== 'passed' ? ', por isso ela não é candidata a dinheiro real.' : '.'),
        h('li', null, `Mesmo código da pesquisa (hash ${s ? s.strategy_hash : dash}). Limites desta demo: ${nf0.format(it.risk.max_contracts_per_symbol || 1)} contrato, perda máxima de R$ ${nf0.format(it.risk.max_daily_loss || 0)} no dia e R$ ${nf0.format(it.risk.max_weekly_loss || 0)} na semana.`)),
        alerts ? h('div', null, h('b', null, 'Avisos do robô'), alerts) : null)));
}

function pageDemoB3() {
  for (const c of DB.refs) { try { c.remove(); } catch (e) { /* já removido */ } }
  DB.refs = [];
  const head = rxHeader('B3: WIN e WDO', 'Demonstração na conta demo da Clear', 'O robô roda a regra da pesquisa, sem mudar nada, com preço real e dinheiro fictício. Serve para ver como ela se comporta ao vivo. Não é evidência de lucro: a pesquisa continua validando regras à parte, e só uma aprovada na validação e no teste final pode ir para dinheiro real.');
  if (!LIVE) return h('div', { class: 'rx rx-stack' }, head, card('Demonstração', null, notAvailable('Demonstração ao vivo', 'o snapshot estático não lê o robô. Abra o painel com python -m lab.dashboard serve.')));
  dbLoad(false);
  if (!DB.data) return h('div', { class: 'rx rx-stack' }, head, DB.error ? emptyState('Não foi possível ler a demonstração.', DB.error) : loadingState('Lendo o robô da demonstração…'));
  const items = DB.data.items || [];
  return h('div', { class: 'rx rx-stack' }, head, items.length ? items.map(dbItem) : emptyState('Nenhuma demonstração configurada.', 'Os arquivos ficam em live/config/demo-b3-*.json.'));
}
