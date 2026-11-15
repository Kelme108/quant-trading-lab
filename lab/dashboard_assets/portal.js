/* ==================== Portal: overview, leaderboard, strategy explorer, comparison, backtests, system ====================
   Inlined into the page's script by lab.dashboard.render_page (after trades_view.js), so it shares the page helpers
   (h, sv, card, chartCard, lineChart, badge, selectBox, segmented, ...) and the page's CSP nonce.
   Every number comes from state.strategies / state.hypotheses (lab/analytics.py over the exported backtests).
   Origin of all results here: BACKTEST (simulated). There are no dry-run or real trades yet; those tabs say so. */

const lb = ui.lb = { stage: 'exploration', q: '', status: 'all', minTrades: '0', year: 'all', more: false, sort: { key: 'score', dir: -1 } };
const sx = ui.sx = { pair: 'all' };
const MIN_TRADES = () => (state.gate_bar && state.gate_bar.minimum_trades) || 30;

/* ---------- data access ---------- */
/* Only live strategies reach the page (candidates, portfolio, dry-run): the server leaves rejected, dropped and
   archived ones out on purpose, so they never mix with the others. They stay in the archive for the agents. */
ui.showAll = false;
const visibleHy = (hy) => !hy.archived && hy.candidate !== false;
const strat = () => (state.strategies || []).filter((r) => r.candidate !== false);
const hiddenCount = () => state.archived_count || 0;
const sRows = (stage) => strat().filter((r) => r.stage === stage);
const sRow = (id, stage) => strat().find((r) => r.id === id && r.stage === stage);
const sIds = () => [...new Set(strat().map((r) => r.id))];
const sStages = (id) => ['exploration', 'validation'].filter((s) => sRow(id, s));
const eligible = (r) => (r.min_trades_pair || 0) >= MIN_TRADES();
const hasStrategies = () => strat().length > 0;
const go = (hash) => { location.hash = hash; };
const idList = (q) => String(q || '').split(',').map((x) => x.trim()).filter(Boolean);

/* ---------- formatting ---------- */
const winPct = (v) => ok(v) ? nf1.format(v * 100) + '%' : dash;
const r2 = (v) => ok(v) ? sgn(nf2.format(v)) : dash;
const plain = (v) => ok(v) ? sgn(nf1.format(v)) + '%' : dash;
const signed = (v) => ok(v) ? (v > 0 ? '+' : '') + sgn(nf2.format(v)) : dash;
const usd = (v) => ok(v) ? (v > 0 ? '+' : '') + sgn(nf2.format(v)) : dash;
const tone = (v) => !ok(v) || v === 0 ? '' : v > 0 ? 'pos' : 'neg';
const hours = (v) => !ok(v) ? dash : v < 48 ? `${nf1.format(v)} h` : `${nf1.format(v / 24)} d`;
const periodText = (r) => r.period && r.period[0] ? `${dayUtc(r.period[0])} a ${dayUtc(r.period[1])}` : dash;
const tier = (s) => s >= 75 ? { cls: 'good', label: 'Forte' } : s >= 50 ? { cls: 'info', label: 'Promissora' } : s >= 35 ? { cls: 'warn', label: 'Frágil' } : { cls: 'bad', label: 'Fraca' };
const gateBadge = (r) => r.gates_all_pass ? badge(ST.cand, 'Passou nos gates') : r.gates_any_rejected ? badge(ST.rej, 'Rejeitada') : badge(ST.incF);
const FLAG_ICON = { good: '✓', bad: '✕', warn: '!', info: 'i' };
const origin = (text = 'backtest') => h('span', { class: 'origin', title: 'Resultado simulado sobre candles históricos: nenhuma ordem foi enviada' }, text);

/* ---------- small visual components ---------- */
function scoreMeter(r) {
  const t = tier(r.score), p = r.score_parts || {};
  const tipText = `Evidência ${nf0.format(r.score)}/100 (${t.label}). Rentabilidade ${nf0.format((p.profit || 0) * 30)}/30 · Risco ${nf0.format((p.risk || 0) * 25)}/25 · Amostra ${nf0.format((p.sample || 0) * 20)}/20 · Consistência ${nf0.format((p.consistency || 0) * 25)}/25`
    + (p.capped_by_sample ? ' · limitada a 40 por amostra pequena' : '') + (p.capped_by_gates ? ' · limitada a 60: rejeitada pelos gates' : '');
  return h('div', { class: 'score', title: tipText }, h('span', { class: 'score-n num' }, nf0.format(r.score)), h('span', { class: 'score-bar ' + t.cls, role: 'img', 'aria-label': tipText }, h('i', { style: `width:${Math.max(2, r.score)}%` })));
}
function spark(points, w = 96, hgt = 28) {
  if (!points || points.length < 2) return h('span', { class: 'muted' }, dash);
  const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), lo = Math.min(0, ...ys), hi = Math.max(0, ...ys), span = hi - lo || 1;
  const X = (v) => 1 + (v - x0) / ((x1 - x0) || 1) * (w - 2), Y = (v) => hgt - 2 - (v - lo) / span * (hgt - 4);
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('');
  const up = ys[ys.length - 1] >= 0;
  return sv('svg', { width: w, height: hgt, class: 'spark', role: 'img', 'aria-label': `Lucro acumulado: ${plain(ys[ys.length - 1])}` },
    sv('line', { x1: 0, x2: w, y1: Y(0), y2: Y(0), class: 'spark-zero' }), sv('path', { d, class: 'spark-line ' + (up ? 'up' : 'down'), fill: 'none' }));
}
function flagList(flags) {
  if (!flags || !flags.length) return h('div', { class: 'sub' }, 'Nenhum sinal acionado com os dados disponíveis.');
  const order = { bad: 0, warn: 1, info: 2, good: 3 };
  return h('ul', { class: 'flags' }, flags.slice().sort((a, b) => order[a.level] - order[b.level]).map((f) => h('li', { class: f.level }, h('span', { class: 'ic ' + f.level, 'aria-hidden': 'true' }, FLAG_ICON[f.level]), h('span', null, f.text))));
}
function flagChips(flags) {
  const by = { bad: [], warn: [], good: [] };
  for (const f of flags || []) if (by[f.level]) by[f.level].push(f.text);
  const chip = (lvl) => by[lvl].length ? h('span', { class: 'badge ' + lvl, title: by[lvl].join('\n') }, h('span', { class: 'ic', 'aria-hidden': 'true' }, FLAG_ICON[lvl]), String(by[lvl].length)) : null;
  return h('span', { class: 'chips' }, chip('bad'), chip('warn'), chip('good'), !flags || !flags.length ? h('span', { class: 'muted' }, dash) : null);
}
function bigKpi(label, value, note, cls = '', termKey) {
  return h('div', { class: 'metric' + (cls ? ' ' + cls : '') }, h('div', { class: 'lab' }, termKey ? term(termKey, label) : label), h('div', { class: 'val num' }, value), note ? h('div', { class: 'note' }, note) : null);
}
function legendRow(items) { return h('div', { class: 'legend' }, items.map((l) => h('span', null, h('span', { class: 'key', style: `border-top-color:${l.color}` }), l.name))); }

/* ---------- charts ---------- */
function histChart(container, hist, width) {
  const { edges, counts } = hist, n = counts.length, m = { l: 36, r: 8, t: 10, b: 30 }, height = 190, pw = width - m.l - m.r, ph = height - m.t - m.b;
  const max = Math.max(...counts, 1), bw = pw / n;
  const svg = sv('svg', { width: width, height, role: 'img', 'aria-label': 'Distribuição do retorno por trade' });
  for (const t of niceTicks(0, max, 3)) svg.append(sv('line', { x1: m.l, x2: m.l + pw, y1: m.t + ph - t / max * ph, y2: m.t + ph - t / max * ph, class: 'gl' }), sv('text', { x: m.l - 6, y: m.t + ph - t / max * ph + 4, 'text-anchor': 'end' }, nf0.format(t)));
  counts.forEach((c, i) => {
    const mid = (edges[i] + edges[i + 1]) / 2, hgt = c / max * ph, x = m.l + i * bw + 1;
    const bar = sv('rect', { x, y: m.t + ph - hgt, width: Math.max(1, bw - 2), height: Math.max(c ? 1 : 0, hgt), rx: 2, fill: mid >= 0 ? 'var(--good)' : 'var(--bad)', opacity: 0.85, class: 'bar', tabindex: '0',
      'aria-label': `${nf0.format(c)} trades entre ${plain(edges[i])} e ${plain(edges[i + 1])}` });
    const rows = [{ value: `${nf0.format(c)} trades`, label: `${plain(edges[i])} a ${plain(edges[i + 1])}` }];
    bar.addEventListener('pointermove', (e) => showTip(e, 'Retorno por trade', rows)); bar.addEventListener('pointerleave', hideTip);
    bar.addEventListener('focus', () => showTip(rectCenter(bar), 'Retorno por trade', rows)); bar.addEventListener('blur', hideTip);
    svg.append(bar);
  });
  const zx = m.l + (n / 2) * bw;
  svg.append(sv('line', { x1: zx, x2: zx, y1: m.t, y2: m.t + ph, class: 'zero' }), sv('line', { x1: m.l, x2: m.l + pw, y1: m.t + ph, y2: m.t + ph, class: 'ax' }));
  for (const f of [0, 0.25, 0.5, 0.75, 1]) svg.append(sv('text', { x: m.l + f * pw, y: height - 10, 'text-anchor': f === 0 ? 'start' : f === 1 ? 'end' : 'middle' }, plain(edges[0] + f * (edges[n] - edges[0]))));
  container.replaceChildren(svg);
}
const symlog = (v) => Math.sign(v) * Math.log10(1 + Math.abs(v));
function scatterChart(container, items, width) {
  const m = { l: 62, r: 22, t: 16, b: 40 }, height = 330, pw = width - m.l - m.r, ph = height - m.t - m.b;
  const xs = items.map((i) => i.x), ys = items.map((i) => symlog(i.y));
  const x1 = Math.max(35, ...xs) * 1.08, ylo = Math.min(0, ...ys) * 1.1, yhi = Math.max(0.5, ...ys) * 1.1;
  const X = (v) => m.l + v / x1 * pw, Y = (v) => m.t + ph - (symlog(v) - ylo) / (yhi - ylo) * ph;
  const svg = sv('svg', { width, height, role: 'img', 'aria-label': 'Retorno contra queda máxima, uma bolha por estratégia' });
  for (const t of [-100, -10, 0, 10, 100, 1000, 10000]) if (symlog(t) >= ylo && symlog(t) <= yhi) svg.append(sv('line', { x1: m.l, x2: m.l + pw, y1: Y(t), y2: Y(t), class: t === 0 ? 'zero' : 'gl' }), sv('text', { x: m.l - 8, y: Y(t) + 4, 'text-anchor': 'end' }, sgn(nf0.format(t)) + '%'));
  for (const t of niceTicks(0, x1, 6)) svg.append(sv('line', { x1: X(t), x2: X(t), y1: m.t, y2: m.t + ph, class: 'gl' }), sv('text', { x: X(t), y: height - 18, 'text-anchor': 'middle' }, nf0.format(t) + '%'));
  const lim = state.gate_bar.max_drawdown_pct;
  if (lim) svg.append(sv('rect', { x: X(lim), y: m.t, width: Math.max(0, m.l + pw - X(lim)), height: ph, class: 'danger-zone' }), sv('line', { x1: X(lim), x2: X(lim), y1: m.t, y2: m.t + ph, class: 'ref' }),
    sv('text', { x: X(lim) + 6, y: m.t + 13, class: 'ink' }, `limite do gate ${nf0.format(lim)}%`));
  svg.append(sv('text', { x: m.l + pw / 2, y: height - 2, 'text-anchor': 'middle' }, 'Queda máxima (pior par), % →'), sv('text', { x: 0, y: 10 }, 'Retorno médio por par, % (escala log) ↑'));
  items.forEach((it, i) => {
    const cx = X(it.x), cy = Y(it.y), dot = sv('circle', { cx, cy, r: 7, fill: `var(--s${(i % 6) + 1})`, stroke: 'var(--panel)', 'stroke-width': 2, class: 'bar', tabindex: '0', 'aria-label': `${it.label}: retorno ${plain(it.y)}, queda ${plain(it.x)}` });
    const rows = [{ value: plain(it.y), label: 'retorno' }, { value: plain(it.x), label: 'queda máxima' }, { value: nf0.format(it.score), label: 'evidência' }];
    dot.addEventListener('pointermove', (e) => showTip(e, it.label, rows)); dot.addEventListener('pointerleave', hideTip);
    dot.addEventListener('focus', () => showTip(rectCenter(dot), it.label, rows)); dot.addEventListener('blur', hideTip);
    svg.append(dot, sv('text', { x: cx + 11, y: cy + 4, class: 'ink halo' }, it.label));
  });
  container.replaceChildren(svg);
}
function heatmap(monthly) {
  if (!monthly || !monthly.length) return emptyState('Sem trades fechados para montar o calendário.');
  const years = {}, vals = monthly.map((m) => Math.abs(m[1] || 0)).sort((a, b) => a - b), cap = vals[Math.floor(vals.length * 0.92)] || vals[vals.length - 1] || 1;
  for (const [ym, v] of monthly) { const [y, mo] = ym.split('-'); (years[y] = years[y] || {})[Number(mo)] = v; }
  const MON = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const cell = (v) => {
    if (v == null) return h('td', { class: 'heat-empty' }, '');
    const a = Math.min(1, Math.abs(v) / cap) * 70 + 8;
    return h('td', { class: 'heat-c', style: `background:color-mix(in srgb, var(${v >= 0 ? '--good' : '--bad'}) ${a}%, transparent)`, title: `${plain(v)} do capital` }, nf1.format(v));
  };
  const rows = Object.keys(years).sort().map((y) => {
    const total = Object.values(years[y]).reduce((a, b) => a + b, 0);
    return h('tr', null, h('th', null, y), MON.map((_, i) => cell(years[y][i + 1])), h('td', { class: 'heat-tot ' + tone(total) }, plain(total)));
  });
  return h('div', { class: 'tablewrap heat' }, h('table', { 'aria-label': 'Resultado mensal em % do capital' }, h('thead', null, h('tr', null, h('th', null, ''), MON.map((m) => h('th', null, m)), h('th', null, 'ano'))), h('tbody', null, rows)));
}

