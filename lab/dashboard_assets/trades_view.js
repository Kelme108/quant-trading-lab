/* ==================== Trades: candles and trades of one backtest run ====================
   Inlined into the page's script by lab.dashboard.render_page, so it
   shares the page helpers (h, card, kpi, badge, dataTable, ...) and the page's CSP nonce.
   Needs the live server: the run's candles and trades come from GET /api/trades?experiment=<id>.
   Everything on this page is a Freqtrade BACKTEST export (simulated); nothing here is a real order. */
const tr = ui.tr = { exp: null, sel: null, range: null, data: {}, loading: {}, error: {}, order: [], refs: null, detail: null, tf: null, day: null };
/* B3 / Substitutos (universes.js): the chart shows ONE session at a time on 1, 5 or 15 minutes (owner 2026-11-16:
   focus on 1 and 5 minutes); the cache key carries the timeframe and the day. Crypto keeps one key per run. */
const trKey = () => (UNI === 'crypto' || !tr.exp ? tr.exp : `${tr.exp}|${tr.tf || ''}|${tr.day || ''}`);
const trSpDay = (ms) => new Date(ms - 3 * 3600000).toISOString().slice(0, 10);   /* Sao Paulo, no DST since 2019 */
const TF_SECONDS = { m: 60, h: 3600, d: 86400, w: 604800 };
const tfSeconds = (tf) => { const m = /^(\d+)([mhdw])$/.exec(String(tf || '')); return m ? Number(m[1]) * TF_SECONDS[m[2]] : 3600; };
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const trRuns = () => experiments().filter((e) => e.artifact_path && e.status === 'completed');
const trPrice = (v) => ok(v) ? sgn(v >= 100 ? nf2.format(v) : new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 4 }).format(v)) : dash;
const trIso = (ms) => new Date(ms).toISOString();
const trDay = (ms) => new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(ms));

function trLoad(id) {
  if (tr.data[id] || tr.loading[id] || tr.error[id]) return;
  tr.loading[id] = true;
  const [exp, tf, day] = String(id).split('|');
  const url = '/api/trades?experiment=' + encodeURIComponent(exp) + (tf ? '&tf=' + encodeURIComponent(tf) : '') + (day ? '&day=' + encodeURIComponent(day) : '');
  fetch(url, { cache: 'no-store' })
    .then(async (r) => { const body = await r.json().catch(() => ({})); if (!r.ok) throw new Error(body.error || 'HTTP ' + r.status); return body; })
    .then((body) => {
      const keys = [id];
      if (body.day) {           /* a session payload: also store it under its canonical key, and adopt its tf and day */
        keys.push(`${exp}|${body.timeframe}|${body.day}`);
        if (tr.exp === exp) { tr.tf = tr.tf || body.timeframe; tr.day = tr.day || body.day; }
      }
      for (const k of keys) tr.data[k] = body;
      tr.order = [...keys, ...tr.order.filter((x) => !keys.includes(x))];
      for (const old of tr.order.slice(8)) delete tr.data[old];
      tr.order = tr.order.slice(0, 8);
    })
    .catch((e) => { tr.error[id] = String(e && e.message ? e.message : e); })
    .finally(() => { tr.loading[id] = false; if (/(^|-)chart$/.test(route.id)) render(); });
}

