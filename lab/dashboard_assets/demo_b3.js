/* ==================== B3: demonstração ao vivo na conta DEMO da Clear (WIN e WDO) ====================
   Inlined into the page's script by lab.dashboard.render_page. Strings only become text nodes.
   Owner, 2026-11-16: "quero apenas demonstração de como está se portando no demo" and "precisa de uma visualização
   destes trades ao vivo para win e wdo". GET /api/demo-b3 (lab/demo_b3.py) gives, per contract: the engine's live
   feed (today's 1-minute bars including the forming one, bid/ask, position and its open result; written every 5 s),
   its snapshot (last decision and the rule's indicator), its journal (fills, vetoes, alerts) and the research verdict.
   The page polls every 5 s and moves the candles in place; it is drawn again only when something structural changes
   (a trade, the position, the robot's status). A demonstration is NOT evidence. */

const DB = { data: null, at: 0, loading: false, error: null, sig: '', sel: null, tf: '1m', view: null, els: {} };
const DB_TF = { '1m': 60, '5m': 300, '15m': 900 };
function dbLoad(force) {
  if (!LIVE || DB.loading || (!force && DB.data && Date.now() - DB.at < 5000)) return;
  DB.loading = true;
  fetch('/api/demo-b3', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((d) => { DB.data = d; DB.error = null; DB.at = Date.now(); })
    .catch((e) => { DB.error = String(e && e.message ? e.message : e); DB.at = Date.now(); })
    .finally(() => {
      DB.loading = false;
      if (route.id !== 'b3-demo') return;
      const sig = dbSig();
      if (sig !== DB.sig || !DB.view) { DB.sig = sig; render(); } else dbLive();
    });
}
if (LIVE) setInterval(() => { if (route.id === 'b3-demo') dbLoad(true); }, 5000);
window.__demoB3 = () => ({ n: DB.view && DB.view.n || 0, chart: !!(DB.view && DB.view.chart), tf: DB.tf, sel: DB.sel });   /* read by the e2e check */
const dbSig = () => JSON.stringify((DB.data && DB.data.items || []).map((i) => [i.id, i.status, i.phase, i.killswitch, i.trades && i.trades.length,
  i.feed && i.feed.position ? i.feed.position.volume : 0, i.snapshot && i.snapshot.last_signal && i.snapshot.last_signal.bar, i.alerts && i.alerts.length, i.vetoes && i.vetoes.length,
  i.feed && i.feed.day])) + (DB.error || '');

/* ---------- formatting ---------- */
const dbIso = (iso) => new Date(String(iso).replace(/(\.\d{3})\d+/, '$1'));
const dbBrl = (v) => ok(v) ? (v < 0 ? MINUS : v > 0 ? '+' : '') + 'R$ ' + nf2.format(Math.abs(v)) : dash;
const dbPts = (v) => ok(v) ? (v < 0 ? MINUS : v > 0 ? '+' : '') + nfv.format(Math.abs(v)) + ' pts' : dash;
const dbPx = (it, v) => ok(v) ? (it.market === 'WDO' ? nf1.format(v) : nf0.format(v)) : dash;
const dbTime = (iso) => iso ? dbIso(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const dbSecs = (iso) => iso ? dbIso(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const dbDayTime = (iso) => iso ? dbIso(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const dbSigned = (v) => ok(v) ? h('span', { class: tone(v) }, (v < 0 ? MINUS : v > 0 ? '+' : '') + nf2.format(Math.abs(v)) + '%') : dash;
const DB_STATUS = { rodando: { icon: '●', cls: 'good', label: 'rodando' }, parado: { icon: '!', cls: 'bad', label: 'parado' }, 'fora do pregão': { icon: '○', cls: 'info', label: 'fora do pregão' },
  'aguardando o próximo candle': { icon: '…', cls: 'info', label: 'aguardando o próximo candle' }, 'sem dados': { icon: '?', cls: 'warn', label: 'sem dados' } };
const DB_PHASE = { closed: 'mercado fechado', no_entry: 'pregão aberto, fora da janela de entrada', entry: 'janela de entrada aberta', flatten: 'zerando antes do fechamento', unknown: 'sem pregão hoje' };
const DB_REASON = { end_of_day_flatten: 'zeragem do fim do dia', killswitch: 'kill switch', loss_limit: 'limite de perda', stop_loss: 'stop', day_up_so_far: 'dia em alta até aqui', day_down_so_far: 'dia em baixa até aqui' };
const dbReason = (r) => { const s = String(r || ''); if (s.startsWith('server:')) return 'stop ou saída no servidor'; return DB_REASON[s] || s || dash; };
const dbName = (it) => it.market === 'WDO' ? 'mini dólar' : 'mini índice';

/* ---------- data for the chart ---------- */
function dbDay(it) { return (it.feed && it.feed.day) || (it.snapshot && it.snapshot.day) || null; }
function dbPrevClose(it) { const s = it.snapshot; return s && s.day === dbDay(it) ? s.prev_close : null; }
function dbPosition(it) { return (it.feed && it.feed.position) || (it.snapshot && it.snapshot.position) || null; }
function dbLast(it) { const f = it.feed; if (f && ok(f.last)) return f.last; const b = f && f.bars_1m.length ? f.bars_1m : it.snapshot ? it.snapshot.bars : []; return b.length ? b[b.length - 1][4] : null; }
function dbCandles(it, tf) {
  const step = DB_TF[tf] || 60, f = it.feed, s = it.snapshot;
  const base = f && f.bars_1m.length ? f.bars_1m : s && s.bars ? s.bars : [];
  const out = [];
  for (const [t, o, hi, lo, c, v] of base) {
    const k = Math.floor(t / step) * step, last = out[out.length - 1];
    if (last && last[0] === k) { last[2] = Math.max(last[2], hi); last[3] = Math.min(last[3], lo); last[4] = c; last[5] += v; }
    else out.push([k, o, hi, lo, c, v]);
  }
  return out;
}
const dbSp = (t) => t - 3 * 3600;          /* the axis shows Sao Paulo time (UTC-3, no DST since 2019) */
function dbMarks(it, step) {
  const day = dbDay(it), snap = (iso) => dbSp(Math.floor(dbIso(iso).getTime() / 1000 / step) * step), marks = [];
  const onDay = (iso) => iso && dbIso(iso).toLocaleDateString('sv-SE', { timeZone: 'America/Sao_Paulo' }) === day;
  for (const t of it.trades) {
    const buy = t.side === 'compra';
    if (onDay(t.entry_time)) marks.push({ time: snap(t.entry_time), position: buy ? 'belowBar' : 'aboveBar', shape: buy ? 'arrowUp' : 'arrowDown', color: cssVar('--info'), text: (buy ? 'compra ' : 'venda ') + dbPx(it, t.entry_price) });
    if (onDay(t.exit_time)) marks.push({ time: snap(t.exit_time), position: buy ? 'aboveBar' : 'belowBar', shape: 'circle', color: t.pnl_brl > 0 ? cssVar('--good') : cssVar('--bad'), text: 'saída ' + dbBrl(t.pnl_brl) });
  }
  const oe = it.open_entry;
  if (oe && onDay(oe.fill_time || oe.ts)) { const buy = oe.side === 'buy'; marks.push({ time: snap(oe.fill_time || oe.ts), position: buy ? 'belowBar' : 'aboveBar', shape: buy ? 'arrowUp' : 'arrowDown', color: cssVar('--info'), text: (buy ? 'compra ' : 'venda ') + dbPx(it, oe.price) + ' (aberta)' }); }
  return marks.sort((a, b) => a.time - b.time);
}

/* ---------- chart ---------- */
function dbDraw(el, it, tf) {
  const LW = window.LightweightCharts;
  if (!LW) { el.replaceChildren(notAvailable('Gráfico', 'a biblioteca de gráficos não carregou.')); return; }
  const key = `${it.id}|${tf}|${dbDay(it)}`, keep = DB.view && DB.view.key === key ? DB.view.range : null;
  dbDrop();
  const wdo = it.market === 'WDO';
  const chart = LW.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: cssVar('--panel') }, textColor: cssVar('--ink2'), fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', attributionLogo: true },
    grid: { vertLines: { color: cssVar('--line') }, horzLines: { color: cssVar('--line') } },
    rightPriceScale: { borderColor: cssVar('--line2') }, timeScale: { borderColor: cssVar('--line2'), timeVisible: true, secondsVisible: false, rightOffset: 4 },
    localization: { locale: 'pt-BR', priceFormatter: (p) => wdo ? nf1.format(p) : nf0.format(p) },
    crosshair: { mode: LW.CrosshairMode.Normal },
  });
  const candle = chart.addSeries(LW.CandlestickSeries, { upColor: cssVar('--good'), downColor: cssVar('--bad'), wickUpColor: cssVar('--good'), wickDownColor: cssVar('--bad'), borderVisible: false,
    priceFormat: { type: 'price', precision: wdo ? 1 : 0, minMove: wdo ? 0.5 : 5 } });
  const bars = dbCandles(it, tf);
  candle.setData(bars.map(([t, o, hi, lo, c]) => ({ time: dbSp(t), open: o, high: hi, low: lo, close: c })));
  const markers = LW.createSeriesMarkers(candle, dbMarks(it, DB_TF[tf]));
  const pc = dbPrevClose(it), pos = dbPosition(it);
  if (ok(pc)) candle.createPriceLine({ price: pc, color: cssVar('--warn'), lineStyle: 2, lineWidth: 1, axisLabelVisible: true, title: 'fechamento de ontem' });
  if (pos && ok(pos.entry_price)) candle.createPriceLine({ price: pos.entry_price, color: cssVar('--info'), lineStyle: 0, lineWidth: 1, axisLabelVisible: true, title: 'entrada' });
  if (pos && ok(pos.stop)) candle.createPriceLine({ price: pos.stop, color: cssVar('--bad'), lineStyle: 0, lineWidth: 1, axisLabelVisible: true, title: 'stop' });
  DB.view = { key, chart, candle, markers, n: bars.length, last: bars.length ? bars[bars.length - 1][0] : null, range: null, tf, id: it.id };
  if (keep) { try { chart.timeScale().setVisibleLogicalRange(keep); } catch (e) { chart.timeScale().fitContent(); } } else chart.timeScale().fitContent();
}
function dbDrop() {
  if (!DB.view) return;
  try { DB.view.range = DB.view.chart.timeScale().getVisibleLogicalRange(); } catch (e) { DB.view.range = null; }
  const range = DB.view.range, key = DB.view.key;
  try { DB.view.chart.remove(); } catch (e) { /* já removido */ }
  DB.view = { key, range };
}
/* move the forming candle and the live numbers without drawing the page again */
function dbLive(data) {          /* `data`: another page's payload (the real-account section reuses this chart) */
  const items = (data || DB.data) ? (data || DB.data).items || [] : [];
  for (const it of items) {
    const e = DB.els[it.id];
    if (!e) continue;
    const pos = dbPosition(it), last = dbLast(it), pc = dbPrevClose(it);
    if (e.last) e.last.textContent = dbPx(it, last);
    if (e.move) e.move.replaceChildren(ok(last) && ok(pc) ? dbSigned((last / pc - 1) * 100) : dash);
    if (e.open) e.open.replaceChildren(pos && ok(pos.open_result_brl) ? h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)) : dash);
    if (e.upd) e.upd.textContent = it.feed ? 'atualizado às ' + dbSecs(it.feed.updated_at) : '';
    const orow = DB.els[it.id + ':openrow'];
    if (orow && pos) {
      if (orow.last) orow.last.textContent = dbPx(it, last);
      if (orow.res) { orow.res.className = tone(pos.open_result_brl); orow.res.textContent = dbBrl(pos.open_result_brl); }
    }
    const c = DB.els[it.id + ':card'];
    if (c) {
      c.last.textContent = dbPx(it, last);
      c.open.replaceChildren(pos && ok(pos.open_result_brl) ? h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)) : dash);
      if (c.read) c.read.textContent = it.feed ? 'preço lido às ' + dbSecs(it.feed.updated_at) : '';
      if (c.book) c.book.textContent = it.feed && ok(it.feed.bid) ? `compra ${dbPx(it, it.feed.bid)} · venda ${dbPx(it, it.feed.ask)}` : it.symbol;
    }
  }
  const v = DB.view, it = v && v.candle && items.find((x) => x.id === v.id);
  if (!it || `${it.id}|${v.tf}|${dbDay(it)}` !== v.key) { if (v && v.candle) render(); return; }
  const bars = dbCandles(it, v.tf);
  if (!bars.length) return;
  const startAt = bars.findIndex((b) => b[0] >= (v.last ?? -Infinity));
  if (startAt < 0 || bars.length < v.n) { render(); return; }
  for (const [t, o, hi, lo, c] of bars.slice(startAt)) v.candle.update({ time: dbSp(t), open: o, high: hi, low: lo, close: c });
  v.n = bars.length; v.last = bars[bars.length - 1][0];
}