/* ---------- answers: the seven questions, computed (never typed) ---------- */
function answers(stage) {
  const rows = sRows(stage), el = rows.filter(eligible), out = [];
  const top = (list, f, dir = 1) => list.slice().sort((a, b) => (f(b) - f(a)) * dir)[0];
  const item = (q, r, metric, extra) => ({ q, row: r, metric, extra });
  if (!rows.length) return out;
  const best = top(rows, (r) => r.score);
  out.push(item('Performando melhor', best, `evidência ${nf0.format(best.score)}/100`, `${tier(best.score).label}; combina rentabilidade, risco, amostra e consistência`));
  const w = el.length ? top(el, (r) => r.winrate) : null;
  out.push(w ? item('Maior win rate', w, winPct(w.winrate), `entre ${el.length} com amostra suficiente; win rate sozinho não diz se dá lucro`) : { q: 'Maior win rate', none: `nenhuma tem ${MIN_TRADES()}+ trades em todos os pares` });
  const rent = el.length ? top(el, (r) => r.roi_pct) : null;
  out.push(rent ? item('Melhor rentabilidade', rent, `ROI médio ${pct(rent.roi_pct)}`, 'o ROI depende da exposição calibrada de cada hipótese; veja também o risco') : { q: 'Melhor rentabilidade', none: 'sem amostra suficiente' });
  const safe = el.filter((r) => (r.roi_pct || 0) > 0 && ok(r.max_dd_pct));
  const lowRisk = safe.length ? top(safe, (r) => r.max_dd_pct, -1) : null;
  out.push(lowRisk ? item('Menor risco', lowRisk, `queda máx. ${plain(lowRisk.max_dd_pct)}`, 'menor drawdown entre as lucrativas com amostra suficiente') : { q: 'Menor risco', none: 'nenhuma lucrativa com amostra suficiente' });
  const worse = rows.filter((r) => (r.flags || []).some((f) => f.key === 'worsening')).sort((a, b) => (a.score - b.score));
  out.push(worse.length ? { q: 'Piorando', rows: worse.slice(0, 3), extra: 'expectativa por trade do último terço bem abaixo da dos primeiros 2/3' } : { q: 'Piorando', none: 'nenhuma com sinal de queda e amostra suficiente' });
  const retest = rows.filter((r) => (r.flags || []).some((f) => f.key === 'no_validation') || ((r.roi_pct || 0) > 0 && (r.profit_factor || 0) >= 1.5 && !eligible(r))).sort((a, b) => b.score - a.score);
  out.push(retest.length ? { q: 'Merecem novos testes', rows: retest.slice(0, 3), extra: 'passaram na exploração sem validação, ou são promissoras com amostra pequena' } : { q: 'Merecem novos testes', none: 'nenhuma com esse perfil' });
  return out;
}
function answersCard(stage, opts = {}) {
  const list = answers(stage);
  const link = (r) => h('a', { href: `#/strategy/${r.id}?stage=${r.stage}`, class: 'sid', 'data-fkey': 'ans:' + r.key }, r.id, h('span', { class: 'fam' }, r.family));
  const body = list.length ? h('dl', { class: 'answers' }, list.map((a) => [
    h('dt', null, a.q),
    h('dd', null, a.none ? h('span', { class: 'muted' }, a.none) : a.rows ? h('div', null, a.rows.map((r) => h('div', null, link(r), h('span', { class: 'metric-inline' }, ` evidência ${nf0.format(r.score)}`))), h('div', { class: 'sub small' }, a.extra))
      : h('div', null, link(a.row), h('span', { class: 'metric-inline' }, ' ' + a.metric), h('div', { class: 'sub small' }, a.extra)))])) : emptyState('Nenhuma estratégia com resultado nesta etapa.');
  return card(opts.title || 'Respostas rápidas', `${STAGE_CAP[stage]} · calculadas dos resultados; "elegível" = ${MIN_TRADES()}+ trades em cada par`, body, { id: 'sec-respostas' });
}