/* ---------- trade facts: only what the export holds, plus ratios computed from it ---------- */
function trFacts(t) {
  const mfe = t.open_rate && t.max_rate ? (t.max_rate / t.open_rate - 1) * 100 : null;
  const mae = t.open_rate && t.min_rate ? (t.min_rate / t.open_rate - 1) * 100 : null;
  return { ...t, ret: ok(t.profit_ratio) ? t.profit_ratio * 100 : null, mfe, mae, stopPct: t.initial_stop_loss_abs && t.open_rate ? (t.initial_stop_loss_abs / t.open_rate - 1) * 100 : null };
}
function trDetail(t) {
  if (!t) return h('div', { class: 'sub' }, 'Clique em "Ver" numa linha da tabela, ou numa seta do gráfico, para abrir uma operação.');
  const f = trFacts(t), win = ok(f.profit_abs) && f.profit_abs > 0;
  return h('div', null,
    h('div', { class: 'row', style: 'margin-bottom:8px' }, h('b', null, `Operação #${t.n}`), badge(win ? ST.good : ST.bad, win ? 'ganho' : 'perda'), h('span', { class: 'tag' }, 'backtest simulado')),
    h('dl', { class: 'kv' },
      h('dt', null, 'Entrada'), h('dd', null, `${whenSec(trIso(t.open_ts))} a ${trPrice(t.open_rate)}`, t.enter_tag ? [' · ', h('code', null, t.enter_tag)] : null),
      h('dt', null, 'Saída'), h('dd', null, `${whenSec(trIso(t.close_ts))} a ${trPrice(t.close_rate)}`, t.exit_reason ? [' · ', h('code', null, t.exit_reason)] : null),
      h('dt', null, 'Duração'), h('dd', null, ok(t.trade_duration) ? ago(t.trade_duration * 60) : dash),
      h('dt', null, 'Resultado'), h('dd', { class: 'num' }, t.unit ? `${pct(f.ret)} do valor de ${t.unit} (já com os custos do cenário base)` : `${pct(f.ret)} · ${usdt(t.profit_abs)} sobre ${usdt(t.stake_amount)} apostados (já com as taxas do cenário base)`),
      h('dt', null, 'Melhor ponto aberto'), h('dd', { class: 'num' }, `${pct(f.mfe)} (máxima ${trPrice(t.max_rate)})`),
      h('dt', null, 'Pior ponto aberto'), h('dd', { class: 'num' }, `${pct(f.mae)} (mínima ${trPrice(t.min_rate)})`),
      h('dt', null, 'Stop inicial'), h('dd', { class: 'num' }, t.initial_stop_loss_abs ? `${trPrice(t.initial_stop_loss_abs)} (${pct(f.stopPct)})` : dash)));
}

/* ---------- the chart ---------- */
function trSelect(n) {
  const data = tr.data[tr.refs && tr.refs.key ? tr.refs.key : tr.exp] || tr.data[tr.exp], refs = tr.refs;
  tr.sel = n;
  const t = data && data.trades.find((x) => x.n === n);
  if (data && data.day && t && trSpDay(t.open_ts) !== data.day) { tr.day = trSpDay(t.open_ts); render(); return; }  /* another session */
  if (tr.detail) tr.detail.replaceChildren(trDetail(t));
  if (!refs || !t) return;
  refs.lines.forEach((l) => refs.candle.removePriceLine(l)); refs.lines = [];
  const line = (price, title, color) => { if (ok(price)) refs.lines.push(refs.candle.createPriceLine({ price, color, lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title })); };
  line(t.open_rate, 'entrada', cssVar('--info')); line(t.close_rate, 'saída', ok(t.profit_abs) && t.profit_abs > 0 ? cssVar('--good') : cssVar('--bad')); line(t.initial_stop_loss_abs, 'stop', cssVar('--warn'));
  refs.markers.setMarkers(trMarkers(data, n, refs.step));
  const pad = Math.max((t.close_ts - t.open_ts) / 1000, refs.step * 40);
  refs.chart.timeScale().setVisibleRange({ from: Math.floor(t.open_ts / 1000 - pad), to: Math.ceil(t.close_ts / 1000 + pad) });
}
function trMarkers(data, selected, step) {
  const snap = (ms) => Math.floor(ms / 1000 / step) * step, list = [];
  const lo = data.candles.length ? data.candles[0][0] : -Infinity, hi = data.candles.length ? data.candles[data.candles.length - 1][0] + step : Infinity;
  for (const t of data.trades) {
    if (data.day && (t.close_ts / 1000 < lo || t.open_ts / 1000 > hi)) continue;     /* only the session on screen */
    const win = ok(t.profit_abs) && t.profit_abs > 0, on = t.n === selected;
    list.push({ time: snap(t.open_ts), position: 'belowBar', shape: 'arrowUp', color: cssVar('--info'), text: on ? `#${t.n} entrada` : '' });
    list.push({ time: snap(t.close_ts), position: 'aboveBar', shape: 'arrowDown', color: win ? cssVar('--good') : cssVar('--bad'), text: on ? `#${t.n} saída ${pct(trFacts(t).ret)}` : '' });
  }
  return list.sort((a, b) => a.time - b.time);
}
function trDraw(el, legend, data) {
  const LW = window.LightweightCharts;
  if (tr.refs) { if (tr.refs.exp === data.experiment_id) { try { tr.range = tr.refs.chart.timeScale().getVisibleRange(); } catch (e) { /* sem faixa salva */ } } tr.refs.chart.remove(); tr.refs = null; }
  if (!LW) { el.replaceChildren(notAvailable('Gráfico', 'a biblioteca de gráficos não carregou.')); return; }
  const chart = LW.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: cssVar('--panel') }, textColor: cssVar('--ink2'), fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', attributionLogo: true },
    grid: { vertLines: { color: cssVar('--line') }, horzLines: { color: cssVar('--line') } },
    rightPriceScale: { borderColor: cssVar('--line2') }, timeScale: { borderColor: cssVar('--line2'), timeVisible: true, secondsVisible: false, minBarSpacing: 0.01 },
    localization: { locale: 'pt-BR', priceFormatter: (p) => nf2.format(p) },
    crosshair: { mode: LW.CrosshairMode.Normal },
  });
  const candle = chart.addSeries(LW.CandlestickSeries, { upColor: cssVar('--good'), downColor: cssVar('--bad'), wickUpColor: cssVar('--good'), wickDownColor: cssVar('--bad'), borderVisible: false });
  const volume = chart.addSeries(LW.HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: '', color: cssVar('--reg'), lastValueVisible: false, priceLineVisible: false });
  volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
  candle.setData(data.candles.map(([time, open, high, low, close]) => ({ time, open, high, low, close })));
  volume.setData(data.candles.map(([time, , , , , v]) => ({ time, value: v })));
  const step = tfSeconds(data.stats.timeframe);
  const markers = LW.createSeriesMarkers(candle, trMarkers(data, tr.sel, step));
  tr.refs = { exp: data.experiment_id, key: data.day ? `${data.experiment_id}|${data.timeframe}|${data.day}` : data.experiment_id, chart, candle, volume, markers, lines: [], step };
  const byTime = new Map(data.candles.map((c) => [c[0], c]));
  const showBar = (c) => legend.replaceChildren(c ? `${trDay(c[0] * 1000)}   A ${trPrice(c[1])}   Máx ${trPrice(c[2])}   Mín ${trPrice(c[3])}   F ${trPrice(c[4])}   Vol ${num(c[5], nf0)}` : '');
  chart.subscribeCrosshairMove((p) => showBar(p && p.time != null ? byTime.get(p.time) : null));
  chart.subscribeClick((p) => {
    if (!p || p.time == null) return;
    const near = data.trades.find((t) => Math.abs(Math.floor(t.open_ts / 1000 / step) * step - p.time) <= step || Math.abs(Math.floor(t.close_ts / 1000 / step) * step - p.time) <= step);
    if (near) trSelect(near.n);
  });
  const selOnDay = tr.sel != null && (!data.day || data.trades.some((t) => t.n === tr.sel && trSpDay(t.open_ts) === data.day));
  if (selOnDay) trSelect(tr.sel);
  else if (tr.range && !data.day) chart.timeScale().setVisibleRange(tr.range);
  else chart.timeScale().fitContent();
}