/* ---------- page pieces ---------- */
function dbRuleText(it) {
  if (it.rule === 'P-004') return `P-004 (momento do resto do dia) no ${dbName(it)}: 30 minutos antes do fechamento, compra se o preço está acima do fechamento de ontem e vende se está abaixo; stop a 1% e zera 5 minutos antes do fechamento. No máximo uma operação por dia.`;
  return `${it.rule} no ${it.market}.`;
}
function dbStrip(items) {
  return h('div', { class: 'db-strip' }, items.filter((it) => !it.error).map((it) => {
    const pos = dbPosition(it), last = dbLast(it), pc = dbPrevClose(it), st = DB_STATUS[it.status] || DB_STATUS['sem dados'];
    const e = DB.els[it.id] = { last: h('span', null, dbPx(it, last)), move: h('span', null, ok(last) && ok(pc) ? dbSigned((last / pc - 1) * 100) : dash),
      open: h('span', null, pos && ok(pos.open_result_brl) ? h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)) : dash), upd: h('span', { class: 'sub' }, it.feed ? 'atualizado às ' + dbSecs(it.feed.updated_at) : '') };
    return h('button', { type: 'button', class: 'db-tile', 'aria-pressed': String(DB.sel === it.id), 'data-fkey': 'db-sel:' + it.id, onclick: () => { DB.sel = it.id; render(); } },
      h('div', { class: 'db-tile-h' }, h('b', { title: `${it.market} · ${it.symbol}` }, String(it.id || '').replace(/^(demo|live)-b3-/, '').toUpperCase()), badge(st)),
      h('div', { class: 'db-tile-p' }, e.last, ' ', e.move),
      h('div', { class: 'db-pos' + (pos ? (pos.volume > 0 ? ' long' : ' short') : '') }, pos ? `${pos.volume > 0 ? '▲ Comprado' : '▼ Vendido'} ${nf0.format(Math.abs(pos.volume))} · aberto ` : 'Zerado', pos ? e.open : null),
      dbTileStats(it),
      e.upd);
  }));
}
/* per-robot numbers (owner 2026-11-24: "calculados dentro dos blocos dele, a porcentagem de win rate, quantas operações") */
function dbStats(it) {
  const tr = it.trades || [], n = tr.length, wins = tr.filter((t) => t.pnl_brl > 0).length;
  const gain = tr.filter((t) => t.pnl_brl > 0).reduce((s, t) => s + t.pnl_brl, 0), loss = -tr.filter((t) => t.pnl_brl < 0).reduce((s, t) => s + t.pnl_brl, 0);
  const today = it.trades_today || [];
  return { n, wins, losses: n - wins, wr: n ? wins / n * 100 : null, pnl: it.pnl_total_brl || 0, avg: n ? (it.pnl_total_brl || 0) / n : null,
    pf: loss > 0 ? gain / loss : (gain > 0 ? Infinity : null), todayN: today.length, todayPnl: today.reduce((s, t) => s + t.pnl_brl, 0) };
}
const dbWr = (v) => ok(v) ? nf0.format(v) + '%' : dash;
function dbTileStats(it) {
  const s = dbStats(it);
  const cell = (lab, val) => h('div', null, h('div', { class: 'db-k' }, lab), h('div', { class: 'db-v' }, val));
  return h('div', { class: 'db-stats' },
    cell('Operações', nf0.format(s.n)),
    cell('Acerto', s.n ? h('span', { class: s.wr >= 50 ? 'pos' : 'neg' }, dbWr(s.wr)) : dash),
    cell('Ganhos × perdas', s.n ? `${nf0.format(s.wins)} / ${nf0.format(s.losses)}` : dash),
    cell('Resultado', s.n ? h('span', { class: tone(s.pnl) }, dbBrl(s.pnl)) : dash),
    cell('Média por op.', s.n ? h('span', { class: tone(s.avg) }, dbBrl(s.avg)) : dash),
    cell('Hoje', s.todayN ? h('span', null, `${nf0.format(s.todayN)} op. `, h('span', { class: tone(s.todayPnl) }, dbBrl(s.todayPnl))) : '0 op.'));
}
/* the market tab's totals */
function dbOverview(items, mk, gone) {
  const ok_ = items.filter((i) => !i.error), st = ok_.map(dbStats);
  const n = st.reduce((a, s) => a + s.n, 0), wins = st.reduce((a, s) => a + s.wins, 0), pnl = st.reduce((a, s) => a + s.pnl, 0);
  const todayN = st.reduce((a, s) => a + s.todayN, 0), todayPnl = st.reduce((a, s) => a + s.todayPnl, 0);
  const running = ok_.filter((i) => i.status === 'rodando').length, inPos = ok_.filter((i) => dbPosition(i)).length;
  const traded = st.filter((s) => s.n), pos = traded.filter((s) => s.pnl > 0).length;
  return h('div', { class: 'kpis' },
    kpi(`Robôs no ${mk}`, nf0.format(ok_.length), `${nf0.format(running)} rodando agora`),
    kpi('Em operação agora', nf0.format(inPos), inPos ? 'veja a lista acima' : 'todos zerados'),
    kpi('Operações', nf0.format(n), `hoje ${nf0.format(todayN)}`),
    kpi('Acerto geral', n ? h('span', { class: wins / n >= 0.5 ? 'pos' : 'neg' }, dbWr(wins / n * 100)) : dash, `${nf0.format(wins)} ganhos, ${nf0.format(n - wins)} perdas`),
    kpi('Resultado fechado', h('span', { class: tone(pnl) }, dbBrl(pnl)), `hoje `, h('span', { class: tone(todayPnl) }, dbBrl(todayPnl))),
    kpi('Robôs no positivo', traded.length ? `${nf0.format(pos)} de ${nf0.format(traded.length)}` : dash, 'entre os ativos que já operaram'),
    gone.length ? kpi('Retirados', h('span', { class: tone(dbGoneSum(gone)) }, dbBrl(dbGoneSum(gone))), `${nf0.format(gone.length)} ${plural(gone.length, 'robô', 'robôs')}, resultado líquido congelado na retirada`) : null,
    gone.length ? kpi('Total geral (ativos + retirados)', h('span', { class: tone(pnl + dbGoneSum(gone)) }, dbBrl(pnl + dbGoneSum(gone))), 'o resultado real do experimento desde 16/11') : null);
}
/* robots taken out of the demo (owner 2026-11-25): kept apart, never in the active numbers above */
const dbGoneSum = (gone) => gone.reduce((a, i) => a + (i.retired.resultado_liquido_brl || 0), 0);
function dbRetired(gone, mk) {
  if (!gone.length) return null;
  const name = (i) => String(i.id).replace(/^(demo|live)-b3-/, '').toUpperCase();
  const table = dataTable({ id: 'db-retired-' + mk, label: 'Robôs retirados', rows: gone.map((i) => ({ it: i, key: i.id })), sort0: { key: 'liq', dir: 1 },
    cols: [{ key: 'id', label: 'Robô', val: (r) => r.it.id, cell: (r) => h('button', { type: 'button', class: 'linkbtn', 'data-fkey': 'db-gone:' + r.it.id, onclick: () => { DB.sel = r.it.id; render(); } }, name(r.it)) },
      { key: 'at', label: 'Retirado em', val: (r) => r.it.retired.retirado_em, cell: (r) => dbDayTime(r.it.retired.retirado_em) },
      { key: 'n', label: 'Operações', num: true, val: (r) => r.it.retired.operacoes, cell: (r) => nf0.format(r.it.retired.operacoes) },
      { key: 'gross', label: 'Bruto', num: true, val: (r) => r.it.retired.resultado_bruto_brl, cell: (r) => h('span', { class: tone(r.it.retired.resultado_bruto_brl) }, dbBrl(r.it.retired.resultado_bruto_brl)) },
      { key: 'cost', label: 'Custos', num: true, val: (r) => r.it.retired.custos_brl, cell: (r) => dbBrl(-r.it.retired.custos_brl) },
      { key: 'liq', label: 'Líquido', num: true, val: (r) => r.it.retired.resultado_liquido_brl, cell: (r) => h('span', { class: tone(r.it.retired.resultado_liquido_brl) }, dbBrl(r.it.retired.resultado_liquido_brl)) }] });
  return card(`Retirados do ${mk}`, `Robôs tirados da demo por resultado líquido negativo. Ficam fora dos números dos ativos, mas o prejuízo continua registrado aqui e entra no total geral. Soma: ${dbBrl(dbGoneSum(gone))}.`, table);
}
/* every robot in a trade right now, both markets (owner 2026-11-24: "quais estão comprados ou vendidos ... no meio da operação") */
function dbOpen(all) {
  const rows = all.filter((i) => !i.error && !i.retired && dbPosition(i)).map((i) => ({ it: i, pos: dbPosition(i), key: i.id }));
  if (!rows.length) return card('Em operação agora', 'Robôs comprados ou vendidos neste momento, nos dois ativos.', emptyState('Nenhum robô posicionado agora.', 'Todos estão zerados; quando um entrar, ele aparece aqui com o resultado aberto ao vivo.'));
  const name = (i) => String(i.id).replace(/^(demo|live)-b3-/, '').toUpperCase();
  const entryAt = (r) => r.it.open_entry ? (r.it.open_entry.fill_time || r.it.open_entry.ts) : (r.pos.entry_time || null);
  const longs = rows.filter((r) => r.pos.volume > 0).length;
  const table = dataTable({ id: 'db-open', label: 'Robôs em operação agora', rows, sort0: { key: 'mk', dir: 1 },
    cols: [{ key: 'mk', label: 'Ativo', val: (r) => r.it.market + r.it.id, cell: (r) => r.it.market },
      { key: 'id', label: 'Robô', val: (r) => r.it.id, cell: (r) => h('button', { type: 'button', class: 'linkbtn', 'data-fkey': 'db-open:' + r.it.id, onclick: () => { DB.mk = r.it.market; DB.sel = r.it.id; render(); } }, name(r.it)) },
      { key: 'side', label: 'Lado', val: (r) => r.pos.volume, cell: (r) => h('span', { class: r.pos.volume > 0 ? 'pos' : 'neg' }, r.pos.volume > 0 ? '▲ comprado' : '▼ vendido') },
      { key: 'q', label: 'Contratos', num: true, val: (r) => Math.abs(r.pos.volume), cell: (r) => nf0.format(Math.abs(r.pos.volume)) },
      { key: 'at', label: 'Entrou às', val: entryAt, cell: (r) => dbTime(entryAt(r)) },
      { key: 'in', label: 'Entrada', num: true, val: (r) => r.pos.entry_price, cell: (r) => dbPx(r.it, r.pos.entry_price) },
      { key: 'stop', label: 'Stop', num: true, val: (r) => r.pos.stop, cell: (r) => dbPx(r.it, r.pos.stop) },
      { key: 'last', label: 'Preço agora', num: true, val: (r) => dbLast(r.it), cell: (r) => { const e = h('span', null, dbPx(r.it, dbLast(r.it))); (DB.els[r.it.id + ':openrow'] = DB.els[r.it.id + ':openrow'] || {}).last = e; return e; } },
      { key: 'res', label: 'Resultado aberto', num: true, val: (r) => r.pos.open_result_brl, cell: (r) => { const e = h('span', { class: tone(r.pos.open_result_brl) }, dbBrl(r.pos.open_result_brl)); (DB.els[r.it.id + ':openrow'] = DB.els[r.it.id + ':openrow'] || {}).res = e; return e; } }] });
  return card('Em operação agora', `${nf0.format(rows.length)} ${plural(rows.length, 'robô posicionado', 'robôs posicionados')} nos dois ativos: ${nf0.format(longs)} comprado(s), ${nf0.format(rows.length - longs)} vendido(s). Resultado aberto atualizado a cada 5 segundos; clique no nome para abrir o gráfico.`, table);
}
function dbItem(it) {
  if (it.error) return card(it.id, null, notAvailable('Demonstração', it.error));
  const s = it.snapshot, pos = dbPosition(it), ls = s && s.last_signal, ind = s && s.indicators ? s.indicators : {};
  const st = DB_STATUS[it.status] || DB_STATUS['sem dados'];
  const val = it.research.find((r) => r.split === 'validation'), exp = it.research.find((r) => r.split === 'exploration');
  const decPt = { passed: 'passou', rejected: 'reprovou', inconclusive: 'inconclusiva' };
  const e = DB.els[it.id] || {};
  const live = { last: h('span', null, e.last ? e.last.textContent : dbPx(it, dbLast(it))), open: h('span', null, dash),
    read: h('span', null, it.feed ? 'preço lido às ' + dbSecs(it.feed.updated_at) : ''),
    book: h('span', null, it.feed && ok(it.feed.bid) ? `compra ${dbPx(it, it.feed.bid)} · venda ${dbPx(it, it.feed.ask)}` : it.symbol) };
  if (pos && ok(pos.open_result_brl)) live.open.replaceChildren(h('span', { class: tone(pos.open_result_brl) }, dbBrl(pos.open_result_brl)));
  DB.els[it.id + ':card'] = live;
  const kpis = h('div', { class: 'kpis' },
    kpi('Robô', badge(st), DB_PHASE[it.phase] || '', live.read),
    kpi('Último preço', live.last, live.book),
    kpi('Posição agora', pos ? (pos.volume > 0 ? 'Comprado ' : 'Vendido ') + nf0.format(Math.abs(pos.volume)) : 'Zerado', pos ? h('span', null, `entrada ${dbPx(it, pos.entry_price)}, stop ${dbPx(it, pos.stop)} · resultado aberto `, live.open) : 'sem posição aberta'),
    kpi('Operações da demonstração', nf0.format(it.trades.length), `${nf0.format(it.wins)} com ganho; hoje ${nf0.format(it.trades_today.length)}`),
    kpi('Resultado fechado', h('span', { class: tone(it.pnl_total_brl) }, dbBrl(it.pnl_total_brl)), `${dbPts(it.points_total)}, ${nf0.format(it.volume || 1)} contrato, conta demo`));
  const tfs = segmented('Tempo gráfico', 'db-tf', DB.tf, [['1m', '1 min'], ['5m', '5 min'], ['15m', '15 min']], (v) => { DB.tf = v; render(); });
  const chartEl = h('div', { class: 'trchart', role: 'img', 'aria-label': `Candles de ${DB.tf.replace('m', ' minutos')} do ${it.symbol} hoje, ao vivo, com as entradas e saídas da demonstração` });
  const hasBars = dbCandles(it, DB.tf).length > 0;
  if (hasBars) queueMicrotask(() => { if (chartEl.isConnected) dbDraw(chartEl, it, DB.tf); });
  const closeAt = s && s.session ? dbTime(new Date(dbIso(s.session.close).getTime() - 30 * 60000).toISOString()) : null;
  const decision = ls ? h('p', { class: 'sub' }, `Última decisão (candle de 5 min das ${dbTime(new Date(ls.bar * 1000).toISOString())}): `,
    h('b', null, ls.action === 'hold' ? 'aguardar' : ls.action === 'enter' ? 'comprar' : ls.action === 'enter_short' ? 'vender' : 'sair'),
    ok(ind.rod_ret) ? `; variação desde o fechamento de ontem ${(ind.rod_ret * 100 < 0 ? MINUS : '+') + nf2.format(Math.abs(ind.rod_ret * 100))}%` : '',
    it.rule === 'P-004' && closeAt ? `. A regra decide no candle que fecha às ${closeAt} (hoje ${ok(ind.rod_ret) ? (ind.rod_ret > 0 ? 'seria compra' : 'seria venda') : 'sem sinal'}, se nada mudar) e zera às ${dbTime(s.session.flatten_at)}.` : '.') : null;
  const table = it.trades.length ? dataTable({ id: 'db-trades-' + it.id, label: 'Operações da demonstração', rows: it.trades.map((t, i) => ({ ...t, key: String(i) })), sort0: { key: 'in', dir: -1 },
    cols: [{ key: 'in', label: 'Entrada', val: (t) => t.entry_time, cell: (t) => dbDayTime(t.entry_time) },
      { key: 'side', label: 'Lado', val: (t) => t.side, cell: (t) => t.side },
      { key: 'pin', label: 'Preço de entrada', num: true, val: (t) => t.entry_price, cell: (t) => dbPx(it, t.entry_price) },
      { key: 'out', label: 'Saída', val: (t) => t.exit_time, cell: (t) => dbTime(t.exit_time) },
      { key: 'pout', label: 'Preço de saída', num: true, val: (t) => t.exit_price, cell: (t) => dbPx(it, t.exit_price) },
      { key: 'why', label: 'Motivo da saída', val: (t) => t.exit_reason, cell: (t) => dbReason(t.exit_reason) },
      { key: 'pts', label: 'Pontos', num: true, val: (t) => t.points, cell: (t) => h('span', { class: tone(t.points) }, dbPts(t.points)) },
      { key: 'brl', label: 'Resultado', num: true, val: (t) => t.pnl_brl, cell: (t) => h('span', { class: tone(t.pnl_brl) }, dbBrl(t.pnl_brl)) }] })
    : emptyState('Nenhuma operação ainda.', it.rule === 'P-004' ? 'A P-004 opera no máximo uma vez por dia, 30 minutos antes do fechamento.' : '');
  const alerts = it.alerts.length || it.vetoes.length ? h('ul', { class: 'sub' },
    it.alerts.map((a) => h('li', null, dbDayTime(a.ts) + ': ' + a.message)),
    it.vetoes.map((v) => h('li', null, dbDayTime(v.ts) + ': ordem barrada pelo controle de risco (' + (v.reasons || []).join(', ') + ')'))) : null;
  return h('div', { class: 'rx-stack' },
    card(`${it.rule} no ${it.symbol} (${dbName(it)}), ao vivo`, dbRuleText(it), h('div', { class: 'rx-stack' }, kpis, decision,
      h('div', { class: 'filters' }, tfs),
      hasBars ? h('div', null, chartEl, h('div', { class: 'sub', style: 'margin-top:6px' }, 'Candles do pregão de hoje, horário de Brasília, atualizados a cada 5 segundos (o último está em formação). Linha amarela: fechamento de ontem. Setas: entradas; círculos: saídas com o resultado. ', h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'Gráficos por TradingView Lightweight Charts™')))
        : loadingState('O gráfico aparece quando o robô gravar os primeiros candles.'),
      it.retired ? h('div', { class: 'notice warn', role: 'note' }, h('b', null, 'Retirado da demo em ' + dbDayTime(it.retired.retirado_em) + ': '), `${it.retired.motivo}. Resultado líquido congelado em ${dbBrl(it.retired.resultado_liquido_brl)}; não entra nos números dos ativos.`) : null,
      it.killswitch ? h('div', { class: 'notice warn', role: 'note' }, h('b', null, 'Kill switch ligado: '), 'o arquivo live/STOP existe; o robô zera e não abre nada até ele ser apagado.') : null)),
    card('Operações', 'Todas as operações desta demonstração, com preços e resultados da conta demo da Clear, em reais.', table),
    card('O que a pesquisa já disse desta regra neste contrato', 'A demonstração não muda nada disto: ela não entra nos critérios nem conta como teste.',
      h('div', { class: 'rx-stack' }, h('ul', null,
        h('li', null, 'Exploração (2021-11 a 2024-06): ', h('b', null, exp ? decPt[exp.decision] || exp.decision : 'não lida'), exp && exp.decision !== 'passed' ? ', então nem chegou à validação.' : '.'),
        exp && exp.decision === 'passed' ? h('li', null, 'Validação (2024-07 a 2025-09): ', h('b', null, val ? decPt[val.decision] || val.decision : 'não lida'), val && val.decision !== 'passed' ? ', por isso ela não é candidata a dinheiro real.' : '.') : null,
        h('li', null, `Mesmo código da pesquisa (hash ${s ? s.strategy_hash : dash}). Limites desta demo: ${nf0.format(it.risk.max_contracts_per_symbol || 1)} contrato, perda máxima de R$ ${nf0.format(it.risk.max_daily_loss || 0)} no dia e R$ ${nf0.format(it.risk.max_weekly_loss || 0)} na semana.`)),
        alerts ? h('div', null, h('b', null, 'Avisos do robô'), alerts) : null)));
}