/* ==================== Leaderboard ==================== */
const LB_COLS = [
  { key: 'score', label: 'Evidência', term: 'evidencia', val: (r) => r.score, cell: (r) => scoreMeter(r) },
  { key: 'gate', label: 'Gates', val: (r) => r.gates_all_pass ? 2 : r.gates_any_rejected ? 0 : 1, cell: (r) => gateBadge(r) },
  { key: 'roi', label: 'ROI', term: 'roi', num: true, val: (r) => r.roi_pct, cell: (r) => h('span', { class: tone(r.roi_pct) }, pct(r.roi_pct)) },
  { key: 'winrate', label: 'Win rate', term: 'winrate', num: true, val: (r) => r.winrate, cell: (r) => h('span', { title: r.winrate_ci ? `Intervalo de 95%: ${winPct(r.winrate_ci[0])} a ${winPct(r.winrate_ci[1])}` : '' }, winPct(r.winrate)) },
  { key: 'pf', label: 'Profit factor', term: 'pf', num: true, val: (r) => r.profit_factor, cell: (r) => ok(r.profit_factor) ? nf2.format(r.profit_factor) : dash },
  { key: 'dd', label: 'Queda máx.', term: 'queda', num: true, val: (r) => r.max_dd_pct, cell: (r) => h('span', { class: ok(r.max_dd_pct) && r.max_dd_pct > state.gate_bar.max_drawdown_pct ? 'neg' : '' }, plain(r.max_dd_pct)) },
  { key: 'trades', label: 'Trades', num: true, val: (r) => r.trades, cell: (r) => h('span', { title: `menor par: ${r.min_trades_pair}` }, nf0.format(r.trades), r.min_trades_pair < MIN_TRADES() ? h('span', { class: 'low', title: 'Algum par tem menos trades que o mínimo' }, ' !') : null) },
  { key: 'exp', label: 'Expectancy', term: 'expectancy', num: true, val: (r) => r.expectancy_pct, cell: (r) => h('span', { class: tone(r.expectancy_pct) }, signed(r.expectancy_pct) + '%') },
  { key: 'net', label: 'Lucro líquido', num: true, extra: true, val: (r) => r.net_profit_abs, cell: (r) => h('span', { class: tone(r.net_profit_abs) }, usd(r.net_profit_abs), h('small', null, ' USDT')) },
  { key: 'sharpe', label: 'Sharpe', term: 'sharpe', num: true, extra: true, val: (r) => r.sharpe, cell: (r) => r.trades >= MIN_TRADES() * 2 ? r2(r.sharpe) : h('span', { class: 'muted', title: 'Poucos trades para um Sharpe confiável' }, ok(r.sharpe) ? r2(r.sharpe) + '*' : dash) },
  { key: 'curve', label: 'Lucro acumulado', val: null, cell: (r) => spark(r.curve, 84, 26) },
  { key: 'flags', label: 'Sinais', val: (r) => (r.flags || []).filter((f) => f.level === 'bad').length * 10 + (r.flags || []).filter((f) => f.level === 'warn').length, cell: (r) => flagChips(r.flags) },
];
function lbRows() {
  let rows = sRows(lb.stage);
  const q = lb.q.trim().toLowerCase();
  if (q) rows = rows.filter((r) => (r.id + ' ' + r.family).toLowerCase().includes(q));
  if (lb.status === 'pass') rows = rows.filter((r) => r.gates_all_pass);
  else if (lb.status === 'reject') rows = rows.filter((r) => r.gates_any_rejected);
  else if (lb.status === 'open') rows = rows.filter((r) => !r.gates_all_pass && !r.gates_any_rejected);
  const mt = Number(lb.minTrades) || 0;
  if (mt) rows = rows.filter((r) => (r.min_trades_pair || 0) >= mt);
  if (lb.year !== 'all') rows = rows.filter((r) => r.years && r.years[lb.year] != null);
  return rows;
}
function lbColumns() {
  const base = LB_COLS.filter((c) => lb.more || !c.extra);
  if (lb.year === 'all') return base;
  const col = { key: 'year', label: `ROI só em ${lb.year}`, num: true, val: (r) => r.years[lb.year], cell: (r) => h('span', { class: tone(r.years[lb.year]) }, pct(r.years[lb.year])) };
  return [base[0], col, ...base.slice(1)];
}
function lbTable(rows, cols) {
  const st = lb.sort, col = cols.find((c) => c.key === st.key) || cols[0];
  const sorted = rows.slice().sort((a, b) => { const x = col.val ? col.val(a) : null, y = col.val ? col.val(b) : null; if (x == null || y == null) return x == null && y == null ? 0 : x == null ? 1 : -1; return (x < y ? -1 : x > y ? 1 : 0) * st.dir; });
  const sel = new Set(idList(route.q.ids));
  const toggle = (r) => { const s = new Set(sel); s.has(r.id) ? s.delete(r.id) : s.add(r.id); lbSelect([...s]); };
  const head = h('tr', null, h('th', { class: 'nosort' }, h('span', { class: 'sr' }, 'Comparar')), h('th', { class: 'rank' }, '#'), h('th', null, 'Estratégia'),
    cols.map((c) => h('th', { class: (c.num ? 'num ' : '') + 'c-' + c.key, title: c.term && glossary()[c.term] ? glossary()[c.term][1] : null, 'aria-sort': c.val ? (st.key === c.key ? (st.dir > 0 ? 'ascending' : 'descending') : 'none') : null },
      c.val ? h('button', { type: 'button', class: 'sortbtn', 'data-fkey': 'lbth:' + c.key, onclick: () => { lb.sort = { key: c.key, dir: st.key === c.key ? -st.dir : (c.key === 'dd' ? 1 : -1) }; render(); } }, c.label + (st.key === c.key ? (st.dir > 0 ? ' ▴' : ' ▾') : '')) : c.label)));
  const body = sorted.map((r, i) => h('tr', { class: sel.has(r.id) ? 'picked' : '', 'data-key': r.key },
    h('td', { class: 'nw' }, h('input', { type: 'checkbox', checked: sel.has(r.id), 'aria-label': `Comparar ${r.id}`, 'data-fkey': 'lbsel:' + r.id, onchange: () => toggle(r) })),
    h('td', { class: 'rank num' }, String(i + 1)),
    h('td', { class: 'sname' }, h('a', { href: `#/strategy/${r.id}?stage=${r.stage}`, 'data-fkey': 'lbrow:' + r.key }, h('b', null, r.id), h('span', { class: 'fam block' }, r.family)), r.in_portfolio ? badge(ST.good, 'no portfólio') : null),
    cols.map((c) => h('td', { class: (c.num ? 'num' : '') + ' c-' + c.key, 'data-label': c.label }, c.cell(r)))));
  return h('div', { class: 'tablewrap lbwrap' }, h('table', { class: 'lb stack', 'aria-label': 'Ranking de estratégias' }, h('thead', null, head), h('tbody', null, body)));
}
function lbSelect(ids) { go(`#/leaderboard?stage=${lb.stage}${ids.length ? '&ids=' + ids.join(',') : ''}`); }
function pageLeaderboard() {
  if (route.q.stage === 'exploration' || route.q.stage === 'validation') lb.stage = route.q.stage;
  if (!hasStrategies()) return emptyState('Nenhuma estratégia com resultado ainda.', 'Rode um ciclo do laboratório: o ranking aparece quando houver backtests concluídos.');
  const years = [...new Set(sRows(lb.stage).flatMap((r) => Object.keys(r.years || {})))].sort();
  if (lb.year !== 'all' && !years.includes(lb.year)) lb.year = 'all';
  const rows = lbRows(), cols = lbColumns(), picked = idList(route.q.ids).filter((id) => sRow(id, lb.stage));
  const filters = h('div', { class: 'filters toolbar' },
    segmented('Etapa', 'lb-stage', lb.stage, [['exploration', 'Exploração'], ['validation', 'Validação']], (v) => { lb.stage = v; go(`#/leaderboard?stage=${v}`); }),
    h('label', null, 'Buscar ', h('input', { type: 'search', value: lb.q, placeholder: 'id ou família', 'data-fkey': 'lb-q', oninput: (e) => { lb.q = e.target.value; render(); } })),
    selectBox('Gates', 'lb-status', lb.status, [['all', 'Todos'], ['pass', 'Passou em todos os pares'], ['reject', 'Rejeitada'], ['open', 'Sem veredito']], (v) => { lb.status = v; render(); }),
    selectBox('Trades mínimos por par', 'lb-min', lb.minTrades, [['0', 'Sem mínimo'], ['30', '30 (mínimo do gate)'], ['100', '100']], (v) => { lb.minTrades = v; render(); }),
    selectBox('Período', 'lb-year', lb.year, [['all', 'Etapa inteira'], ...years.map((y) => [y, `ROI só em ${y}`])], (v) => { lb.year = v; render(); }),
    h('button', { type: 'button', 'data-fkey': 'lb-more', 'aria-pressed': lb.more ? 'true' : 'false', onclick: () => { lb.more = !lb.more; render(); } }, lb.more ? '✓ Mais métricas' : 'Mais métricas'),
    h('button', { type: 'button', 'data-fkey': 'lb-clear', onclick: () => { lb.q = ''; lb.status = 'all'; lb.minTrades = '0'; lb.year = 'all'; lb.sort = { key: 'score', dir: -1 }; go(`#/leaderboard?stage=${lb.stage}`); } }, 'Limpar'));
  const cmp = h('div', { class: 'cmpbar' + (picked.length ? ' on' : ''), role: 'status' }, picked.length
    ? [h('span', null, `${picked.length} selecionada${picked.length > 1 ? 's' : ''}: `, h('b', null, picked.join(', '))), h('a', { class: 'btn primary', href: `#/compare?ids=${picked.join(',')}&stage=${lb.stage}`, 'data-fkey': 'lb-compare' }, picked.length > 1 ? 'Comparar' : 'Escolha mais uma para comparar')]
    : [h('span', { class: 'muted' }, 'Marque estratégias para compará-las lado a lado.')]);
  const note = h('div', { class: 'sub small lbnote' }, `${rows.length} de ${sRows(lb.stage).length} estratégias · ${STAGE_CAP[lb.stage]} · todos os valores são backtest simulado, cenário base, somados ou médios sobre os pares. `,
    h('b', null, 'A evidência não é o win rate: '), `combina rentabilidade (30), risco (25), amostra (20) e consistência (25); limitada a 40 com amostra pequena e a 60 se os gates rejeitaram. `,
    state.hypotheses.some((x) => x.invalid) ? 'Hipóteses inválidas ficam de fora (números descartados). ' : '', '* Sharpe com poucos trades. Passe o mouse sobre um cabeçalho para ver o que a métrica significa.');
  return h('div', null,
    card('Ranking de estratégias', null, h('div', null, filters, cmp, rows.length ? lbTable(rows, cols) : emptyState('Nenhuma estratégia com esses filtros.', null, h('button', { type: 'button', onclick: () => { lb.q = ''; lb.status = 'all'; lb.minTrades = '0'; lb.year = 'all'; render(); } }, 'Limpar filtros')), note), { id: 'sec-ranking', cls: 'flush' }), h('div', { style: 'height:12px' }), answersCard(lb.stage));
}

