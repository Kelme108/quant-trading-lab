/* ==================== Dry-run: what each bot did (trades, profit) and the live chart per asset ====================
   Data: GET /api/dryrun (bots) and GET /api/live?pair=&tf= (candles from Binance public data + every bot's trades).
   Everything here is dry-run: virtual wallet, real prices, no order is ever sent. Read-only. */
const dl = { bots: null, botsErr: null, botsAt: 0, loadingBots: false, live: null, liveErr: null, loadingLive: false, pair: 'BTC/USDT', tf: '1h', hide: {}, refs: null, open: {}, range: null };
const DL_COLORS = ['#3b82f6', '#f59e0b', '#a855f7', '#14b8a6', '#ef4444', '#84cc16', '#ec4899', '#06b6d4'];
const dlColor = (id) => { const ids = dl.live ? dl.live.bots.map((b) => b.id) : []; const i = ids.indexOf(id); return DL_COLORS[(i < 0 ? 0 : i) % DL_COLORS.length]; };
const DL_VERDICT = { collecting: ['warn', 'Coletando'], approved_for_review: ['good', 'Aprovada para análise'], rejected: ['bad', 'Reprovada'] };
const dlPct = (v, d = 2) => (ok(v) ? (v > 0 ? '+' : '') + v.toFixed(d).replace('.', ',').replace('-', MINUS) + '%' : dash);
const dlWhen = (s) => (s ? s.replace('T', ' ') : dash);
const dlTone = (v) => (ok(v) ? (v > 0 ? 'pos' : v < 0 ? 'neg' : '') : '');