function pageDemoB3() {
  dbDrop();
  DB.els = {};
  const head = rxHeader('B3: WIN e WDO', 'Demonstração ao vivo na conta demo da Clear', 'Os robôs rodam a regra da pesquisa, sem mudar nada, com preço real e dinheiro fictício, no mini índice e no mini dólar. Serve para ver ao vivo como ela se comporta. Não é evidência de lucro: a pesquisa continua validando regras à parte, e só uma aprovada na validação e no teste final pode ir para dinheiro real.');
  if (!LIVE) return h('div', { class: 'rx rx-stack' }, head, card('Demonstração', null, notAvailable('Demonstração ao vivo', 'o snapshot estático não lê os robôs. Abra o painel com python -m lab.dashboard serve.')));
  dbLoad(false);
  if (!DB.data) return h('div', { class: 'rx rx-stack' }, head, DB.error ? emptyState('Não foi possível ler a demonstração.', DB.error) : loadingState('Lendo os robôs da demonstração…'));
  const all = (DB.data.items || []).slice().sort((a, b) => String(a.id).localeCompare(String(b.id)));
  if (!all.length) return h('div', { class: 'rx rx-stack' }, head, emptyState('Nenhuma demonstração configurada.', 'Os arquivos ficam em live/config/demo-b3-*.json.'));
  /* one tab per contract (owner 2026-11-23: "precisamos fazer duas abas na demo para wdo e win") */
  const count = (m) => all.filter((i) => i.market === m && !i.retired).length;
  if (!DB.mk || !count(DB.mk)) DB.mk = count('WIN') ? 'WIN' : 'WDO';
  const mkAll = all.filter((i) => i.market === DB.mk), gone = mkAll.filter((i) => i.retired), items = mkAll.filter((i) => !i.retired);
  const tabs = segmented('Ativo', 'db-mk', DB.mk, [['WIN', `WIN · mini índice (${count('WIN')})`], ['WDO', `WDO · mini dólar (${count('WDO')})`]], (v) => { DB.mk = v; DB.sel = null; render(); });
  if (!DB.sel || !mkAll.some((i) => i.id === DB.sel)) DB.sel = (items[0] || mkAll[0]).id;
  return h('div', { class: 'rx rx-stack' }, head, dbOpen(all), tabs, dbOverview(items, DB.mk, gone), dbStrip(items), dbItem(mkAll.find((i) => i.id === DB.sel)), dbRetired(gone, DB.mk));
}
const DB_STYLE = `.db-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:12px}
.db-tile{display:flex;flex-direction:column;gap:6px;text-align:left;padding:14px 16px;border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--fg);cursor:pointer;font:inherit}
.db-tile[aria-pressed=true]{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}.db-tile-h{display:flex;justify-content:space-between;align-items:center;gap:8px}
.db-tile-p{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
.db-pos{font-size:13px;font-weight:600;color:var(--ink2)}.db-pos.long{color:var(--good)}.db-pos.short{color:var(--bad)}
.db-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px 10px;padding-top:8px;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}
.db-k{font-size:11px;color:var(--ink2);white-space:nowrap}.db-v{font-size:13px;font-weight:600}
.linkbtn{background:none;border:0;padding:0;color:var(--accent);font:inherit;font-weight:600;cursor:pointer;text-decoration:underline}`;
(() => { const st = document.createElement('style'); st.textContent = DB_STYLE; document.head.append(st); })();