/* ==================== Strategy explorer ==================== */
function viewOf(row, pair) {
  if (pair === 'all') return row;
  const hy = hypById(row.id), cell = hy && hy.cells.find((c) => c.split === row.stage && c.pair === pair);
  if (!cell || !cell.analytics) return null;
  const a = cell.analytics;
  return { ...a, max_dd_pct: cell.max_drawdown_pct, roi_stress_pct: ok(cell.profit_by_cost.stress) ? cell.profit_by_cost.stress / state.wallet * 100 : null, min_trades_pair: a.trades };
}
function pageStrategy(idArg) {
  if (!hasStrategies()) return emptyState('Nenhuma estratégia com resultado ainda.', 'O explorador aparece quando houver backtests concluídos.');
  const all = sIds();
  const id = idArg && all.includes(idArg) ? idArg : (idArg ? null : (topRow(lb.stage) || strat()[0]).id);
  if (!id) return card('Estratégia não encontrada', `Não há resultado para "${idArg}".`, h('div', null, 'Escolha uma:', h('div', { class: 'btnrow', style: 'margin-top:8px' }, all.map((x) => h('a', { class: 'badge info', href: `#/strategy/${x}` }, x)))));
  const stages = sStages(id), stage = stages.includes(route.q.stage) ? route.q.stage : stages[0], row = sRow(id, stage), hy = hypById(id);
  const pair = route.q.pair && row.pairs.includes(route.q.pair) ? route.q.pair : 'all', v = viewOf(row, pair);
  const nav = (o) => go(`#/strategy/${id}?stage=${o.stage || stage}&pair=${o.pair || pair}`);
  const head = h('div', { class: 'sxhead' },
    h('div', { class: 'sxtitle' }, h('div', { class: 'eyebrow' }, row.family), h('h2', null, id), h('div', { class: 'row' }, gateBadge(row), tier(row.score) && h('span', { class: 'badge ' + tier(row.score).cls }, `Evidência ${nf0.format(row.score)} · ${tier(row.score).label}`), origin(), hy && hy.in_portfolio ? badge(ST.good, 'no portfólio') : null)),
    h('div', { class: 'filters' }, selectBox('Estratégia', 'sx-id', id, all.map((x) => [x, `${x} · ${(hypById(x) || {}).family || ''}`]), (val) => go(`#/strategy/${val}?stage=${stage}`)),
      stages.length > 1 ? segmented('Etapa', 'sx-stage', stage, stages.map((s) => [s, STAGE_CAP[s]]), (val) => nav({ stage: val })) : h('span', { class: 'tag' }, STAGE_CAP[stage]),
      segmented('Par', 'sx-pair', pair, [['all', 'Todos'], ...row.pairs.map((p) => [p, short(p)])], (val) => nav({ pair: val }))));
  if (!v) return h('div', null, head, emptyState('Sem resultado para este par.'));
  const kp = h('div', { class: 'metrics' },
    bigKpi('ROI', pct(v.roi_pct), pair === 'all' ? 'média dos pares' : `lucro ${usd(v.net_profit_abs)} USDT`, tone(v.roi_pct), 'roi'),
    bigKpi('Lucro líquido', h('span', null, usd(v.net_profit_abs), h('small', null, 'USDT')), pair === 'all' ? `soma de ${row.n_pairs} carteiras de ${num(state.wallet)}` : `de ${num(state.wallet)} USDT iniciais`, tone(v.net_profit_abs)),
    bigKpi('Win rate', winPct(v.winrate), v.winrate_ci ? `IC 95%: ${winPct(v.winrate_ci[0])} a ${winPct(v.winrate_ci[1])}` : null, '', 'winrate'),
    bigKpi('Profit factor', ok(v.profit_factor) ? nf2.format(v.profit_factor) : dash, v.profit_factor_note || (ok(v.profit_factor) ? `ganhos ${nf0.format(v.gross_profit_abs || 0)} / perdas ${nf0.format(Math.abs(v.gross_loss_abs || 0))}` : null), ok(v.profit_factor) ? (v.profit_factor >= 1 ? 'pos' : 'neg') : '', 'pf'),
    bigKpi('Queda máxima', plain(v.max_dd_pct), `limite do gate ${nf0.format(state.gate_bar.max_drawdown_pct)}%${pair === 'all' ? ' · pior par' : ''}`, ok(v.max_dd_pct) && v.max_dd_pct > state.gate_bar.max_drawdown_pct ? 'neg' : '', 'queda'),
    bigKpi('Expectancy', signed(v.expectancy_pct) + '%', `${usd(v.expectancy_abs)} USDT por trade`, tone(v.expectancy_pct), 'expectancy'));
  const mini = h('dl', { class: 'minis' },
    [['Trades', nf0.format(v.trades) + (pair === 'all' ? ` (mín. ${row.min_trades_pair} por par)` : '')], ['Sharpe (Freqtrade)', ok(v.sharpe) ? r2(v.sharpe) : dash], ['Payoff (ganho médio / perda média)', ok(v.payoff) ? nf2.format(v.payoff) : dash],
      ['Ganho médio / perda média', `${plain(v.avg_win_pct)} / ${plain(v.avg_loss_pct)}`], ['Duração média', hours(v.avg_duration_h)],
      ['Maior sequência de ganhos / perdas', v.streaks ? `${v.streaks.max_win} / ${v.streaks.max_loss}` : dash], ['Sequência atual', v.streaks ? (v.streaks.current > 0 ? `${v.streaks.current} ganhos` : v.streaks.current < 0 ? `${-v.streaks.current} perdas` : dash) : dash],
      ['Taxas pagas (estimativa)', ok(v.fees_paid_abs) ? nf2.format(v.fees_paid_abs) + ' USDT' : dash], ['Período', periodText(v)]].map(([k, val]) => h('div', { class: 'mini' }, h('dt', null, k), h('dd', null, val))));
  const cells = hy ? hy.cells.filter((c) => c.split === stage && (pair === 'all' || c.pair === pair)) : [];
  const eq = cells.filter((c) => c.equity && c.equity.length);
  const equity = chartCard({ id: 'sx-eq', title: 'Curva de capital', sim: true, hasData: eq.length > 0, subtitle: `${STAGE_CAP[stage]} · custo base · variação do saldo em % da carteira inicial, nos fechamentos de trades`,
    legend: eq.map((c) => ({ name: short(c.pair), color: pairColor(c.pair) })), empty: notAvailable('Curva de capital', 'o arquivo de resultado do backtest não está disponível.'),
    draw: (el, w) => lineChart(el, { series: eq.map((c) => ({ name: short(c.pair), color: pairColor(c.pair), points: c.equity.map(([t, b]) => [t, (b / state.wallet - 1) * 100]) })), width: w, height: 300, zero: true, yLabel: 'Variação do saldo, em %',
      fmtY: (val, t) => (t ? pct(val) : sgn(nfv.format(val)) + '%') }),
    table: { head: ['Par', 'Saldo final (USDT)', 'Mínimo', 'Máximo'], rows: eq.map((c) => { const b = c.equity.map((p) => p[1]); return [short(c.pair), nf2.format(b[b.length - 1]), nf2.format(Math.min(...b)), nf2.format(Math.max(...b))]; }), numCols: [1, 2, 3] } });
  const dd = drawdownChartFor(cells, 'sx-dd');
  const hist = v.histogram ? chartCard({ id: 'sx-hist', title: 'Distribuição de ganhos e perdas', sim: true, subtitle: `Retorno por trade (%), ${nf0.format(v.trades)} trades`, hasData: true,
    draw: (el, w) => histChart(el, v.histogram, w), table: { head: ['Faixa de retorno por trade', 'Trades'], rows: v.histogram.counts.map((c, i) => [`${plain(v.histogram.edges[i])} a ${plain(v.histogram.edges[i + 1])}`, nf0.format(c)]), numCols: [1] } }) : card('Distribuição de ganhos e perdas', null, emptyState('Sem trades.'));
  const reasons = Object.entries(v.exit_reasons || {});
  const exitCard = card('Como as operações terminam', 'Motivo de saída informado pelo Freqtrade', reasons.length ? h('div', { class: 'tablewrap' }, simpleTable(['Motivo', 'Trades', '%'], reasons.map(([k, n]) => [k, nf0.format(n), nf1.format(n / v.trades * 100) + '%']), [1, 2])) : emptyState('Sem trades.'));
  const cost = hy ? costChartFor(cells.length ? cells : hy.cells.filter((c) => c.split === stage), hy.invalid, 'sx-cost') : null;
  const sinais = card('Sinais da análise', 'Calculados dos números ao lado; cada sinal cita o valor que o acionou', flagList(row.flags));
  const sp = row.score_parts || {};
  const parts = [['Rentabilidade', sp.profit, 30], ['Risco', sp.risk, 25], ['Amostra', sp.sample, 20], ['Consistência', sp.consistency, 25]];
  const scoreCard = card(term('evidencia', 'Evidência'), 'Não é o win rate: quatro componentes explícitos', h('div', null, scoreMeter(row),
    h('div', { class: 'parts' }, parts.map(([name, val, max]) => h('div', { class: 'part' }, h('span', null, name), h('span', { class: 'part-bar' }, h('i', { style: `width:${(val || 0) * 100}%` })), h('span', { class: 'num' }, `${nf0.format((val || 0) * max)}/${max}`)))),
    sp.capped_by_sample ? h('div', { class: 'sub small' }, 'Limitada a 40 por amostra pequena.') : null, sp.capped_by_gates ? h('div', { class: 'sub small' }, 'Limitada a 60: os gates rejeitaram esta estratégia.') : null));
  const other = sRow(id, stage === 'exploration' ? 'validation' : 'exploration');
  const sets = [['ROI', 'roi_pct', pct], ['Profit factor', 'profit_factor', (x) => ok(x) ? nf2.format(x) : dash], ['Win rate', 'winrate', winPct], ['Queda máxima', 'max_dd_pct', plain], ['Trades', 'trades', (x) => nf0.format(x)], ['Expectancy', 'expectancy_pct', (x) => signed(x) + '%']];
  const ex = sRow(id, 'exploration'), va = sRow(id, 'validation');
  const trainVal = ex && va ? card('Exploração × validação', 'A diferença entre o que foi otimizado e o que foi lido uma vez depois', h('div', { class: 'tablewrap' }, simpleTable(['Métrica', 'Exploração', 'Validação'], sets.map(([n, k, f]) => [n, f(ex[k]), f(va[k])]), [1, 2])))
    : card('Exploração × validação', null, emptyState(other ? '' : `Só existe a etapa de ${STAGE[stage]}.`, 'A validação só roda depois que a exploração passa nos gates em todos os pares, e é lida uma única vez.'));
  const perPair = card('Por par', 'Cada linha é um backtest; abra o gráfico de preço e as operações', h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Gates', 'Trades', 'ROI', 'Win rate', 'Profit factor', 'Queda máx.', 'Expectancy', 'Sharpe', ''],
    row.per_pair.map((p) => [pairTag(p.pair), badge(DECISION[p.decision] || ST.info), nf0.format(p.trades), pct(p.roi_pct), winPct(p.winrate), ok(p.profit_factor) ? nf2.format(p.profit_factor) : dash, plain(p.max_dd_pct), signed(p.expectancy_pct) + '%', r2(p.sharpe),
      h('span', { class: 'row' }, h('a', { href: `#/chart/${encodeURIComponent(p.experiment_id)}`, 'data-fkey': 'sx-tr:' + p.experiment_id }, 'Operações'), h('a', { href: `#/experiments/${encodeURIComponent(p.experiment_id)}`, 'data-fkey': 'sx-ex:' + p.experiment_id }, 'Gates'))]), [2, 3, 4, 5, 6, 7, 8])));
  const runs = experiments().filter((e) => e.hypothesis_id === id).sort((a, b) => String(b.created_at_utc).localeCompare(String(a.created_at_utc)));
  const hist2 = card('Histórico de backtests', `${runs.length} execuções desta hipótese (inclui as substituídas por reexecução)`, runs.length ? h('div', { class: 'tablewrap' }, simpleTable(['Quando', 'Experimento', 'Par', 'Etapa', 'Execução', 'Decisão'], runs.slice(0, 30).map((e) => [whenShort(e.created_at_utc),
    h('a', { href: `#/experiments/${encodeURIComponent(e.id)}`, class: 'mono' }, e.id), short(e.pair), STAGE_CAP[e.split] || e.split, badge(execMeta(e.status)), e.decision ? badge(DECISION[e.decision] || ST.info) : 'sem decisão']))) : emptyState('Nenhuma execução registrada.'));
  const logic = card('Descrição e lógica operacional', `Timeframe ${state.timeframes.join(', ')} · spot, somente long · regra fixada antes do teste`, h('div', null,
    hy ? h('div', { class: 'pre' }, hy.rule) : emptyState('Regra não disponível.'), hy && hy.notes ? h('div', { class: 'sub', style: 'margin-top:8px' }, hy.notes) : null,
    h('div', { class: 'sub small', style: 'margin-top:8px' }, 'Indicadores e parâmetros estão descritos na regra acima: o laboratório os guarda como texto, não como campos separados, então o painel não os extrai.')));
  return h('div', { class: 'sx' }, head, kp, mini,
    h('div', { class: 'grid g21' }, h('div', { class: 'vstack' }, equity, dd), h('div', { class: 'vstack' }, sinais, scoreCard, trainVal)),
    h('div', { class: 'grid g2' }, hist, card('Resultado por mês', `Soma dos trades fechados no mês, em % do capital (${pair === 'all' ? 'todos os pares' : short(pair)})`, heatmap(v.monthly))),
    h('div', { class: 'grid g2' }, cost || card('Custos', null, emptyState('Sem dados.')), exitCard), perPair, hist2, logic);
}
const topRow = (stage) => sRows(stage).slice().sort((a, b) => b.score - a.score)[0];