function dlLoadBots(force) {
  if (!LIVE || dl.loadingBots || (!force && dl.bots && Date.now() - dl.botsAt < 8000)) return;
  dl.loadingBots = true;
  fetch('/api/dryrun', { cache: 'no-store' })
    .then(async (r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((body) => { dl.bots = body.bots; dl.botsErr = null; dl.botsAt = Date.now(); })
    .catch((e) => { dl.botsErr = String(e && e.message ? e.message : e); })
    .finally(() => { dl.loadingBots = false; if (route.id === 'dryrun') render(); });
}
function dlLoadLive(refreshOnly) {
  if (!LIVE || dl.loadingLive) return;
  dl.loadingLive = true;
  fetch(`/api/live?pair=${encodeURIComponent(dl.pair)}&tf=${dl.tf}`, { cache: 'no-store' })
    .then(async (r) => { const body = await r.json().catch(() => ({})); if (!r.ok) throw new Error(body.error || 'HTTP ' + r.status); return body; })
    .then((body) => { dl.live = body; dl.liveErr = null; })
    .catch((e) => { dl.liveErr = String(e && e.message ? e.message : e); })
    .finally(() => {
      dl.loadingLive = false;
      if (route.id !== 'aovivo') return;
      if (refreshOnly && dl.refs && dl.live && dl.refs.pair === dl.live.pair && dl.refs.tf === dl.live.tf) dlUpdate(); else render();
    });
}
if (LIVE) setInterval(() => { if (route.id === 'dryrun') dlLoadBots(true); else if (route.id === 'aovivo') dlLoadLive(true); }, 10000);

/* ---------- page: strategies in dry-run ---------- */
function dlBotCard(b) {
  if (b.error) return card(b.id, 'não foi possível ler este bot', notAvailable('Bot', b.error));
  const m = b.pooled, [vc, vt] = DL_VERDICT[b.verdict] || ['na', b.verdict];
  const pctDone = Math.min(100, (100 * m.trades) / b.need_trades);
  const progress = h('div', null, h('div', { class: 'sub' }, `${nf0.format(m.trades)} de ${nf0.format(b.need_trades)} trades fechados · ${m.days.toFixed(1).replace('.', ',')} de ${b.need_days} dias`),
    h('div', { style: 'height:6px;border-radius:6px;background:var(--line);margin-top:4px;overflow:hidden' }, h('div', { style: `height:100%;width:${pctDone}%;background:var(--info)` })));
  const kp = h('div', { class: 'kpis', style: 'grid-template-columns:repeat(auto-fit,minmax(min(100%,128px),1fr));margin:10px 0' },
    kpi('Trades fechados', nf0.format(m.trades)), kpi('Abertos agora', nf0.format(b.open.length)),
    kpi('Lucro fechado', usdt(m.net_profit)), kpi('Taxa de acerto', ok(m.win_rate) ? pct0(m.win_rate * 100) : dash, ok(m.payoff) ? `payoff ${nf2.format(m.payoff)}` : null),
    kpi('Fator de lucro', ok(m.profit_factor) ? nf2.format(m.profit_factor) : dash, 'ganhos ÷ perdas'), kpi('Expectativa', ok(m.expectancy_pct) ? dlPct(m.expectancy_pct) : dash, 'por trade, após taxas'),
    kpi('Queda máxima', pct0(m.max_drawdown_pct), 'da carteira'));
  const pairRows = Object.entries(b.pairs).map(([pair, x]) => [h('a', { href: `#/aovivo?pair=${encodeURIComponent(pair)}`, 'data-fkey': 'dl-pair:' + b.id + pair }, pair), nf0.format(x.trades), nf0.format(x.open),
    ok(x.win_rate) ? pct0(x.win_rate * 100) : dash, ok(x.profit_factor) ? nf2.format(x.profit_factor) : dash, h('span', { class: dlTone(x.net_profit) }, usdt(x.net_profit)), pct0(x.max_drawdown_pct)]);
  const openRows = b.open.map((t) => [t.pair, dlWhen(t.open_date) + ' UTC', nf2.format(t.open_rate), nf2.format(t.stake), h('span', { class: dlTone(t.unrealised_pct) }, ok(t.unrealised_pct) ? dlPct(t.unrealised_pct) : dash)]);
  const closedRows = b.closed.slice(0, 25).map((t) => [t.pair, dlWhen(t.open_date), dlWhen(t.close_date), ok(t.minutes) ? ago(t.minutes * 60) : dash, t.reason ? h('code', null, t.reason) : dash, h('span', { class: dlTone(t.profit) }, dlPct(t.profit_pct)), h('span', { class: dlTone(t.profit) }, usdt(t.profit))]);
  const body = h('div', null, progress, kp,
    h('ul', { class: 'sub', style: 'margin:6px 0 10px;padding-left:18px' }, b.reasons.map((r) => h('li', null, r))),
    h('h3', { class: 'sub', style: 'margin:10px 0 4px' }, 'Por ativo'), h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Fechados', 'Abertos', 'Acerto', 'Fator de lucro', 'Lucro', 'Queda máx.'], pairRows, [1, 2, 3, 4, 5, 6])),
    h('h3', { class: 'sub', style: 'margin:14px 0 4px' }, 'Posições abertas agora'),
    openRows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Aberta em', 'Preço de entrada', 'Valor (USDT)', 'Resultado agora'], openRows, [2, 3, 4])) : h('div', { class: 'sub' }, 'Nenhuma posição aberta agora.'),
    h('h3', { class: 'sub', style: 'margin:14px 0 4px' }, 'Últimos trades fechados'),
    closedRows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Entrada (UTC)', 'Saída (UTC)', 'Duração', 'Motivo', 'Resultado', 'Lucro'], closedRows, [3, 5, 6])) : h('div', { class: 'sub' }, 'Ainda nenhum trade fechado. Estratégias lentas levam dias entre um trade e outro.'));
  const det = h('details', { class: 'dl-bot', open: dl.open[b.id] !== false && (dl.open[b.id] || m.trades > 0 || b.open.length > 0) }, h('summary', { style: 'cursor:pointer;padding:6px 0' }, 'Detalhes (por ativo, posições e trades)'), body);
  det.addEventListener('toggle', () => { dl.open[b.id] = det.open; });
  return card(`${b.id} · ${b.strategy.replace(/_H\d+_v\d+$/, '')}`, `no ar desde ${dlWhen(b.frozen_at)} UTC · carteira virtual ${nf0.format(b.wallet)} USDT`, det, { actions: badge({ icon: vc === 'good' ? '✓' : vc === 'bad' ? '✕' : '…', cls: vc }, vt) });
}
function pageDryrunLive() {
  if (!LIVE) return h('div', null, notAvailable('Dry-run ao vivo', 'o snapshot estático não lê os bots. Abra o painel com python -m lab.dashboard serve.'), pageDryrun());
  dlLoadBots(false);
  const head = h('div', { class: 'notice info', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'),
    h('div', null, h('b', null, 'Dry-run: '), 'carteira virtual com preços reais da Binance; nenhuma ordem é enviada e não há chaves de corretora. O veredito usa o número de trades e todas as métricas juntas (regra em lab/config/dryrun.json); "aprovada para análise" só quer dizer que vale uma olhada humana. ', h('a', { href: '#/aovivo', 'data-fkey': 'dl-to-live' }, 'Ver o gráfico ao vivo →')));
  if (dl.botsErr && !dl.bots) return h('div', null, head, card('Estratégias em dry-run', null, notAvailable('Leitura dos bots', dl.botsErr)));
  if (!dl.bots) return h('div', null, head, card('Estratégias em dry-run', null, loadingState('Lendo os bots…')));
  const good = dl.bots.filter((b) => !b.error);
  const sum = (f) => good.reduce((a, b) => a + f(b), 0);
  const kp = h('div', { class: 'kpis', style: 'grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr))' },
    kpi('Estratégias em dry-run', nf0.format(good.length)), kpi('Trades fechados', nf0.format(sum((b) => b.pooled.trades)), 'todas as estratégias'),
    kpi('Posições abertas agora', nf0.format(sum((b) => b.open.length))), kpi('Lucro fechado', usdt(sum((b) => b.pooled.net_profit)), 'após taxas do dry-run'));
  return h('div', null, head, kp, h('div', { style: 'height:var(--gap)' }),
    ...(dl.bots.length ? dl.bots.map(dlBotCard) : [card('Estratégias em dry-run', null, emptyState('Nenhuma estratégia congelada em dry-run.', 'Quando o autopilot subir um bot, ele aparece aqui.'))]),
    h('div', { style: 'height:var(--gap)' }), sectionTitle('Qualidade de execução'), pageDryrun());
}
pageDryrunLive = guard(pageDryrunLive, 'Dry-run');

/* ---------- page: live chart per asset ---------- */
function dlMarkers(live) {
  const step = live.step, snap = (s) => Math.floor(s / step) * step, list = [];
  for (const b of live.bots) {
    if (dl.hide[b.id]) continue;
    const c = dlColor(b.id);
    for (const t of b.trades) {
      list.push({ time: snap(t.open_ts), position: 'belowBar', shape: 'arrowUp', color: c, text: b.id.replace('H-', 'H') });
      if (t.close_ts) list.push({ time: snap(t.close_ts), position: 'aboveBar', shape: 'arrowDown', color: c, text: ok(t.profit_pct) ? dlPct(t.profit_pct, 1) : '' });
    }
  }
  return list.sort((a, b) => a.time - b.time);
}
function dlDraw(el, live) {
  const LW = window.LightweightCharts;
  if (dl.refs) { try { dl.range = dl.refs.chart.timeScale().getVisibleRange(); } catch (e) { /* sem faixa */ } dl.refs.chart.remove(); dl.refs = null; }
  if (!LW) { el.replaceChildren(notAvailable('Gráfico', 'a biblioteca de gráficos não carregou.')); return; }
  const chart = LW.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: cssVar('--panel') }, textColor: cssVar('--ink2'), fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', attributionLogo: true },
    grid: { vertLines: { color: cssVar('--line') }, horzLines: { color: cssVar('--line') } },
    rightPriceScale: { borderColor: cssVar('--line2') }, timeScale: { borderColor: cssVar('--line2'), timeVisible: true, secondsVisible: false },
    localization: { locale: 'pt-BR' }, crosshair: { mode: LW.CrosshairMode.Normal },
  });
  const candle = chart.addSeries(LW.CandlestickSeries, { upColor: cssVar('--good'), downColor: cssVar('--bad'), wickUpColor: cssVar('--good'), wickDownColor: cssVar('--bad'), borderVisible: false });
  candle.setData(live.candles.map(([time, open, high, low, close]) => ({ time, open, high, low, close })));
  const markers = LW.createSeriesMarkers(candle, dlMarkers(live));
  dl.refs = { chart, candle, markers, lines: [], pair: live.pair, tf: live.tf };
  dlLines(live);
  if (dl.range) { try { chart.timeScale().setVisibleRange(dl.range); } catch (e) { chart.timeScale().fitContent(); } } else chart.timeScale().fitContent();
}
function dlLines(live) {
  const r = dl.refs; if (!r) return;
  for (const l of r.lines) { try { r.candle.removePriceLine(l); } catch (e) { /* já removida */ } }
  r.lines = [];
  for (const b of live.bots) {
    if (dl.hide[b.id]) continue;
    for (const t of b.trades.filter((x) => x.is_open)) r.lines.push(r.candle.createPriceLine({ price: t.open_rate, color: dlColor(b.id), lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: `${b.id} entrada ${ok(t.unrealised_pct) ? dlPct(t.unrealised_pct, 2) : ''}` }));
  }
}
function dlUpdate() {
  const r = dl.refs, live = dl.live; if (!r || !live) return;
  r.candle.setData(live.candles.map(([time, open, high, low, close]) => ({ time, open, high, low, close })));
  r.markers.setMarkers(dlMarkers(live)); dlLines(live);
  const price = document.getElementById('dl-price'), stamp = document.getElementById('dl-stamp');
  if (price) price.textContent = ok(live.last_price) ? nf2.format(live.last_price) : dash;
  if (stamp) stamp.textContent = `atualizado ${new Date(live.served_at * 1000).toLocaleTimeString('pt-BR')} · fonte: ${live.source}`;
  const open = document.getElementById('dl-open'); if (open) open.replaceChildren(dlOpenList(live));
}
function dlOpenList(live) {
  const rows = [];
  for (const b of live.bots) for (const t of b.trades.filter((x) => x.is_open)) rows.push([b.id, dlWhen(new Date(t.open_ts * 1000).toISOString().slice(0, 16)) + ' UTC', nf2.format(t.open_rate), nf2.format(t.stake || 0), h('span', { class: dlTone(t.unrealised_pct) }, ok(t.unrealised_pct) ? dlPct(t.unrealised_pct) : dash)]);
  return rows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Estratégia', 'Aberta em', 'Entrada', 'Valor (USDT)', 'Resultado agora'], rows, [2, 3, 4])) : h('div', { class: 'sub' }, 'Nenhuma posição aberta neste ativo agora.');
}
function pageAoVivo(r) {
  if (!LIVE) return notAvailable('Gráfico ao vivo', 'o snapshot estático não busca preços. Abra o painel com python -m lab.dashboard serve.');
  if (r.q.pair && r.q.pair !== dl.pair) { dl.pair = r.q.pair; dl.live = null; dl.range = null; }
  if (r.q.tf && TFS_LIVE.includes(r.q.tf) && r.q.tf !== dl.tf) { dl.tf = r.q.tf; dl.live = null; dl.range = null; }
  const head = h('div', { class: 'notice info', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'),
    h('div', null, 'Preço real da Binance (dados públicos, sem chave) e, em cima dele, as entradas (setas para cima) e saídas (setas para baixo) de cada robô em dry-run neste ativo. A cor identifica o robô. Linhas tracejadas: posições abertas agora. ', h('a', { href: '#/dryrun', 'data-fkey': 'dl-to-dry' }, '← Resultado por estratégia')));
  if (!dl.live && !dl.liveErr) { dlLoadLive(false); return h('div', null, head, card('Gráfico ao vivo', null, loadingState('Buscando candles e operações…'))); }
  if (!dl.live) return h('div', null, head, card('Gráfico ao vivo', null, h('div', null, notAvailable('Gráfico', dl.liveErr), h('div', { class: 'btnrow', style: 'margin-top:8px' }, h('button', { type: 'button', 'data-fkey': 'dl-retry', onclick: () => { dl.liveErr = null; render(); } }, 'Tentar de novo')))));
  const live = dl.live;
  const go = (pair, tf) => { location.hash = `#/aovivo?pair=${encodeURIComponent(pair)}&tf=${tf}`; };
  const pairBar = h('div', { class: 'row', role: 'group', 'aria-label': 'Ativo', style: 'flex-wrap:wrap;gap:6px' }, live.pairs.map((p) => h('button', { type: 'button', 'data-fkey': 'dl-p:' + p, 'aria-pressed': p === live.pair ? 'true' : 'false', onclick: () => go(p, dl.tf) }, p === live.pair ? '✓ ' + p : p)));
  const tfBar = segmented('Candle', 'dl-tf', dl.tf, TFS_LIVE.map((t) => [t, t]), (v) => go(dl.pair, v));
  const chips = h('div', { class: 'row', style: 'flex-wrap:wrap;gap:8px;margin:6px 0' }, live.bots.length ? live.bots.map((b) => {
    const n = b.trades.length, off = !!dl.hide[b.id];
    return h('label', { style: 'display:inline-flex;align-items:center;gap:6px;cursor:pointer' }, h('input', { type: 'checkbox', checked: !off, 'data-fkey': 'dl-bot:' + b.id, onchange: (e) => { dl.hide[b.id] = !e.target.checked; if (dl.refs) { dl.refs.markers.setMarkers(dlMarkers(live)); dlLines(live); } } }),
      h('span', { style: `width:10px;height:10px;border-radius:50%;background:${dlColor(b.id)};display:inline-block` }), `${b.id} (${n} ${n === 1 ? 'operação' : 'operações'})`);
  }) : [h('span', { class: 'sub' }, 'Nenhum robô em dry-run opera este ativo.')]);
  const chartEl = h('div', { class: 'trchart', style: 'height:520px', role: 'img', 'aria-label': `Candles de ${live.pair} com as operações dos robôs em dry-run` });
  queueMicrotask(() => { if (chartEl.isConnected && live.candles.length) dlDraw(chartEl, live); });
  const body = h('div', null, h('div', { class: 'row', style: 'justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:6px' }, pairBar, tfBar),
    h('div', { class: 'row', style: 'gap:14px;align-items:baseline;margin:4px 0' }, h('b', { style: 'font-size:20px' }, live.pair), h('span', { id: 'dl-price', class: 'mono', style: 'font-size:20px' }, ok(live.last_price) ? nf2.format(live.last_price) : dash),
      h('span', { id: 'dl-stamp', class: 'sub' }, `atualizado ${new Date(live.served_at * 1000).toLocaleTimeString('pt-BR')} · fonte: ${live.source}`)),
    live.error ? h('div', { class: 'notice warn' }, h('div', null, 'Sem conexão com a Binance agora: mostrando os candles do arquivo local (podem estar atrasados).')) : null,
    chips, live.candles.length ? chartEl : notAvailable('Candles', 'sem dados para este ativo.'),
    h('div', { class: 'sub', style: 'margin-top:6px' }, 'Atualiza sozinho a cada 10 s. ', h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'Gráficos por TradingView Lightweight Charts')));
  return h('div', null, head, card(`${live.pair} · ao vivo`, 'candles reais e operações dos robôs em dry-run', body),
    card('Posições abertas neste ativo', 'resultado calculado com o último preço', h('div', { id: 'dl-open' }, dlOpenList(live))));
}
const TFS_LIVE = ['15m', '1h'];
pageAoVivo = guard(pageAoVivo, 'Gráfico ao vivo');