/* ---------- page ---------- */
function trStatsU(data) {
  const t = data.trades, n = t.length, wins = t.filter((x) => x.profit_abs > 0).length, sum = t.reduce((a, x) => a + (x.profit_abs || 0), 0);
  const today = t.filter((x) => trSpDay(x.open_ts) === data.day), daySum = today.reduce((a, x) => a + (x.profit_abs || 0), 0), tag = h('span', { class: 'tag' }, 'simulado');
  return h('div', { class: 'kpis', style: 'grid-template-columns:repeat(auto-fit,minmax(min(100%,128px),1fr))' },
    kpi('Operações', num(n), tag), kpi('Taxa de acerto', pct0(n ? wins / n * 100 : null), 'win rate'),
    kpi('Resultado somado', pct(sum), '% do valor de 1 contrato, custo base'), kpi('Dias com operação', num(data.days.length), 'pregões'),
    kpi('Neste pregão', `${today.length} ${plural(today.length, 'operação', 'operações')}`, pct(daySum)));
}
function trControlsU(data) {
  const days = data.days || [], i = days.indexOf(data.day);
  const go = (d) => { if (d) { tr.day = d; tr.sel = null; render(); } };
  return h('div', { class: 'filters' },
    segmented('Tempo gráfico', 'tr-tf', data.timeframe, (data.timeframes || ['1m', '5m', '15m']).map((x) => [x, x.replace('m', ' min')]), (v) => { tr.tf = v; render(); }),
    h('button', { type: 'button', 'data-fkey': 'tr-prev', disabled: i <= 0, onclick: () => go(days[i - 1]) }, '← Pregão anterior'),
    selectBox('Pregão', 'tr-day', data.day, [...days].reverse().map((d) => [d, d.split('-').reverse().join('/')]), (v) => go(v)),
    h('button', { type: 'button', 'data-fkey': 'tr-next', disabled: i < 0 || i >= days.length - 1, onclick: () => go(days[i + 1]) }, 'Próximo pregão →'));
}
function trStats(data) {
  if (data.day) return trStatsU(data);
  const s = data.stats, n = data.trades.length, tag = h('span', { class: 'tag' }, 'simulado');
  return h('div', { class: 'kpis', style: 'grid-template-columns:repeat(auto-fit,minmax(min(100%,128px),1fr))' },
    kpi('Operações', num(s.total_trades), tag), kpi('Taxa de acerto', pct0(ok(s.winrate) ? s.winrate * 100 : null), 'win rate'),
    kpi('Profit factor', ok(s.profit_factor) ? nf2.format(s.profit_factor) : dash, 'ganhos brutos ÷ perdas brutas'), kpi('Sharpe', ok(s.sharpe) ? nf2.format(s.sharpe) : dash, 'calculado pelo Freqtrade'),
    kpi('Queda máxima', pct0(ok(s.max_relative_drawdown) ? s.max_relative_drawdown * 100 : null), 'pico a vale, relativa'), kpi('Expectância', usdt(s.expectancy), 'média por operação'),
    kpi('Lucro líquido', usdt(s.profit_total_abs), n ? `${num(s.starting_balance)} → ${num(s.final_balance, nf2)} USDT` : null));
}
function trTable(data) {
  const rows = data.trades.map((t) => ({ key: t.n, label: '#' + t.n, t, f: trFacts(t) }));
  const tone = (v) => ok(v) ? (v > 0 ? 'pos' : v < 0 ? 'neg' : '') : '';
  const cols = [
    { key: 'n', label: '#', num: true, val: (r) => r.t.n, cell: (r) => h('button', { type: 'button', 'data-fkey': 'tr-see:' + r.t.n, onclick: () => { trSelect(r.t.n); els.page.querySelector('.trchart').scrollIntoView({ block: 'nearest' }); } }, 'Ver ' + r.t.n) },
    { key: 'open', label: 'Entrada', val: (r) => r.t.open_ts, cell: (r) => trDay(r.t.open_ts) },
    { key: 'close', label: 'Saída', val: (r) => r.t.close_ts, cell: (r) => trDay(r.t.close_ts) },
    { key: 'dur', label: 'Duração', num: true, val: (r) => r.t.trade_duration, cell: (r) => ok(r.t.trade_duration) ? ago(r.t.trade_duration * 60) : dash },
    { key: 'tag', label: 'Sinal', val: (r) => r.t.enter_tag, cell: (r) => r.t.enter_tag ? h('code', null, r.t.enter_tag) : dash },
    { key: 'exit', label: 'Motivo de saída', val: (r) => r.t.exit_reason, cell: (r) => r.t.exit_reason ? h('code', null, r.t.exit_reason) : dash },
    { key: 'ret', label: 'Retorno', num: true, val: (r) => r.f.ret, cell: (r) => h('span', { class: tone(r.f.ret) }, pct(r.f.ret)) },
    data.day ? null : { key: 'abs', label: 'Lucro', num: true, val: (r) => r.t.profit_abs, cell: (r) => h('span', { class: tone(r.t.profit_abs) }, usdt(r.t.profit_abs)) },
    data.day ? null : { key: 'mfe', label: 'Melhor ponto', num: true, val: (r) => r.f.mfe, cell: (r) => pct(r.f.mfe) },
    data.day ? null : { key: 'mae', label: 'Pior ponto', num: true, val: (r) => r.f.mae, cell: (r) => pct(r.f.mae) },
  ].filter(Boolean);
  return dataTable({ id: 'tr-trades', cols, rows, sort0: { key: 'n', dir: 1 }, label: 'Operações do backtest' });
}
function pageTrades(r) {
  if (r.arg && r.arg !== tr.exp) { tr.exp = r.arg; tr.sel = null; tr.range = null; tr.tf = null; tr.day = null; }
  if (r.q.sel && tr.selUrl !== r.key + r.q.sel) { tr.selUrl = r.key + r.q.sel; tr.sel = Number(r.q.sel) || null; }
  const runs = trRuns();
  const head = h('div', { class: 'notice info', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'),
    UNI !== 'crypto' ? h('div', null, uxChartNote()) : h('div', null, 'Operações de backtest exportadas pelo Freqtrade, sobre os candles reais da Binance em ', h('code', null, 'user_data/data'), '. É histórico simulado: nenhuma ordem foi enviada a uma corretora. Resultados de dry-run ao vivo aparecem quando um forward test estiver rodando (hoje: ', String(state.forward_test.closed + state.forward_test.open), ' operações).'));
  if (!LIVE) return h('div', null, head, card('Gráfico e operações', null, notAvailable('Gráfico de preço e operações', 'o snapshot estático não carrega candles. Abra o painel com python -m lab.dashboard serve.')));
  if (!runs.length) return h('div', null, head, card('Gráfico e operações', null, emptyState('Nenhum backtest com resultado salvo.', 'Rode um ciclo para gerar experimentos.')));
  if (!tr.exp || !runs.some((e) => e.id === tr.exp)) { const first = runs.find((e) => e.current) || runs[0]; tr.exp = first.id; tr.sel = null; tr.range = null; tr.tf = null; tr.day = null; }
  const run = runs.find((e) => e.id === tr.exp);
  const picker = selectBox('Experimento', 'tr-exp', tr.exp, runs.map((e) => [e.id, `${e.hypothesis_id} · ${short(e.pair)} · ${STAGE[e.split] || e.split}${e.current ? '' : ' (substituída)'} · ${whenShort(e.created_at_utc)}`]), (v) => { location.hash = rxR('chart') + '/' + encodeURIComponent(v); });
  const filters = h('div', { class: 'filters' }, picker, UNI !== 'crypto' ? null : h('a', { href: `#/experiments/${encodeURIComponent(tr.exp)}`, 'data-fkey': 'tr-detail' }, 'Ver decisão dos gates'));
  const key = trKey();
  trLoad(key);
  const data = tr.data[key];
  if (tr.error[key]) return h('div', null, head, card('Gráfico e operações', null, h('div', null, filters, notAvailable('Gráfico e operações', tr.error[tr.exp]), h('div', { class: 'btnrow', style: 'margin-top:8px' }, h('button', { type: 'button', 'data-fkey': 'tr-retry', onclick: () => { delete tr.error[key]; render(); } }, 'Tentar de novo')))));
  if (!data) return h('div', null, head, card('Gráfico e operações', null, h('div', null, filters, loadingState('Carregando candles e operações…'))));
  const legend = h('div', { class: 'sub mono', style: 'min-height:18px;margin:4px 0' });
  const chartEl = h('div', { class: 'trchart', role: 'img', 'aria-label': `Candles de ${data.pair} com as ${data.trades.length} operações do backtest` });
  tr.detail = h('div');
  tr.detail.replaceChildren(trDetail(data.trades.find((x) => x.n === tr.sel)));
  queueMicrotask(() => { if (chartEl.isConnected && data.candles.length) trDraw(chartEl, legend, data); });
  const chartBody = data.candles.length ? h('div', null, legend, chartEl,
    h('div', { class: 'sub', style: 'margin-top:6px' }, 'Setas azuis: entradas. Setas verdes e vermelhas: saídas com ganho e com perda. ', h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'Gráficos por TradingView Lightweight Charts™')))
    : notAvailable('Candles', data.candles_error || 'o arquivo de candles deste par não cobre o período do backtest.');
  return h('div', null, head,
    card(`${data.hypothesis_id} · ${data.pair} · ${STAGE[data.split] || data.split}`, `Backtest de ${data.stats.backtest_start ? data.stats.backtest_start.slice(0, 10) : dash} a ${data.stats.backtest_end ? data.stats.backtest_end.slice(0, 10) : dash} · candles de ${data.stats.timeframe}`, h('div', null, filters, data.day ? trControlsU(data) : null, trStats(data), chartBody), { id: 'sec-trades-chart' }),
    card('Operação selecionada', data.day ? 'Dados do backtest no motor da B3 (resultados em % do valor de 1 contrato)' : 'Dados do export do Freqtrade', tr.detail, { id: 'sec-trade-detail' }),
    card('Operações', 'Ordene pelas colunas; "Ver" leva o gráfico até a operação', data.trades.length ? trTable(data) : emptyState('Este backtest não fez operações.'), { id: 'sec-trades-table' }));
}
pageTrades = guard(pageTrades, 'Gráfico e operações');