/* ==================== Comparison ==================== */
function pageCompare() {
  if (route.q.stage === 'exploration' || route.q.stage === 'validation') lb.stage = route.q.stage;
  const stage = lb.stage;
  if (!hasStrategies()) return emptyState('Nenhuma estratégia com resultado ainda.');
  const avail = sRows(stage);
  let ids = idList(route.q.ids).filter((id) => sRow(id, stage)).slice(0, 6);
  const set = (list, st = stage) => go(`#/compare?stage=${st}${list.length ? '&ids=' + list.join(',') : ''}`);
  const picker = h('div', { class: 'picker' }, avail.map((r) => { const on = ids.includes(r.id), idx = ids.indexOf(r.id);
    return h('label', { class: 'chip' + (on ? ' on' : '') }, h('input', { type: 'checkbox', checked: on, 'data-fkey': 'cmp:' + r.id, disabled: !on && ids.length >= 6, onchange: () => set(on ? ids.filter((x) => x !== r.id) : [...ids, r.id]) }),
      on ? h('span', { class: 'dot', style: `background:var(--s${idx + 1})` }) : null, r.id, h('small', null, r.family)); }));
  const top = h('div', { class: 'filters toolbar' }, segmented('Etapa', 'cmp-stage', stage, [['exploration', 'Exploração'], ['validation', 'Validação']], (v) => { lb.stage = v; set(ids.filter((id) => sRow(id, v)), v); }),
    h('button', { type: 'button', 'data-fkey': 'cmp-top', onclick: () => set(avail.slice().sort((a, b) => b.score - a.score).slice(0, 4).map((r) => r.id)) }, 'Escolher as 4 de maior evidência'), h('button', { type: 'button', 'data-fkey': 'cmp-none', onclick: () => set([]) }, 'Limpar'));
  const head = card('Comparar estratégias', `${STAGE_CAP[stage]} · escolha de 2 a 6 · valores em backtest simulado`, h('div', null, top, picker));
  if (ids.length < 2) return h('div', null, head, h('div', { style: 'height:12px' }), emptyState(ids.length ? 'Escolha pelo menos mais uma estratégia.' : 'Escolha duas ou mais estratégias acima.', 'O comparativo mostra retorno acumulado, risco × retorno, métricas lado a lado e consistência por ano.'));
  const rows = ids.map((id) => sRow(id, stage));
  const color = (i) => `var(--s${i + 1})`;
  const curves = chartCard({ id: 'cmp-curves', title: 'Lucro acumulado', sim: true, subtitle: 'Soma do lucro dos trades fechados, em % do capital total dos pares', legend: rows.map((r, i) => ({ name: r.id, color: color(i) })), hasData: rows.some((r) => r.curve && r.curve.length > 1),
    draw: (el, w) => lineChart(el, { series: rows.map((r, i) => ({ name: r.id, color: color(i), points: r.curve || [] })), width: w, height: 320, zero: true, yLabel: 'Lucro acumulado em % do capital', fmtY: (val, t) => (t ? pct(val) : sgn(nfv.format(val)) + '%') }),
    table: { head: ['Estratégia', 'Lucro acumulado final'], rows: rows.map((r) => [r.id, pct(r.curve && r.curve.length ? r.curve[r.curve.length - 1][1] : null)]), numCols: [1] } });
  const scatter = chartCard({ id: 'cmp-scatter', title: 'Risco × retorno', sim: true, subtitle: 'Mais à esquerda e mais acima é melhor; a zona à direita passa do limite de queda do gate', hasData: true,
    legend: rows.map((r, i) => ({ name: r.id, color: color(i) })), draw: (el, w) => scatterChart(el, rows.map((r) => ({ label: r.id, x: r.max_dd_pct || 0, y: r.roi_pct || 0, score: r.score })), w),
    table: { head: ['Estratégia', 'Queda máxima', 'ROI médio por par'], rows: rows.map((r) => [r.id, plain(r.max_dd_pct), pct(r.roi_pct)]), numCols: [1, 2] } });
  const METRICS = [['Evidência', (r) => r.score, (x) => nf0.format(x), 1], ['ROI', (r) => r.roi_pct, pct, 1], ['Lucro líquido', (r) => r.net_profit_abs, (x) => usd(x) + ' USDT', 1], ['Win rate', (r) => r.winrate, winPct, 1], ['Profit factor', (r) => r.profit_factor, (x) => nf2.format(x), 1],
    ['Queda máxima', (r) => r.max_dd_pct, plain, -1], ['Expectancy', (r) => r.expectancy_pct, (x) => signed(x) + '%', 1], ['Sharpe', (r) => r.sharpe, r2, 1], ['Trades', (r) => r.trades, (x) => nf0.format(x), 1], ['Pares lucrativos', (r) => r.pairs_positive / r.n_pairs, (x) => `${nf0.format(x * 100)}%`, 1],
    ['Anos positivos', (r) => r.positive_year_share, (x) => `${nf0.format(x * 100)}%`, 1]];
  const table = h('div', { class: 'tablewrap' }, h('table', { class: 'cmp', 'aria-label': 'Métricas lado a lado' }, h('thead', null, h('tr', null, h('th', null, 'Métrica'), rows.map((r, i) => h('th', { class: 'num' }, h('span', { class: 'dot', style: `background:${color(i)}` }), h('a', { href: `#/strategy/${r.id}?stage=${stage}` }, r.id))))),
    h('tbody', null, METRICS.map(([name, f, fmt, dir]) => { const vals = rows.map(f).filter(ok), best = vals.length > 1 ? (dir > 0 ? Math.max(...vals) : Math.min(...vals)) : null;
      return h('tr', null, h('th', null, name), rows.map((r) => { const x = f(r); return h('td', { class: 'num' + (ok(x) && x === best ? ' best' : '') }, ok(x) ? fmt(x) : dash); })); }),
      h('tr', null, h('th', null, 'Gates'), rows.map((r) => h('td', { class: 'num' }, gateBadge(r)))), h('tr', null, h('th', null, 'Sinais'), rows.map((r) => h('td', { class: 'num' }, flagChips(r.flags)))))));
  const yrs = [...new Set(rows.flatMap((r) => Object.keys(r.years || {})))].sort();
  const cap = Math.max(1, ...rows.flatMap((r) => Object.values(r.years || {}).map((x) => Math.abs(x)))) * 0.7;
  const years = h('div', { class: 'tablewrap heat' }, h('table', { 'aria-label': 'Resultado por ano' }, h('thead', null, h('tr', null, h('th', null, 'Ano'), rows.map((r, i) => h('th', null, h('span', { class: 'dot', style: `background:${color(i)}` }), r.id)))),
    h('tbody', null, yrs.map((y) => h('tr', null, h('th', null, y), rows.map((r) => { const x = (r.years || {})[y];
      return x == null ? h('td', { class: 'heat-empty' }) : h('td', { class: 'heat-c', style: `background:color-mix(in srgb, var(${x >= 0 ? '--good' : '--bad'}) ${Math.min(1, Math.abs(x) / cap) * 70 + 8}%, transparent)`, title: `${plain(x)} do capital` }, nf1.format(x)); }))))));
  const consist = card('Consistência por ano', 'Resultado de cada ano em % do capital: quem ganha sempre é mais confiável do que quem depende de um ano', years);
  return h('div', null, head, h('div', { style: 'height:12px' }), curves, h('div', { style: 'height:12px' }), h('div', { class: 'grid g2' }, scatter, consist), card('Métricas lado a lado', 'Destaque = melhor valor da linha (para queda máxima, o menor)', table));
}

/* ==================== Backtests & performance ==================== */
const bt = ui.bt = { hyp: 'all', stage: 'all', pair: 'all', origin: 'backtest' };
function btRuns() {
  const out = [];
  for (const hy of state.hypotheses) { if (hy.invalid || !visibleHy(hy)) continue; for (const c of hy.cells) { const a = c.analytics; if (!a) continue; out.push({ hy, c, a }); } }
  return out;
}
function pageBacktests() {
  if (['backtest', 'dryrun', 'real'].includes(route.q.origin)) bt.origin = route.q.origin;
  const tabs = h('div', { class: 'tabs2', role: 'tablist', 'aria-label': 'Origem dos resultados' }, [['backtest', 'Backtest'], ['dryrun', 'Dry-run'], ['real', 'Operações reais']].map(([k, t]) =>
    h('a', { href: `#/backtests?origin=${k}`, role: 'tab', class: 'tab' + (bt.origin === k ? ' on' : ''), 'aria-selected': bt.origin === k ? 'true' : 'false', 'data-fkey': 'bt-tab:' + k }, t)));
  const intro = h('div', { class: 'notice info', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'), h('div', null, h('b', null, 'Três origens, nunca misturadas. '), 'Backtest: histórico simulado pelo Freqtrade. Dry-run: bot em tempo real com carteira virtual. Real: ordens em corretora. Hoje só existe backtest.'));
  if (bt.origin === 'dryrun') return h('div', null, tabs, intro, h('div', { class: 'grid g2' }, walletCard(), forwardCard()));
  if (bt.origin === 'real') return h('div', null, tabs, intro, card('Operações reais', 'Corretora', emptyState('Nenhuma operação real.', 'O laboratório não tem chaves de corretora (a checagem de segurança exige isso) e roda somente em dry-run. Esta aba só terá dados se isso mudar de forma deliberada.')));
  let runs = btRuns();
  if (bt.hyp !== 'all') runs = runs.filter((r) => r.hy.id === bt.hyp);
  if (bt.stage !== 'all') runs = runs.filter((r) => r.c.split === bt.stage);
  if (bt.pair !== 'all') runs = runs.filter((r) => r.c.pair === bt.pair);
  const hyps = [...new Set(btRuns().map((r) => r.hy.id))];
  const filters = h('div', { class: 'filters toolbar' }, selectBox('Hipótese', 'bt-h', bt.hyp, [['all', 'Todas'], ...hyps.map((x) => [x, x])], (v) => { bt.hyp = v; render(); }),
    selectBox('Etapa', 'bt-s', bt.stage, [['all', 'Todas'], ['exploration', 'Exploração'], ['validation', 'Validação']], (v) => { bt.stage = v; render(); }),
    selectBox('Par', 'bt-p', bt.pair, [['all', 'Todos'], ...state.pairs.map((p) => [p, short(p)])], (v) => { bt.pair = v; render(); }));
  const cols = [
    { key: 'hy', label: 'Hipótese', val: (r) => r.hy.id, cell: (r) => h('a', { href: `#/strategy/${r.hy.id}?stage=${r.c.split}&pair=${r.c.pair}` }, h('b', null, r.hy.id), ' ', r.hy.family) },
    { key: 'pair', label: 'Par', val: (r) => r.c.pair, cell: (r) => pairTag(r.c.pair) },
    { key: 'stage', label: 'Etapa', val: (r) => r.c.split, cell: (r) => STAGE_CAP[r.c.split] },
    { key: 'period', label: 'Período testado', val: (r) => r.a.period ? r.a.period[0] : null, cell: (r) => r.a.period ? `${dayUtc(r.a.period[0])} a ${dayUtc(r.a.period[1])}` : dash },
    { key: 'start', label: 'Capital inicial', num: true, val: (r) => r.a.starting_balance, cell: (r) => nf2.format(r.a.starting_balance) },
    { key: 'end', label: 'Capital final', num: true, val: (r) => r.a.starting_balance + r.a.net_profit_abs, cell: (r) => nf2.format(r.a.starting_balance + r.a.net_profit_abs) },
    { key: 'net', label: 'Resultado líquido', num: true, val: (r) => r.a.net_profit_abs, cell: (r) => h('span', { class: tone(r.a.net_profit_abs) }, usd(r.a.net_profit_abs)) },
    { key: 'roi', label: 'ROI', num: true, val: (r) => r.a.roi_pct, cell: (r) => h('span', { class: tone(r.a.roi_pct) }, pct(r.a.roi_pct)) },
    { key: 'dd', label: 'Queda máx.', num: true, val: (r) => r.c.max_drawdown_pct, cell: (r) => plain(r.c.max_drawdown_pct) },
    { key: 'pf', label: 'Profit factor', num: true, val: (r) => r.a.profit_factor, cell: (r) => ok(r.a.profit_factor) ? nf2.format(r.a.profit_factor) : dash },
    { key: 'wr', label: 'Win rate', num: true, val: (r) => r.a.winrate, cell: (r) => winPct(r.a.winrate) },
    { key: 'sh', label: 'Sharpe', num: true, val: (r) => r.a.sharpe, cell: (r) => r2(r.a.sharpe) },
    { key: 'tr', label: 'Trades', num: true, val: (r) => r.a.trades, cell: (r) => nf0.format(r.a.trades) },
    { key: 'fee', label: 'Taxas (estim.)', num: true, val: (r) => r.a.fees_paid_abs, cell: (r) => ok(r.a.fees_paid_abs) ? nf2.format(r.a.fees_paid_abs) : dash },
    { key: 'dec', label: 'Gates', val: (r) => r.c.decision, cell: (r) => badge(DECISION[r.c.decision] || ST.info) },
    { key: 'go', label: '', val: null, cell: (r) => h('a', { href: `#/chart/${encodeURIComponent(r.c.experiment_id)}`, 'data-fkey': 'bt-tr:' + r.c.experiment_id }, 'Operações') },
  ];
  const table = runs.length ? dataTable({ id: 'bt-runs', cols: cols.map((c) => ({ ...c, nw: true })), rows: runs.map((r) => ({ ...r, key: r.c.experiment_id, label: r.c.experiment_id })), sort0: { key: 'start', dir: -1 }, label: 'Execuções de backtest' }) : emptyState('Nenhum backtest com esses filtros.');
  // versions of the same family, side by side
  const fam = {};
  for (const r of strat().filter((x) => x.stage === 'exploration')) (fam[r.family] = fam[r.family] || []).push(r);
  const multi = Object.entries(fam).filter(([, list]) => list.length > 1);
  const versions = card('Versões de uma mesma família', 'Hipóteses da mesma ideia, exploração, uma linha por versão', multi.length ? h('div', null, multi.map(([name, list]) => h('div', { style: 'margin-bottom:12px' }, h('div', { class: 'row' }, h('b', null, name), h('span', { class: 'sub' }, `${list.length} versões`)),
    h('div', { class: 'tablewrap' }, simpleTable(['Versão', 'ROI', 'Profit factor', 'Queda máx.', 'Trades', 'Evidência', 'Gates'], list.map((r) => [h('a', { href: `#/strategy/${r.id}` }, r.id), pct(r.roi_pct), ok(r.profit_factor) ? nf2.format(r.profit_factor) : dash, plain(r.max_dd_pct), nf0.format(r.trades), nf0.format(r.score), gateBadge(r)]), [1, 2, 3, 4, 5]))))) : emptyState('Nenhuma família tem mais de uma versão com resultado.'));
  const kp = h('div', { class: 'kpis' }, kpi('Backtests lidos', nf0.format(btRuns().length), 'hipótese × par × etapa, resultado atual'), kpi('Hipóteses', nf0.format(hyps.length), 'válidas, com resultado'), kpi('Origem', 'Backtest', 'simulado; nada foi enviado a uma corretora'));
  return h('div', null, tabs, intro, kp, card('Execuções de backtest', 'Custo base; clique em um cabeçalho para ordenar', h('div', null, filters, table), { id: 'sec-bt', cls: 'flush' }), h('div', { style: 'height:12px' }), versions);
}

/* ==================== Overview ==================== */
function systemTiles() {
  const s = state.safety, wd = worstData(), lc = lastCycle(), att = (state.attention || []).filter((a) => !a.resolved);
  const tile = (label, value, meta, note) => h('div', { class: 'tile' }, h('div', { class: 'lab' }, label), h('div', { class: 'val' }, badge(meta, value)), note ? h('div', { class: 'note' }, note) : null);
  return h('div', { class: 'tiles' },
    tile('Modo', s.dry_run ? 'Dry-run' : 'DRY-RUN DESLIGADO', s.dry_run ? ST.good : ST.bad, `${s.trading_mode || dash} · sem chaves: ${s.no_exchange_keys ? 'sim' : 'NÃO'}`),
    tile('Bot em tempo real', 'Parado', ST.na, 'nenhuma estratégia passou nos gates; o painel só lê arquivos'),
    tile('Banco de experimentos', state.database.found ? 'Encontrado' : 'Não encontrado', state.database.found ? ST.good : ST.bad, `${nf0.format(state.experiments.total)} experimentos`),
    tile('Dados de mercado', wd.value, wd.meta, wd.note),
    tile('Último ciclo', lc ? (cycleDone(lc) ? 'Completo' : 'Parou') : 'Nenhum', lc ? (cycleDone(lc) ? ST.good : ST.bad) : ST.na, lc ? whenShort(lc.started) : 'ainda não rodou'),
    tile('Alertas abertos', String(att.length), att.length ? (att.some((a) => a.level === 'critical') ? ST.bad : ST.warn) : ST.good, att.length ? 'veja em Sistema' : 'nada precisa de atenção'));
}
/* ---------- overview (v3 "Observatório"): bento grid, size = importance ---------- */
const REDUCED = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
/* count a number up to its final text once, when the page is entered (never on the 15 s refresh) */
function countUp(el, value, format) {
  queueMicrotask(() => {
    if (!ok(value) || REDUCED() || !els.page.classList.contains('enter')) return;
    const t0 = performance.now(), dur = 1100, final = el.textContent;
    const step = (t) => { const p = Math.min(1, (t - t0) / dur); el.textContent = p >= 1 ? final : format(value * (1 - Math.pow(2, -10 * p))); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
  return el;
}
function ring(score, size = 38) {
  const r = size / 2 - 4, c = 2 * Math.PI * r, t = tier(score), col = `var(--${t.cls === 'info' ? 'accent' : t.cls})`;
  return sv('svg', { class: 'ring', width: size, height: size, viewBox: `0 0 ${size} ${size}`, role: 'img', 'aria-label': `Evidência ${nf0.format(score)} de 100 (${t.label})` },
    sv('circle', { class: 'bgc', cx: size / 2, cy: size / 2, r }),
    sv('circle', { cx: size / 2, cy: size / 2, r, stroke: col, 'stroke-linecap': 'round', 'stroke-dasharray': `${(c * Math.max(2, score) / 100).toFixed(1)} ${c.toFixed(1)}`, transform: `rotate(-90 ${size / 2} ${size / 2})` }),
    sv('text', { x: size / 2, y: size / 2 + 4, 'text-anchor': 'middle' }, nf0.format(score)));
}
/* area sparkline for the featured card: drawn once the card has a width */
function heroArea(points, positive) {
  const box = h('div', { class: 'hero-plot' });
  if (!points || points.length < 2) return box;
  queueMicrotask(() => {
    const w = Math.max(240, box.clientWidth || 600), hgt = 128, pad = 6, col = positive ? 'var(--good)' : 'var(--bad)';
    const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), lo = Math.min(0, ...ys), hi = Math.max(0, ...ys), span = (hi - lo) || 1;
    const X = (v) => pad + (v - x0) / ((x1 - x0) || 1) * (w - pad * 2), Y = (v) => hgt - pad - (v - lo) / span * (hgt - pad * 2);
    const d = points.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join(''), last = points[points.length - 1];
    const gid = 'hg' + Math.random().toString(36).slice(2, 8);
    box.replaceChildren(sv('svg', { width: w, height: hgt, role: 'img', 'aria-label': `Lucro acumulado: ${plain(last[1])} do capital` },
      sv('defs', null, sv('linearGradient', { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 }, sv('stop', { offset: '0', 'stop-color': col, 'stop-opacity': 0.32 }), sv('stop', { offset: '1', 'stop-color': col, 'stop-opacity': 0 }))),
      sv('line', { x1: pad, x2: w - pad, y1: Y(0), y2: Y(0), class: 'spark-zero' }),
      sv('path', { d: `${d}L${X(last[0]).toFixed(1)} ${hgt}L${X(points[0][0]).toFixed(1)} ${hgt}Z`, fill: `url(#${gid})` }),
      sv('path', { d, class: 'ln', pathLength: 1, stroke: col, 'stroke-width': 2, 'stroke-linejoin': 'round' }),
      sv('circle', { cx: X(last[0]), cy: Y(last[1]), r: 9, fill: col, class: 'end-halo' }), sv('circle', { cx: X(last[0]), cy: Y(last[1]), r: 3.5, fill: col })));
  });
  return box;
}
function featuredCard(best, stage) {
  const lim = state.gate_bar.max_drawdown_pct, ddShare = ok(best.max_dd_pct) && lim ? Math.min(100, best.max_dd_pct / lim * 100) : 0;
  const ddTone = ddShare >= 100 ? 'bad' : ddShare >= 70 ? 'warn' : '';
  const roiEl = countUp(h('div', { class: 'hero-big ' + tone(best.roi_pct) }, pct(best.roi_pct)), best.roi_pct, pct);
  const cell = (label, value, note, cls = '', extra = null) => h('div', null, h('span', { class: 'l' }, label), h('span', { class: 'v ' + cls }, value), note ? h('span', { class: 'n' }, note) : null, extra);
  return h('section', { class: 'card hero beam b-7 b-r2', id: 'sec-destaque', 'aria-labelledby': 'ov-hero-t' },
    h('div', { class: 'chiprow' }, h('span', { class: 'badge accent' }, 'Em destaque · maior evidência'), gateBadge(best), h('span', { class: 'badge ' + tier(best.score).cls }, `Evidência ${nf0.format(best.score)} · ${tier(best.score).label}`), origin()),
    h('div', { class: 'hero-title' }, h('b', { id: 'ov-hero-t' }, best.id), h('span', { class: 'fam' }, best.family)),
    h('div', { class: 'hero-row' }, roiEl, h('div', { class: 'sub' }, h('div', null, 'ROI médio dos pares · ', STAGE_CAP[stage]), h('div', { class: 'num' }, periodText(best)))),
    h('div', { class: 'hstrip' },
      cell(term('winrate', 'Win rate'), winPct(best.winrate), best.winrate_ci ? `IC 95%: ${winPct(best.winrate_ci[0])} a ${winPct(best.winrate_ci[1])}` : null),
      cell(term('pf', 'Profit factor'), ok(best.profit_factor) ? nf2.format(best.profit_factor) : dash, best.profit_factor_note || (ok(best.profit_factor) ? `ganhos ${nf0.format(best.gross_profit_abs || 0)} / perdas ${nf0.format(Math.abs(best.gross_loss_abs || 0))} USDT` : null), ok(best.profit_factor) ? (best.profit_factor >= 1 ? 'pos' : 'neg') : ''),
      h('div', { title: `Queda máxima relativa calculada pelo Freqtrade, cenário de custo base, em cada par; mostra o pior par. Limite do gate: ${nf0.format(lim)}%.` },
        h('span', { class: 'l' }, 'Queda máxima'), h('span', { class: 'v' }, plain(best.max_dd_pct)), h('span', { class: 'n' }, `pior par · limite ${nf0.format(lim)}%`),
        h('div', { class: 'gauge ' + ddTone, role: 'img', 'aria-label': `${plain(best.max_dd_pct)} de ${nf0.format(lim)}% permitidos` }, h('i', { style: `width:${ddShare.toFixed(1)}%` }))),
      cell('Trades', nf0.format(best.trades), `mín. ${nf0.format(best.min_trades_pair)} por par`)),
    heroArea(best.curve, (best.roi_pct || 0) >= 0),
    flagList(best.flags.filter((f) => f.level !== 'info').slice(0, 3)),
    h('a', { class: 'open', href: `#/strategy/${best.id}?stage=${stage}`, 'data-fkey': 'ov-open' }, 'Abrir análise completa →'));
}
function funnelBento() {
  const f = Object.fromEntries(state.funnel.map((x) => [x.key, x.count])), top = Math.max(1, f[FUNNEL[0][0]] || 0);
  const passed = f.explore_passed || 0, read = f.validation_run || 0, waiting = Math.max(0, passed - read), approved = f.validation_passed || 0;
  const rows = FUNNEL.map(([k, label, def], i) => {
    const v = f[k] ?? 0, prev = i ? (f[FUNNEL[i - 1][0]] ?? 0) : null;
    return h('div', { class: 'fn-row', title: def },
      h('span', { class: 'lbl' }, label), h('span', { class: 'fn-bar' + (v ? '' : ' zero') }, v ? h('i', { style: `width:${(v / top * 100).toFixed(1)}%;animation-delay:${(i * 70)}ms` }) : null),
      h('span', { class: 'n' }, nf0.format(v), prev ? h('small', null, `${nf0.format(v / prev * 100)}%`) : null));
  });
  return h('section', { class: 'card b-5', id: 'sec-funil' }, h('header', null, h('div', null, h('h2', null, 'Funil de pesquisa'), h('div', { class: 'sub' }, 'Hipóteses válidas por etapa; à direita, a fração da etapa anterior.'))),
    h('div', { class: 'fn-sum' }, h('span', { class: 'badge info' }, `${nf0.format(passed)} passaram na exploração`), h('span', { class: 'badge warn' }, `${nf0.format(waiting)} aguardam validação`), h('span', { class: 'badge ' + (approved ? 'good' : 'na') }, `${nf0.format(approved)} de ${nf0.format(read)} aprovadas na validação`)),
    h('div', { class: 'fn', role: 'list', 'aria-label': 'Funil de pesquisa' }, rows),
    det('ov-funnel-rule', 'Como é contado', h('div', { class: 'sub' }, funnelRule())));
}
function healthBento() {
  const s = state.safety, wd = worstData(), lc = lastCycle(), open = openItems(), crit = criticalItems(), act = (state.activity || [])[0];
  const since = act ? (Date.now() - new Date(act.at).getTime()) / 1000 : null;
  const item = (cls, title, note, href, fkey) => h(href ? 'a' : 'div', { class: 'hi', href, 'data-fkey': fkey }, h('span', { class: 'hdot ' + cls, 'aria-hidden': 'true' }), h('div', null, h('b', null, title), h('span', null, note)));
  return h('section', { class: 'card b-5', id: 'sec-sistema' },
    h('header', null, h('div', null, h('h2', null, 'Sistema agora'), h('div', { class: 'sub' }, `gasto com agentes US$ ${nf2.format(state.agents.total_cost_usd || 0)}`)), h('a', { href: '#/data', 'data-fkey': 'ov-sys' }, 'Abrir Sistema →')),
    h('div', { class: 'health' },
      item(since != null && since < 1800 ? 'info' : 'na', since == null ? 'Sem atividade registrada' : `Última atividade há ${ago(since)}`, act ? `${act.kind === 'agent' ? `agente ${act.agent}` : act.kind === 'hypothesis' ? 'hipótese registrada' : act.kind === 'experiment' ? 'experimento' : act.kind === 'decision' ? 'decisão dos gates' : 'ciclo'}${act.hypothesis_id ? ` · ${act.hypothesis_id}` : ''}` : 'o feed aparece depois do primeiro ciclo', '#/data?at=sec-atividade', 'ov-h-act'),
      item(s.dry_run && s.no_exchange_keys ? 'good' : 'bad', s.dry_run ? `Dry-run · ${s.trading_mode || dash}` : 'Dry-run DESLIGADO', `sem chaves: ${s.no_exchange_keys ? 'sim' : 'NÃO'} · API ${s.api_disabled ? 'desligada' : 'LIGADA'}`, null),
      item(wd.meta.cls === 'good' ? 'good' : wd.meta.cls === 'warn' ? 'warn' : 'bad', `Dados: ${wd.value.toLowerCase()}`, wd.note, '#/data?at=sec-dados', 'ov-h-data'),
      item(lc ? (cycleDone(lc) ? 'good' : 'bad') : 'na', lc ? (cycleDone(lc) ? 'Último ciclo completo' : 'Último ciclo parou') : 'Nenhum ciclo ainda', lc ? whenShort(lc.started) : 'ainda não rodou', '#/data?at=sec-ciclos', 'ov-h-cyc'),
      item(crit.length ? 'bad' : open.length ? 'warn' : 'good', open.length ? `${nf0.format(open.length)} ${plural(open.length, 'alerta aberto', 'alertas abertos')}` : 'Nenhum alerta aberto', crit.length ? `${nf0.format(crit.length)} ${plural(crit.length, 'crítico', 'críticos')}` : 'nada exige atenção', '#/data?at=sec-alertas', 'ov-h-att'),
      item('good', usdt(state.wallet), 'carteira virtual · sem posições abertas', '#/dryrun', 'ov-h-wallet')));
}
function rankBento(rows, stage) {
  const head = h('div', { class: 'rk-row rk-head', 'aria-hidden': 'true' }, h('span', null, '#'), h('span', null, 'Evid.'), h('span', null, 'Estratégia'), h('span', { class: 'v' }, 'ROI'), h('span', { class: 'v c-wr' }, 'Win rate'), h('span', { class: 'v c-pf' }, 'PF'), h('span', { class: 'v c-dd' }, 'Queda'), h('span', { class: 'c-sp' }, 'Curva'));
  const list = rows.map((r, i) => h('a', { class: 'rk-row', href: `#/strategy/${r.id}?stage=${stage}`, 'data-fkey': 'ov-rk:' + r.id, 'aria-label': `${i + 1}º ${r.id}, evidência ${nf0.format(r.score)}, ROI ${pct(r.roi_pct)}` },
    h('span', { class: 'pos-n' }, String(i + 1)), ring(r.score), h('span', { class: 'nm' }, h('b', null, r.id), h('span', null, r.family)),
    h('span', { class: 'v ' + tone(r.roi_pct) }, pct(r.roi_pct)), h('span', { class: 'v c-wr' }, winPct(r.winrate)), h('span', { class: 'v c-pf' }, ok(r.profit_factor) ? nf2.format(r.profit_factor) : dash), h('span', { class: 'v c-dd' }, plain(r.max_dd_pct)), h('span', { class: 'c-sp' }, spark(r.curve, 96, 28))));
  const n = hiddenCount();
  return h('section', { class: 'card b-7', id: 'sec-top' }, h('header', null, h('div', null, h('h2', null, 'Ranking por evidência'), h('div', { class: 'sub' }, `${STAGE_CAP[stage]} · evidência 0 a 100, não é win rate`)), h('a', { href: `#/leaderboard?stage=${stage}`, 'data-fkey': 'ov-rank' }, 'Abrir o ranking completo →')),
    h('div', { class: 'rk' }, head, list),
    n ? h('div', { class: 'rk-foot' }, h('span', null, `${nf0.format(n)} ${plural(n, 'hipótese arquivada', 'hipóteses arquivadas')} (reprovadas, descartadas ou inválidas) fora desta visão: ficam só no arquivo, para consulta dos agentes.`)) : null);
}
function yearsBento(rows) {
  const years = [...new Set(rows.flatMap((r) => Object.keys(r.years || {})))].sort();
  if (!years.length) return null;
  const vals = rows.flatMap((r) => Object.values(r.years || {}).map(Math.abs)).sort((a, b) => a - b), cap = vals[Math.floor(vals.length * 0.9)] || vals[vals.length - 1] || 1;
  const grid = h('div', { class: 'yh', role: 'table', 'aria-label': 'Resultado por ano, % do capital', style: `grid-template-columns:52px repeat(${years.length}, minmax(0, 1fr))` },
    h('span', { role: 'columnheader' }), years.map((y) => h('span', { class: 'yl', role: 'columnheader' }, `'${y.slice(2)}`)),
    rows.map((r) => [h('a', { class: 'sl', role: 'rowheader', href: `#/strategy/${r.id}` }, r.id), years.map((y) => {
      const v = (r.years || {})[y];
      if (!ok(v)) return h('span', { class: 'cell na', role: 'cell', title: `${r.id} · ${y}: sem trades` });
      const k = Math.min(1, Math.abs(v) / cap);
      return h('span', { class: 'cell', role: 'cell', title: `${r.id} · ${y}: ${plain(v)} do capital`, style: `background:color-mix(in srgb, var(${v >= 0 ? '--good-fill' : '--bad-fill'}, var(${v >= 0 ? '--good' : '--bad'})) ${Math.round(12 + k * 68)}%, var(--track))` }, sgn((v >= 0 ? '+' : '') + nf0.format(v)));
    })]));
  return h('section', { class: 'card b-5', id: 'sec-anos' }, h('header', null, h('div', null, h('h2', null, 'Resultado por ano'), h('div', { class: 'sub' }, '% do capital somado dos pares · backtest'))),
    grid, h('div', { class: 'yh-scale', 'aria-hidden': 'true' }, h('span', null, sgn('-' + nf0.format(cap)) + '%'), h('i'), h('span', null, '+' + nf0.format(cap) + '%')));
}
function pageOverviewPortal() {
  const stage = lb.stage;
  const rows = sRows(stage), best = rows.length ? (rows.filter(eligible).sort((a, b) => b.score - a.score)[0] || topRow(stage)) : null;
  const stageSwitch = h('div', { class: 'filters toolbar' }, segmented('Etapa', 'ov-stage', stage, [['exploration', 'Exploração'], ['validation', 'Validação']], (v) => { lb.stage = v; render(); }), h('span', { class: 'sub' }, `${rows.length} ${plural(rows.length, 'estratégia', 'estratégias')} com resultado`));
  const parts = summaryParts(), notes = parts.filter((p) => !p.startsWith('Atenção'));
  const head = h('div', { class: 'ob-head' }, h('section', { 'aria-label': 'Resumo' }, h('p', { class: 'lead' }, notes[0]), h('p', { class: 'next' }, h('b', null, 'Próximo passo: '), nextStep())), stageSwitch);
  if (!best) return h('div', null, head, emptyState('Nenhuma estratégia com resultado nesta etapa.', 'O resumo aparece quando houver backtests concluídos.'), h('div', { style: 'height:12px' }), h('div', { class: 'bento' }, funnelBento(), healthBento()));
  const topN = rows.slice().sort((a, b) => b.score - a.score).slice(0, 5);
  const evol = chartCard({ id: 'ov-evol', title: 'Evolução do lucro acumulado', sim: true, subtitle: `As ${topN.length} de maior evidência · ${STAGE_CAP[stage]} · % do capital · passe o mouse para comparar no tempo`, legend: topN.map((r, i) => ({ name: r.id, color: `var(--s${i + 1})` })), hasData: topN.some((r) => r.curve && r.curve.length > 1),
    draw: (el, w) => lineChart(el, { series: topN.map((r, i) => ({ name: r.id, color: `var(--s${i + 1})`, points: r.curve || [] })), width: w, height: 320, zero: true, area: true, yLabel: 'Lucro acumulado em % do capital', fmtY: (val, t) => (t ? pct(val) : sgn(nfv.format(val)) + '%') }),
    table: { head: ['Estratégia', 'Lucro acumulado final'], rows: topN.map((r) => [r.id, pct(r.curve && r.curve.length ? r.curve[r.curve.length - 1][1] : null)]), numCols: [1] } });
  evol.classList.add('b-12');
  const answers = answersCard(stage), since = sinceCard();
  answers.classList.add('b-6'); since.classList.add('b-6');
  const alerts = alertPanel(state.attention || []), feed = activityFeed(8);
  alerts.classList.add('b-7'); feed.classList.add('b-5');
  return h('div', null, head,
    h('div', { class: 'bento' }, featuredCard(best, stage), funnelBento(), healthBento(), evol, rankBento(topN, stage), yearsBento(topN), alerts, feed, answers, since));
}

/* ==================== System monitor ==================== */
function pageSystem() {
  const list = state.attention || [];
  return h('div', null, systemTiles(), h('div', { style: 'height:12px' }), safetyStrip(), alertPanel(list, { id: 'sec-alertas', title: 'Erros e alertas' }), h('div', { style: 'height:12px' }),
    h('div', { class: 'grid g2' }, infraCard(), activityFeed(14)), dataTableCard(), h('div', { style: 'height:12px' }), h('div', { class: 'grid g2' }, periodsCard(), cyclesCard()), sectionTitle('Custo do laboratório'), h('div', { class: 'grid g3' }, ...spendCharts()));
}

/* ==================== command palette (Ctrl/Cmd+K): go to a page or a strategy ==================== */
const palette = { el: null, input: null, list: null, items: [], idx: 0 };
function paletteItems(q) {
  const pages = ROUTES.filter((r) => !r.hidden).map((r) => ({ label: r.title, hint: r.ctx, hash: '#/' + r.id }));
  const ids = sIds().map((id) => ({ label: id, hint: `Estratégia · ${(hypById(id) || {}).family || ''}`, hash: `#/strategy/${id}` }));
  const ixd = typeof ixData === 'function' ? (state.indices || (typeof IX !== 'undefined' ? IX.data : null)) : null;
  const ixRules = ixd ? (ixd.rules || []).map((r) => ({ label: r.id, hint: `Índices · ${r.title || r.name || ''}`, hash: `#/indices-regra/${r.id}` })) : [];
  const all = [...pages, ...ids, ...ixRules], s = q.trim().toLowerCase();
  return (s ? all.filter((x) => (x.label + ' ' + x.hint).toLowerCase().includes(s)) : all).slice(0, 12);
}
function paletteRender() {
  palette.items = paletteItems(palette.input.value);
  palette.idx = Math.min(palette.idx, Math.max(0, palette.items.length - 1));
  palette.list.replaceChildren(...(palette.items.length ? palette.items.map((it, i) => h('li', { role: 'option', 'aria-selected': i === palette.idx ? 'true' : 'false', class: i === palette.idx ? 'on' : '', onclick: () => paletteGo(it), onmousemove: () => { palette.idx = i; paletteRender(); } }, h('b', null, it.label), h('span', null, it.hint))) : [h('li', { class: 'none' }, 'Nada encontrado')]));
}
function paletteGo(it) { if (!it) return; paletteClose(); go(it.hash); }
function paletteClose() { if (palette.el) palette.el.hidden = true; }
function paletteOpen() {
  if (!palette.el) {
    palette.input = h('input', { type: 'text', placeholder: 'Ir para… página ou estratégia', 'aria-label': 'Buscar página ou estratégia', oninput: () => { palette.idx = 0; paletteRender(); },
      onkeydown: (e) => { if (e.key === 'ArrowDown') { e.preventDefault(); palette.idx = Math.min(palette.items.length - 1, palette.idx + 1); paletteRender(); } else if (e.key === 'ArrowUp') { e.preventDefault(); palette.idx = Math.max(0, palette.idx - 1); paletteRender(); } else if (e.key === 'Enter') { e.preventDefault(); paletteGo(palette.items[palette.idx]); } else if (e.key === 'Escape') paletteClose(); } });
    palette.list = h('ul', { role: 'listbox', 'aria-label': 'Resultados' });
    palette.el = h('div', { class: 'palette', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Busca rápida', hidden: true, onclick: (e) => { if (e.target === palette.el) paletteClose(); } }, h('div', { class: 'palette-box' }, palette.input, palette.list, h('div', { class: 'palette-foot' }, '↑↓ navegar · Enter abrir · Esc fechar')));
    document.body.append(palette.el);
  }
  palette.el.hidden = false; palette.input.value = ''; palette.idx = 0; paletteRender(); palette.input.focus();
}
addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); paletteOpen(); } });

/* ==================== Dry-run (evidence collection) and idea intake ==================== */
function pageDryrun() {
  const ft = state.forward_test || {}, hy = ft.hypotheses || [], intake = ft.intake || {};
  const p3 = (v) => (v == null ? dash : (v * 100).toFixed(3) + '%');
  const mins = (v) => (v == null ? dash : v.toFixed(1) + ' min');
  const states = [['new', 'Coletadas'], ['triaged', 'Triadas'], ['queued', 'Na fila'], ['registered', 'Registradas'], ['dropped', 'Descartadas']];
  const intakeTotal = states.reduce((a, [k]) => a + (intake[k] || 0), 0);
  const intakeCard = card('Esteira de ideias', 'Coleta (scout) e triagem; nada aqui é resultado de backtest.', intakeTotal
    ? h('div', { class: 'rx-stack' }, h('ol', { class: 'dl-flow' }, states.map(([k, t], i) => h('li', { style: `--i:${i}` }, h('b', null, nf0.format(intake[k] || 0)), h('span', null, t)))),
      h('p', { class: 'sub' }, 'O scout coleta ideias descritas em texto; a triagem tira repetidas e inviáveis; as da fila viram hipóteses registradas, com a regra escrita antes de qualquer backtest.'))
    : emptyState('Nenhuma ideia coletada ainda.', 'O scout roda no ciclo semanal.'), { cls: 'b-5' });
  const label = hy.length ? hy[0].label : 'Dry-run como coleta de evidência: NÃO validada; não é aprovação, não é holdout.';
  const banner = h('div', { class: 'notice info', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'), h('div', null, h('b', null, 'Aviso: '), label, ' Esta seção mostra só a qualidade de execução; a avaliação formal é o holdout (a partir de 2027-04-21).'));
  if (!hy.length) return h('div', { class: 'rx-stack' }, banner, emptyState('Nenhuma estratégia congelada para dry-run.', 'Aprove com approve.py --stage dryrun e congele com forward_freeze.py.'), h('div', { class: 'bento' }, intakeCard));
  const tag = (id) => (typeof dlBotTag === 'function' ? dlBotTag(id) : h('b', null, id));
  const freeze = card('Congelamento', 'O arquivo da estratégia não pode mudar durante a coleta; se mudar, a evidência deixa de valer.',
    h('ul', { class: 'dl-freeze' }, hy.map((x) => { const total = Object.values(x.pairs).reduce((a, q) => a + (q.trades || 0), 0);
      return h('li', null, tag(x.id), badge(x.freeze_ok ? ST.good : ST.bad, x.freeze_ok ? 'Íntegro' : 'ARQUIVO ALTERADO'),
        h('small', null, `desde ${x.frozen_at ? x.frozen_at.slice(0, 16).replace('T', ' ') : dash} UTC · commit `, h('code', null, String(x.commit || dash).slice(0, 10)), ` · ${nf0.format(total)} trades`),
        x.problems.length ? h('pre', null, x.problems.join(String.fromCharCode(10))) : null); })), { cls: 'b-7' });
  const rows = hy.flatMap((x) => Object.entries(x.pairs).map(([pair, q]) => q.error ? [tag(x.id), pair, h('span', { class: 'neg' }, q.error), '', '', '', '', '']
    : [tag(x.id), pair, `${nf0.format(q.open)} / ${nf0.format(q.closed)}`, `${nf0.format(q.entry_orders_not_filled)} de ${nf0.format(q.entry_orders)}`,
      p3(q.entry_slippage_mean), p3(q.exit_slippage_mean), mins(q.fill_latency_minutes_mean), h('span', null, p3(q.observed_entry_cost_per_side_mean), h('small', { class: 'muted' }, ` assumido ${p3(q.assumed_cost_per_side)}`))]));
  const anyTrade = hy.some((x) => Object.values(x.pairs).some((q) => q.trades));
  const exec = card('Execução por robô e ativo', anyTrade ? 'Slippage é a diferença entre o preço pedido e o preço obtido; latência é o tempo até a ordem ser preenchida.' : 'Sem trades ainda: as colunas enchem conforme os robôs operam. Estratégias lentas levam dias entre um trade e outro.',
    h('div', { class: 'tablewrap' }, simpleTable(['Estratégia', 'Par', 'Abertos / fechados', 'Entradas não preenchidas', 'Slippage entrada', 'Slippage saída', 'Latência', 'Custo observado'], rows, [2, 3, 4, 5, 6, 7])), { cls: 'b-12' });
  return h('div', { class: 'rx-stack' }, banner, h('div', { class: 'bento' }, freeze, intakeCard, exec));
}
