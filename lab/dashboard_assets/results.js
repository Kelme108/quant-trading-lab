/* ==================== Resultados (portal v4): Início, Ranking, Operações, Comparar, Estratégia ====================
   Inlined into the page's script by lab.dashboard.render_page (after portal.js), so it shares the page helpers
   (h, sv, term, card, dataTable, badge, showTip, ...), the state and the CSP nonce. Strings only become text nodes.

   Design (owner's request 2026-11-08, research in the conversation log): one site for both readers. Each page opens
   with its conclusion in one plain sentence, then numbers, then tables that sort, then the technical detail.
   - Every valid strategy with results is listed, approved or not, with its status in a badge (state.strategies).
   - Win rate is never shown alone: always beside payoff and return.
   - Every technical word explains itself (term()).
   - Operations come from state.trade_index, fetched once from /api/trade-index (embedded in a static export).
   Origin of every number here: BACKTEST (simulated), base cost scenario, unless the label says otherwise. */

const rx = ui.rx = {
  rank: { stage: 'exploration', view: 'all', status: 'all', tf: 'all', pair: 'all', q: '', sample: false, mode: 'cards', csort: 'roi' },
  ops: { stage: 'exploration', hyp: 'all', pair: 'all', tf: 'all', res: 'all', reason: 'all', dow: 'all', hour: 'all', dur: 'all', group: 'hyp', metric: 'wr', page: 0, sort: { key: 'sum', dir: -1 }, calYear: null },
  cmp: { ids: null, stage: 'exploration' }, st: { stage: null }, sel: [],
};

/* ---------- vocabulary of this module ---------- */
function rxTerms() {
  return {
    rx_payoff: ['Payoff', 'Ganho médio dividido pela perda média. Payoff 2 quer dizer: quando ganha, ganha o dobro do que perde quando perde. Com payoff alto, a estratégia pode acertar pouco e ainda lucrar.'],
    rx_wr: ['Win rate (taxa de acerto)', 'De cada 100 operações, quantas fecharam no lucro. Sozinho engana: dá para acertar 40 de cada 100 e ganhar muito, se os ganhos forem bem maiores que as perdas (veja o payoff).'],
    rx_ret: ['Retorno médio por ativo', 'Quanto o capital de cada criptomoeda testada cresceu ou caiu no período, na média dos ativos, já com taxas no cenário base.'],
    rx_stress: ['Com custo alto', 'O mesmo retorno refeito com taxas e escorregamento de preço bem piores que o normal (cenário de estresse). Se continua positivo, a estratégia aguenta custos reais.'],
    rx_dd: ['Pior queda (drawdown)', 'A maior queda do capital, do pico até o fundo seguinte, em algum momento do teste. Mede o susto que você teria passado.'],
    rx_risk: ['Risco de 1 a 10', 'Escala simples feita a partir da pior queda: 1 a 3 é risco baixo (queda abaixo de 15%), 4 a 6 é médio (15% a 30%), 7 a 10 é alto (acima de 30%). O limite do laboratório é 25%, o que fica entre 5 e 6.'],
    rx_score: ['Nota de evidência (0 a 100)', 'Resumo de quatro notas: lucro (inclui aguentar custo alto), risco (queda e retorno sobre a queda), amostra (operações por ativo) e consistência (ativos e anos positivos, lucro sem o melhor trade). Fica limitada a 40 com amostra pequena e a 60 se algum critério reprovou. Nenhuma nota isolada decide.'],
    rx_trades: ['Operações', 'Compras e vendas completas no período. Menos de 30 por ativo é amostra pequena demais para confiar.'],
    rx_pairs: ['Ativos positivos', 'Em quantas das criptomoedas testadas a estratégia terminou no lucro. Funcionar em vários ativos é sinal de regra robusta, não de sorte.'],
    rx_avg: ['Média por operação', 'Resultado médio de cada operação, em % do valor aplicado nela, já descontadas as taxas.'],
    rx_sum: ['Resultado somado', 'Soma dos resultados das operações, em % do capital do backtest de cada ativo. Como cada backtest começa com o mesmo capital, dá para comparar estratégias e grupos.'],
    rx_explo: ['Exploração', 'Primeira prova: dados de 2017 a jul/2024. É onde a ideia é testada pela primeira vez.'],
    rx_valid: ['Validação', 'Segunda prova, com dados recentes (jul/2024 a out/2026) que a ideia nunca viu. É lida uma única vez, para ninguém ajustar a regra olhando o resultado.'],
    rx_drop: ['Da exploração para a validação', 'Quanto o retorno mudou dos dados antigos para os dados novos. Uma queda grande é o sinal clássico de que a regra foi ajustada demais ao passado (overfitting).'],
    rx_bh: ['Comprar e segurar', 'Quanto teria rendido só comprar o ativo no início do período e não fazer nada. Serve de régua: em alta forte, quase toda estratégia perde para isso.'],
    rx_underwater: ['Queda desde o pico', 'Quanto o capital estava abaixo do seu ponto mais alto em cada momento. Zero quer dizer que estava no topo; quanto mais fundo, maior o susto.'],
    rx_annual: ['Retorno por ano', 'O retorno total convertido em uma taxa por ano, com juros compostos. As duas provas têm durações diferentes (a exploração tem uns 7 anos; a validação, uns 2), então o total não se compara direto; a taxa por ano, sim.'],
    rx_hour: ['Horário de Brasília', 'Dias e horas das entradas no horário de Brasília (UTC−3). Ajuda a ver em que momentos do dia a estratégia funciona melhor, o que importa muito para day trade.'],
  };
}

/* ---------- data access ---------- */
const rxHyps = () => state.allHypotheses || state.hypotheses;
const rxHy = (id) => rxHyps().find((x) => x.id === id);
const rxRows = (stage) => (state.strategies || []).filter((r) => r.stage === stage);
const rxRow = (id, stage) => (state.strategies || []).find((r) => r.id === id && r.stage === stage);
const rxMin = () => (state.gate_bar && state.gate_bar.minimum_trades) || 30;
const rxGo = (hash) => { location.hash = hash; };
const RX_STAGE = { exploration: 'Exploração', validation: 'Validação' };
const RX_PERIOD = { exploration: '2017 a jul/2024', validation: 'jul/2024 a out/2026' };
const humanName = (family) => String(family || '').replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/([A-Z])([A-Z][a-z])/g, '$1 $2');
function tfOf(hy) {
  const m = /\b(15m|5m|1h|4h|1d)\b|(\d+)-minute|\bhourly\b|\bdaily\b/i.exec((hy && hy.rule) || '');
  if (!m) return null;
  const s = m[0].toLowerCase();
  return s === 'hourly' ? '1h' : s === 'daily' ? '1d' : /^\d+-minute$/.test(s) ? m[2] + 'm' : s;
}
const RX_PAIRS = ['var(--btc)', 'var(--eth)', 'var(--bnb)', 'var(--s4)', 'var(--s5)', 'var(--s6)', 'var(--s2)', 'var(--s3)', 'var(--s1)'];
const rxPairColor = (pair) => RX_PAIRS[Math.max(0, (state.pairs || []).indexOf(pair)) % RX_PAIRS.length];
const rxSeries = (i) => ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s6)'][i % 6];

/* status in plain words (the registry text stays in the tooltip) */
const RXS = {
  validada: { icon: '✓', cls: 'good', label: 'Aprovada na validação', why: 'Passou nas duas provas: dados antigos e dados recentes.' },
  val_reprovada: { icon: '!', cls: 'warn', label: 'Reprovada na validação', why: 'Foi bem nos dados de 2017 a 2024, mas não repetiu o resultado nos dados recentes.' },
  exp_aprovada: { icon: '✓', cls: 'info', label: 'Aprovada na exploração', why: 'Passou nos dados de 2017 a 2024; falta a prova nos dados recentes.' },
  exp_reprovada: { icon: '✕', cls: 'bad', label: 'Reprovada na exploração', why: 'Não atingiu os critérios mínimos já na primeira prova.' },
  inconclusiva: { icon: '?', cls: 'na', label: 'Inconclusiva', why: 'Sem evidência suficiente para aprovar nem para reprovar.' },
  descartada: { icon: '–', cls: 'na', label: 'Descartada antes do teste', why: 'Barrada antes do backtest completo: poucas operações, risco alto demais ou erro na regra.' },
  referencia: { icon: '–', cls: 'na', label: 'Referência', why: 'Estratégia-base usada para comparar as outras.' },
};
function statusKey(status) {
  const s = String(status || '');
  if (/^frozen reference/.test(s)) return 'referencia';
  if (/^validation: candidate/.test(s)) return 'validada';
  if (/not approved at validation|validation: mixed/.test(s)) return 'val_reprovada';
  if (/exploration: candidate|candidate at exploration/.test(s)) return 'exp_aprovada';
  if (/inconclusive/.test(s)) return 'inconclusiva';
  if (/rejected/.test(s)) return 'exp_reprovada';
  return 'descartada';
}
const statusBadge = (status) => { const m = RXS[statusKey(status)]; return h('span', { title: m.why + ' (registro: ' + status + ')' }, badge(m)); };
const dryBadge = () => h('span', { title: 'Rodando ao vivo com dinheiro simulado' }, badge({ icon: '●', cls: 'info', label: 'Em dry-run' }));
const DROP = [
  [/fewer than 30 trades/, 'Operou pouco demais (menos de 30 operações)'], [/exposure below/, 'Risco alto demais para o tamanho mínimo de posição'],
  [/causality/, 'Olhava o futuro sem querer (falha de causalidade)'], [/rejected at exploration|rejected \(family\)/, 'Reprovada nos critérios da exploração'],
  [/not approved at validation/, 'Não repetiu o resultado na validação'], [/^invalid/, 'Código não seguia a regra registrada'], [/failed/, 'Falhou na implementação ou na calibração'],
];
const dropReason = (s) => (DROP.find(([re]) => re.test(String(s))) || [0, 'Ainda não testada'])[1];

/* risk 1..10 from the worst drawdown; bands 1-3 low, 4-6 medium, 7-10 high */
const RISK_EDGES = [5, 10, 15, 20, 25, 30, 40, 50, 65];
const riskOf = (dd) => ok(dd) ? 1 + RISK_EDGES.filter((e) => dd >= e).length : null;
function riskBadge(dd) {
  const r = riskOf(dd);
  if (r == null) return dash;
  const cls = r <= 3 ? 'good' : r <= 6 ? 'warn' : 'bad', band = r <= 3 ? 'baixo' : r <= 6 ? 'médio' : 'alto';
  return h('span', { class: 'rx-risk ' + cls, title: `Risco ${r} de 10 (${band}): pior queda de ${nf1.format(dd)}%` }, h('b', null, String(r)), h('small', null, band));
}

/* ---------- formatting ---------- */
const wr = (v) => ok(v) ? nf1.format(v * 100) + '%' : dash;
const sp = (v, d = 1) => ok(v) ? (v > 0 ? '+' : '') + sgn((d === 2 ? nf2 : nf1).format(v)) + '%' : dash;
const toneOf = (v) => !ok(v) || v === 0 ? '' : v > 0 ? 'pos' : 'neg';
const signedSpan = (v, d = 1, bold = false) => h(bold ? 'b' : 'span', { class: toneOf(v) }, sp(v, d));
const ddText = (v) => ok(v) ? sgn('-' + nf1.format(v)) + '%' : dash;
const n2 = (v) => ok(v) ? sgn(nf2.format(v)) : dash;
const durText = (m) => !ok(m) ? dash : m < 60 ? `${nf0.format(m)} min` : m < 2880 ? `${nf1.format(m / 60)} h` : `${nf1.format(m / 1440)} d`;
const nameCell = (r, hy) => h('div', { class: 'rx-name' }, h('a', { href: '#/strategy/' + encodeURIComponent(r.id), 'data-fkey': 'rxn:' + r.id + ':' + r.stage }, r.id), h('span', null, humanName(r.family)),
  h('small', null, [tfOf(hy) || '?', `${r.n_pairs} ${plural(r.n_pairs, 'ativo', 'ativos')}`].join(' · ')));

/* ---------- small charts (drawn to scale, colors from the theme tokens) ---------- */
function rxSpark(points, w = 112, hgt = 28) {
  if (!points || points.length < 2) return h('span', { class: 'sub' }, dash);
  const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(0, ...ys), y1 = Math.max(0, ...ys);
  const X = (x) => 2 + (x - x0) / ((x1 - x0) || 1) * (w - 4), Y = (y) => hgt - 3 - (y - y0) / ((y1 - y0) || 1) * (hgt - 6);
  const end = ys[ys.length - 1], col = end >= 0 ? 'var(--good)' : 'var(--bad)';
  return sv('svg', { width: w, height: hgt, viewBox: `0 0 ${w} ${hgt}`, 'aria-hidden': 'true', class: 'rx-spark' },
    sv('line', { x1: 2, x2: w - 2, y1: Y(0), y2: Y(0), stroke: 'var(--line2)' }),
    sv('path', { d: points.map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)).join(''), fill: 'none', stroke: col, 'stroke-width': 1.5 }),
    sv('circle', { cx: X(xs[xs.length - 1]), cy: Y(end), r: 2.2, fill: col }));
}
function niceTicks(a, b, n = 5) {
  const span = (b - a) || 1, raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) || mag * 10, out = [];
  for (let v = Math.ceil(a / step) * step; v <= b + step * 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}
const yearOf = (ms) => new Date(ms).getUTCFullYear();
/* line chart over time; series: [{label, color, pts: [[epoch_ms, value]]}]; area: fill below zero (underwater) */
function rxLine(series, { height = 260, yfmt = (v) => nf0.format(v) + '%', area = false, fill = false, label = 'Gráfico de linha' } = {}) {
  const pts = series.flatMap((s) => s.pts);
  if (pts.length < 2) return emptyState('Sem pontos suficientes para o gráfico.');
  const W = 820, L = 52, R = 14, T = 10, B = 26;
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), ticks = niceTicks(Math.min(0, ...ys), Math.max(0, ...ys));
  const y0 = Math.min(ticks[0], ...ys), y1 = Math.max(ticks[ticks.length - 1], ...ys);
  const X = (x) => L + (x - x0) / ((x1 - x0) || 1) * (W - L - R), Y = (y) => T + (1 - (y - y0) / ((y1 - y0) || 1)) * (height - T - B);
  const svg = sv('svg', { viewBox: `0 0 ${W} ${height}`, width: '100%', role: 'img', 'aria-label': label, class: 'rx-chart' });
  for (const v of ticks) svg.append(sv('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), stroke: v === 0 ? 'var(--line2)' : 'var(--line)' }), sv('text', { x: L - 6, y: Y(v) + 4, 'text-anchor': 'end' }, yfmt(v)));
  const ya = yearOf(x0), yb = yearOf(x1), every = Math.max(1, Math.ceil((yb - ya) / 8));
  for (let y = ya + 1; y <= yb; y++) { if ((y - ya) % every) continue; const x = X(Date.UTC(y, 0, 1)); svg.append(sv('line', { x1: x, x2: x, y1: T, y2: height - B, stroke: 'var(--line)', 'stroke-dasharray': '2 4' }), sv('text', { x, y: height - 8, 'text-anchor': 'middle' }, String(y))); }
  for (const s of series) {
    if (s.pts.length < 2) continue;
    const d = s.pts.map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)).join('');
    const xa = X(s.pts[0][0]).toFixed(1), xb = X(s.pts[s.pts.length - 1][0]).toFixed(1);
    if (area) svg.append(sv('path', { class: 'ar', d: d + `L${xb} ${Y(0)}L${xa} ${Y(0)}Z`, fill: s.color, 'fill-opacity': 0.18, stroke: 'none' }));
    else if (fill && series.length === 1) { const id = rxGid(); svg.append(sv('defs', null, gradDef(id, s.color, 0.3)), sv('path', { class: 'ar', d: d + `L${xb} ${height - B}L${xa} ${height - B}Z`, fill: `url(#${id})` })); }
    svg.append(sv('path', { class: 'ln', d, fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', pathLength: 1 }));
    const e = s.pts[s.pts.length - 1];
    if (series.length === 1) svg.append(sv('circle', { class: 'rx-halo', cx: X(e[0]), cy: Y(e[1]), r: 4, fill: s.color }));
    svg.append(sv('circle', { cx: X(e[0]), cy: Y(e[1]), r: 4, fill: s.color, stroke: 'var(--solid, var(--panel))', 'stroke-width': 2 }));
  }
  const cursor = sv('line', { x1: 0, x2: 0, y1: T, y2: height - B, stroke: 'var(--muted)', 'stroke-dasharray': '3 3', visibility: 'hidden' });
  svg.append(cursor, sv('rect', { x: L, y: T, width: W - L - R, height: height - T - B, fill: 'transparent',
    onmousemove: (e) => {
      const box = svg.getBoundingClientRect(), xv = x0 + ((e.clientX - box.left) / box.width * W - L) / (W - L - R) * (x1 - x0);
      cursor.setAttribute('x1', X(xv)); cursor.setAttribute('x2', X(xv)); cursor.setAttribute('visibility', 'visible');
      const rows = series.map((s) => { let best = null; for (const p of s.pts) { if (p[0] <= xv) best = p; else break; } return best ? { color: s.color, value: yfmt(best[1]), label: ' ' + s.label } : null; }).filter(Boolean);
      showTip(e, dayUtc(new Date(xv).toISOString()), rows);
    }, onmouseleave: () => { cursor.setAttribute('visibility', 'hidden'); hideTip(); } }));
  return svg;
}
/* drawdown from a cumulative % curve (profit in % of the starting capital) */
const underwater = (curve) => { let peak = 100; return (curve || []).map(([t, v]) => { const eq = 100 + v; peak = Math.max(peak, eq); return [t, (eq / peak - 1) * 100]; }); };
function hbars(items, fmt = (v) => nf0.format(v)) {
  const m = Math.max(1e-9, ...items.map((x) => Math.abs(x.v || 0)));
  return h('div', { class: 'rx-hbars' }, items.map((x) => h('div', { class: 'rx-hb' }, h('span', { class: 'l' }, x.label),
    h('span', { class: 't' }, h('i', { style: `width:${(Math.abs(x.v || 0) / m * 100).toFixed(1)}%;background:${x.color || 'var(--accent)'}` })), h('span', { class: 'v ' + (x.tone || '') }, fmt(x.v)))));
}
/* fills use --good-fill / --bad-fill: deeper than the line colours in the dark theme, so the text on them keeps 4.5:1 */
const FILL_GOOD = 'var(--good-fill, var(--good))', FILL_BAD = 'var(--bad-fill, var(--bad))';
const heatBg = (v, scale = 60) => !ok(v) ? 'transparent' : `color-mix(in srgb, ${v >= 0 ? FILL_GOOD : FILL_BAD} ${Math.round(Math.min(1, Math.abs(v) / scale) * 52 + 6)}%, transparent)`;
/* opaque version for tiles and calendar cells (text sits on it) */
const heatSolid = (v, scale = 60) => !ok(v) ? 'var(--panel2)' : `color-mix(in srgb, ${v >= 0 ? FILL_GOOD : FILL_BAD} ${Math.round(Math.min(1, Math.abs(v) / scale) * 62 + 12)}%, var(--panel2))`;

/* data bar behind a table number: length = |v| / scale (scale = a high percentile, so one outlier does not flatten the rest) */
const pmax = (vals, q = 0.9) => { const a = vals.filter(ok).map(Math.abs).sort((x, y) => x - y); return a.length ? Math.max(1e-9, a[Math.floor((a.length - 1) * q)]) : 1; };
function dbar(v, scale, content, color) {
  if (!ok(v)) return h('span', { class: 'sub' }, dash);
  const w = Math.min(1, Math.abs(v) / (scale || 1)) * 100;
  return h('span', { class: 'rx-db', style: `--w:${w.toFixed(1)}%;--c:${color || (v >= 0 ? 'var(--good)' : 'var(--bad)')}` }, content);
}
/* status as a dot + words (one line), for dense tables; the full badge stays on cards and headers */
const statusDot = (status) => { const m = RXS[statusKey(status)]; return h('span', { class: 'rx-sdot ' + m.cls, title: m.why + ' (registro: ' + status + ')' }, m.label); };
const statusLine = (r) => h('span', { class: 'rx-sline' }, statusDot(r.status), r.in_dryrun ? h('span', { class: 'rx-sdot dry', title: 'Rodando ao vivo com dinheiro simulado' }, 'Em dry-run') : null);

/* ---------- visual layer (v5): rings, donut, gradient areas, strategy cards, tiles, waffle, calendar ----------
   All shapes are SVG or plain elements built with h()/sv(); colours come from the theme tokens. Entrance motion
   plays once per route (rxAnim), never on the 15 s refresh, and is off with prefers-reduced-motion. */
let RXG = 0;
const rxGid = () => 'rxg' + (++RXG);
const RXA = { hash: null, on: false, queue: [] };
function rxAnim() {
  const key = String(location.hash || '').split('?')[0];
  if (RXA.hash === key) { RXA.on = false; return ''; }
  RXA.hash = key;
  RXA.on = !(typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches);
  return RXA.on ? ' rx-anim' : '';
}
/* a number that counts up to its value (once per route); fmt turns a number into the final text */
function cnt(value, fmt) {
  const el = h('span', { class: 'rx-cnt' }, ok(value) ? fmt(value) : dash);
  if (!RXA.on || !ok(value) || value === 0) return el;
  if (!RXA.queue.length) requestAnimationFrame((t0) => {
    const q = RXA.queue.splice(0), dur = 1100;
    const step = (t) => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 4); for (const [n, v, f] of q) n.textContent = f(v * e); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
  RXA.queue.push([el, value, fmt]);
  return el;
}
const fmtInt = (v) => nf0.format(Math.round(v));
const gradDef = (id, color, top = 0.34) => sv('linearGradient', { id, x1: 0, y1: 0, x2: 0, y2: 1 },
  sv('stop', { offset: '0%', style: `stop-color:${color};stop-opacity:${top}` }), sv('stop', { offset: '100%', style: `stop-color:${color};stop-opacity:0` }));
/* progress ring: frac in 0..1, text in the middle */
function ring(frac, { size = 64, stroke = 6, color = 'var(--accent)', text = '', sub = '', label } = {}) {
  const r = (size - stroke) / 2, c = size / 2, f = Math.max(0, Math.min(1, ok(frac) ? frac : 0));
  return h('div', { class: 'rx-ring', style: `width:${size}px;height:${size}px;font-size:${Math.round(size * (sub ? 0.26 : 0.3))}px`, role: 'img', 'aria-label': label || `${text} ${sub}`.trim() },
    sv('svg', { viewBox: `0 0 ${size} ${size}`, width: size, height: size, 'aria-hidden': 'true' },
      sv('circle', { cx: c, cy: c, r, fill: 'none', stroke: 'var(--track)', 'stroke-width': stroke }),
      f > 0 ? sv('circle', { class: 'arc', style: `color:${color}`, cx: c, cy: c, r, fill: 'none', stroke: color, 'stroke-width': stroke, 'stroke-linecap': f < 1 ? 'round' : 'butt', pathLength: 100,
        'stroke-dasharray': `${(f * 100).toFixed(2)} 100`, transform: `rotate(-90 ${c} ${c})` }) : null),
    h('div', { class: 'in' }, h('b', null, text), sub ? h('small', null, sub) : null));
}
/* donut: parts [{label, v, color}], 2-unit surface gap between parts, hover tooltip on each arc */
function donut(parts, { size = 176, stroke = 24, center = '', sub = '' } = {}) {
  const total = parts.reduce((a, p) => a + (p.v || 0), 0) || 1, r = (size - stroke) / 2, c = size / 2, live = parts.filter((p) => p.v);
  const gap = live.length > 1 ? 0.9 : 0, svg = sv('svg', { viewBox: `0 0 ${size} ${size}`, width: size, height: size, 'aria-hidden': 'true' });
  svg.append(sv('circle', { cx: c, cy: c, r, fill: 'none', stroke: 'var(--track)', 'stroke-width': stroke }));
  let acc = 0;
  for (const p of live) {
    const len = p.v / total * 100, dash = Math.max(0.4, len - gap);
    svg.append(sv('circle', { class: 'arc rx-dot', cx: c, cy: c, r, fill: 'none', stroke: p.color, 'stroke-width': stroke, pathLength: 100, 'stroke-dasharray': `${dash.toFixed(2)} ${(100 - dash).toFixed(2)}`,
      'stroke-dashoffset': (-acc).toFixed(2), transform: `rotate(-90 ${c} ${c})`,
      onmousemove: (e) => showTip(e, p.label, [{ color: p.color, value: nf0.format(p.v), label: ` de ${nf0.format(total)} (${nf0.format(p.v / total * 100)}%)` }]), onmouseleave: hideTip }));
    acc += len;
  }
  return h('div', { class: 'rx-donut', style: `width:${size}px;height:${size}px`, role: 'img', 'aria-label': `${nf0.format(total)} ${sub}: ` + live.map((p) => `${p.label} ${p.v}`).join(', ') },
    svg, h('div', { class: 'in' }, h('b', null, center), h('small', null, sub)));
}
/* area sparkline with a gradient wash; the line draws itself on entrance */
function rxArea(points, { w = 300, ht = 72, color } = {}) {
  if (!points || points.length < 2) return h('div', { class: 'rx-area-empty' }, 'sem curva');
  const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(0, ...ys), y1 = Math.max(0, ...ys);
  const X = (x) => 1 + (x - x0) / ((x1 - x0) || 1) * (w - 6), Y = (y) => ht - 3 - (y - y0) / ((y1 - y0) || 1) * (ht - 8);
  const end = ys[ys.length - 1], col = color || (end >= 0 ? 'var(--good)' : 'var(--bad)'), id = rxGid();
  const d = points.map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)).join('');
  return sv('svg', { viewBox: `0 0 ${w} ${ht}`, width: '100%', class: 'rx-area', preserveAspectRatio: 'none', 'aria-hidden': 'true' },
    sv('defs', null, gradDef(id, col)),
    sv('line', { x1: 0, x2: w, y1: Y(0), y2: Y(0), stroke: 'var(--line2)', 'stroke-dasharray': '2 3', 'vector-effect': 'non-scaling-stroke' }),
    sv('path', { class: 'ar', d: d + `L${X(x1).toFixed(1)} ${ht}L${X(x0).toFixed(1)} ${ht}Z`, fill: `url(#${id})` }),
    sv('path', { class: 'ln', d, fill: 'none', stroke: col, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', pathLength: 1, 'vector-effect': 'non-scaling-stroke' }));
}
/* risk 1..10 as ten segments */
function riskMeter(dd) {
  const r = riskOf(dd);
  if (r == null) return h('span', { class: 'sub' }, 'risco ' + dash);
  const cls = r <= 3 ? 'good' : r <= 6 ? 'warn' : 'bad', band = r <= 3 ? 'baixo' : r <= 6 ? 'médio' : 'alto';
  return h('span', { class: 'rx-meter ' + cls, role: 'img', 'aria-label': `Risco ${r} de 10 (${band})`, title: `Risco ${r} de 10 (${band}): pior queda de ${nf1.format(dd)}%` },
    Array.from({ length: 10 }, (_, i) => h('i', { class: i < r ? 'on' : null })), h('small', null, `risco ${r}/10 · ${band}`));
}
/* frequency framing: 100 squares, wins first */
function waffle(frac) {
  const k = ok(frac) ? Math.round(frac * 100) : 0;
  return h('div', { class: 'rx-waffle', role: 'img', 'aria-label': `De cada 100 operações, ${k} deram lucro e ${100 - k} deram prejuízo` }, Array.from({ length: 100 }, (_, i) => h('i', { class: i < k ? 'w' : null, style: `--i:${i}` })));
}
/* one strategy as a card: name, score ring, big return, curve, four numbers, risk meter */
/* compound return per year over the span of the row's own curve */
function perYear(r) {
  const c = r && r.curve; if (!c || c.length < 2 || !ok(r.roi_pct)) return null;
  const years = (c[c.length - 1][0] - c[0][0]) / (365.25 * 86400000);
  if (years < 0.25 || r.roi_pct <= -100) return null;
  return (Math.pow(1 + r.roi_pct / 100, 1 / years) - 1) * 100;
}
const approvedOf = (r) => Object.values(r.decisions || {}).filter((d) => d === 'candidate_for_portfolio').length;
const PARTS = [['profit', 'Lucro'], ['risk', 'Risco'], ['sample', 'Amostra'], ['consistency', 'Consistência']];
function stratCard(r, { i = 0, sel = false } = {}) {
  const hy = rxHy(r.id), low = (r.min_trades_pair || 0) < rxMin(), none = !r.trades;
  return h('article', { class: 'rx-sc' + (r.in_dryrun ? ' dry' : '') + (none ? ' none' : ''), style: `--i:${Math.min(i, 24)}` },
    h('header', null,
      h('div', { class: 'rx-name' }, h('a', { class: 'stretch', href: '#/strategy/' + encodeURIComponent(r.id), 'data-fkey': 'rxc:' + r.id + ':' + r.stage }, r.id), h('span', null, humanName(r.family)),
        h('small', null, [tfOf(hy) || '?', `${r.n_pairs} ${plural(r.n_pairs, 'ativo', 'ativos')}`, RX_STAGE[r.stage].toLowerCase()].join(' · '))),
      h('div', { title: PARTS.map(([k, l]) => `${l}: ${nf0.format(((r.score_parts || {})[k] || 0) * 100)}/100`).join(' · ') },
        ring(ok(r.score) ? r.score / 100 : 0, { size: 50, stroke: 5, text: ok(r.score) ? nf0.format(r.score) : dash, sub: 'nota', label: `Nota ${ok(r.score) ? nf0.format(r.score) : 'sem nota'} de 100` }))),
    h('div', { class: 'row' }, statusBadge(r.status), r.in_dryrun ? dryBadge() : null),
    none ? h('div', { class: 'rx-sc-big' }, h('b', { class: 'sub' }, dash), h('small', null, 'não fez nenhuma operação no período'))
      : h('div', { class: 'rx-sc-big' }, h('b', { class: toneOf(r.roi_pct) + ' rx-glow' }, cnt(r.roi_pct, (v) => sp(v, 1))), h('small', null, 'retorno médio por ativo')),
    none ? h('div', { class: 'rx-area-empty' }, 'sem operações, sem curva') : rxArea(r.curve),
    h('dl', { class: 'rx-sc-stats' },
      h('div', null, h('dt', null, 'Win rate'), h('dd', null, wr(r.winrate)), h('span', { class: 'mini' }, h('i', { style: `width:${((r.winrate || 0) * 100).toFixed(1)}%` }))),
      h('div', null, h('dt', null, 'Payoff'), h('dd', null, n2(r.payoff))),
      h('div', null, h('dt', null, 'Operações'), h('dd', null, nf0.format(r.trades || 0), low ? h('span', { class: 'rx-low', title: 'Pouca amostra: algum ativo teve menos de 30 operações' }, ' !') : null)),
      h('div', null, h('dt', null, 'Custo alto'), h('dd', null, signedSpan(r.roi_stress_pct, 0)))),
    h('footer', null, none ? h('span', { class: 'sub' }, 'risco: sem dados') : riskMeter(r.max_dd_pct),
      sel ? h('label', { class: 'rx-check rx-pickc' }, h('input', { type: 'checkbox', 'data-fkey': 'rxsel:' + r.id, checked: rx.sel.includes(r.id), onchange: (e) => { rx.sel = e.target.checked ? [...rx.sel, r.id].slice(-4) : rx.sel.filter((x) => x !== r.id); render(); } }), 'Comparar') : null));
}
/* the lab as tiles: one tile per strategy, grouped by outcome, coloured by return */
const MAP_GROUPS = [['validada', 'Aprovadas nas duas provas'], ['exp_aprovada', 'Aprovadas na exploração'], ['val_reprovada', 'Foram bem, mas não repetiram na validação'], ['exp_reprovada', 'Reprovadas na exploração'], ['inconclusiva', 'Inconclusivas'], ['referencia', 'Referência'], ['descartada', 'Outras']];
function labMap(rows) {
  if (!rows.length) return emptyState('Nenhuma estratégia com backtest.');
  const abs = rows.map((r) => Math.abs(r.roi_pct || 0)).sort((a, b) => a - b), scale = Math.max(10, abs[Math.floor(abs.length * 0.8)] || 10);
  let n = 0;
  return h('div', { class: 'rx-map' }, MAP_GROUPS.map(([k, title]) => {
    const g = rows.filter((r) => statusKey(r.status) === k).sort((a, b) => (b.roi_pct ?? -1e9) - (a.roi_pct ?? -1e9));
    if (!g.length) return null;
    return h('section', { class: 'rx-mapgrp' }, h('h3', null, title, h('small', null, ` · ${g.length}`)),
      h('div', { class: 'rx-tilewrap' }, g.map((r) => h('a', { class: 'rx-tile', href: '#/strategy/' + encodeURIComponent(r.id), 'data-fkey': 'rxt:' + r.id, style: `background:${heatSolid(r.roi_pct, scale)};--i:${Math.min(n++, 40)}`,
        onmousemove: (e) => showTip(e, `${r.id} · ${humanName(r.family)}`, [{ value: sp(r.roi_pct), label: ' retorno médio' }, { value: wr(r.winrate), label: ' win rate' }, { value: n2(r.payoff), label: ' payoff' }, { value: nf0.format(r.trades || 0), label: ' operações' }, { value: RXS[k].label, label: '' }]), onmouseleave: hideTip },
        r.in_dryrun ? h('span', { class: 'dot', title: 'Em dry-run' }) : null, h('b', null, r.id), h('span', { class: 'v' }, sp(r.roi_pct, 0)), h('small', null, humanName(r.family))))));
  }));
}
/* the funnel as a pipeline of steps (the counts are not monotonic: dry-run also takes strategies that failed validation) */
function pipeline(fun) {
  const max = Math.max(1, fun[0][1]);
  return h('ol', { class: 'rx-pipe' }, fun.map(([l, n, s], i) => h('li', { class: n ? null : 'zero', style: `--i:${i}` },
    h('span', { class: 'k' }, `Etapa ${i + 1}`), h('b', null, cnt(n, fmtInt)), h('span', { class: 'l' }, l), h('small', null, s),
    h('span', { class: 'bar', title: `${nf0.format(n / max * 100)}% das ideias registradas` }, h('i', { style: `width:${(n / max * 100).toFixed(1)}%` })))));
}
/* where each registered idea stopped, in six buckets (detail list below the donut) */
const DEST = [['ok', 'Aprovadas até agora', 'var(--good)'], ['val', 'Não repetiram na validação', 'var(--warn)'], ['exp', 'Reprovadas na exploração', 'var(--bad)'],
  ['pre', 'Barradas antes do backtest completo', 'var(--na)'], ['inc', 'Inconclusivas', 'var(--line2)'], ['todo', 'Ainda não testadas', 'var(--info)'], ['ref', 'Referência', 'var(--accent)']];
function destOf(x) {
  const k = statusKey(x.status);
  if (x.invalid) return 'pre';
  if (k === 'exp_aprovada' || k === 'validada') return 'ok';
  if (k === 'referencia') return 'ref';
  if (k === 'val_reprovada') return 'val';
  if (k === 'inconclusiva') return 'inc';
  const why = dropReason(x.status);
  return /exploração/.test(why) ? 'exp' : /validação/.test(why) ? 'val' : why === 'Ainda não testada' ? 'todo' : 'pre';
}
/* calendar heatmap of the daily summed result (close date, Brasília), one year at a time, with month totals */
const MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function calendarHeat(I, list, st) {
  const by = new Map();
  for (const i of list) { const t = I.rows[i], d = Math.floor((t[1] + t[2] - 180) / 1440), o = by.get(d) || { s: 0, n: 0, w: 0 }; o.s += t[4] / wOf(I, i) * 100; o.n++; if (t[3] > 0) o.w++; by.set(d, o); }
  if (!by.size) return emptyState('Sem operações com estes filtros.');
  const yOf = (d) => new Date(d * 86400000).getUTCFullYear(), years = [...new Set([...by.keys()].map(yOf))].sort((a, b) => a - b);
  const perYear = {}; for (const [d, o] of by) { const y = yOf(d); perYear[y] = (perYear[y] || 0) + o.n; }
  const busiest = years.reduce((a, y) => (perYear[y] > perYear[a] ? y : a), years[0]);
  const year = years.includes(+st.calYear) ? +st.calYear : busiest;
  const inYear = [...by].filter(([d]) => yOf(d) === year), abs = inYear.map(([, o]) => Math.abs(o.s)).sort((a, b) => a - b), scale = Math.max(0.2, abs[Math.floor(abs.length * 0.9)] || 1);
  const start = Date.UTC(year, 0, 1) / 86400000, end = Date.UTC(year + 1, 0, 1) / 86400000, dow0 = new Date(start * 86400000).getUTCDay();
  const C = 12, G = 3, L = 30, T = 16, W = L + 54 * (C + G), H = T + 7 * (C + G);
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': `Resultado somado por dia em ${year}`, class: 'rx-chart rx-cal' });
  [1, 3, 5].forEach((d) => svg.append(sv('text', { x: L - 6, y: T + d * (C + G) + C - 2, 'text-anchor': 'end' }, DOW[d])));
  for (let m = 0; m < 12; m++) { const k = Date.UTC(year, m, 1) / 86400000 - start + dow0; svg.append(sv('text', { x: L + Math.floor(k / 7) * (C + G), y: T - 5 }, MES[m])); }
  const months = Array.from({ length: 12 }, () => ({ s: 0, n: 0 }));
  for (let d = start; d < end; d++) {
    const k = d - start + dow0, o = by.get(d), date = new Date(d * 86400000);
    if (o) { const m = months[date.getUTCMonth()]; m.s += o.s; m.n += o.n; }
    svg.append(sv('rect', { x: L + Math.floor(k / 7) * (C + G), y: T + (k % 7) * (C + G), width: C, height: C, rx: 3, fill: o ? heatSolid(o.s, scale) : 'var(--track)',
      onmousemove: (e) => showTip(e, dayUtc(date.toISOString()), o ? [{ value: sp(o.s, 2), label: ' resultado somado' }, { value: nf0.format(o.n), label: ` ${plural(o.n, 'operação fechada', 'operações fechadas')}` }, { value: `${o.w}/${o.n}`, label: ' no lucro' }] : [{ value: '—', label: ' nenhuma operação fechou' }]),
      onmouseleave: hideTip }));
  }
  const mmax = Math.max(1e-9, ...months.map((m) => Math.abs(m.s)));
  const pos = inYear.filter(([, o]) => o.s > 0).length, neg = inYear.filter(([, o]) => o.s < 0).length;
  return h('div', { class: 'rx-stack' },
    h('div', { class: 'rx-views', role: 'group', 'aria-label': 'Ano' }, years.map((y) => h('button', { type: 'button', class: 'rx-view', 'aria-pressed': y === year ? 'true' : 'false', 'data-fkey': 'rxcal:' + y, onclick: () => { st.calYear = String(y); render(); } }, String(y)))),
    h('div', { class: 'tablewrap rx-calwrap' }, svg),
    h('div', { class: 'rx-monthbars', role: 'img', 'aria-label': 'Resultado somado por mês' }, months.map((m, i) => h('div', { class: 'mb', onmousemove: (e) => showTip(e, `${MES[i]}/${year}`, [{ value: m.n ? sp(m.s, 1) : '—', label: ' resultado somado' }, { value: nf0.format(m.n), label: ' operações' }]), onmouseleave: hideTip },
      h('span', { class: 'up' }, m.s > 0 ? h('i', { style: `height:${(m.s / mmax * 100).toFixed(1)}%` }) : null), h('span', { class: 'dn' }, m.s < 0 ? h('i', { style: `height:${(-m.s / mmax * 100).toFixed(1)}%` }) : null), h('small', null, MES[i])))),
    h('div', { class: 'row sub' }, `${year}: ${pos} ${plural(pos, 'dia', 'dias')} no lucro, ${neg} no prejuízo.`, h('span', { class: 'rx-scale' }, 'prejuízo', ['-1', '-0.5', '0', '0.5', '1'].map((v) => h('i', { style: `background:${+v ? heatSolid(+v * scale, scale) : 'var(--track)'}` })), 'lucro')));
}

/* ---------- the trade index (all operations), loaded once ---------- */
const TI = { data: null, ref: null, loading: false, error: null };
function prepIndex(raw) {
  const cells = raw.cells || [], reasons = raw.exit_reasons || [], rows = raw.trades || [];
  const hyOfCell = cells.map((c) => rxHy(c.id)), tfOfCell = hyOfCell.map(tfOf);
  const n = rows.length, dow = new Int8Array(n), hour = new Int8Array(n);
  for (let i = 0; i < n; i++) { const d = new Date((rows[i][1] - 180) * 60000); dow[i] = d.getUTCDay(); hour[i] = d.getUTCHours(); }
  return { cells, reasons, rows, dow, hour, tfOfCell };
}
function tradeIndex() {
  if (state.trade_index && (state.trade_index.trades || []).length) { if (TI.ref !== state) { TI.data = prepIndex(state.trade_index); TI.ref = state; } return TI.data; }
  if (!LIVE) return TI.data;
  if (TI.ref !== state && !TI.loading) {
    TI.loading = true; TI.error = null; const want = state;
    fetch('/api/trade-index', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then((d) => { TI.data = prepIndex(d); TI.ref = want; }).catch((e) => { TI.error = String(e.message || e); TI.ref = want; })
      .finally(() => { TI.loading = false; render(); });
  }
  return TI.data;
}
const indexPending = () => TI.error ? emptyState('Não foi possível carregar as operações.', TI.error) : loadingState('Carregando as operações dos backtests…');
const wOf = (I, i) => (I.cells[I.rows[i][0]].wallet || 100);
function tradeStats(I, list) {
  let n = 0, wins = 0, gp = 0, gl = 0, sw = 0, nw = 0, sl = 0, nl = 0, sp_ = 0, sum = 0, sd = 0, best = -Infinity, worst = Infinity;
  for (const i of list) {
    const t = I.rows[i], p = t[3], a = t[4]; n++; sp_ += p; sd += t[2]; sum += a / wOf(I, i) * 100;
    if (p > 0) { wins++; sw += p; nw++; } else if (p < 0) { sl += p; nl++; }
    if (a > 0) gp += a; else gl -= a;
    if (p > best) best = p; if (p < worst) worst = p;
  }
  const aw = nw ? sw / nw : null, al = nl ? sl / nl : null;
  return { n, wins, wr: n ? wins / n : null, pf: gl > 0 ? gp / gl : null, avg: n ? sp_ / n : null, sum, aw, al, payoff: aw != null && al ? aw / -al : null,
    best: n ? best : null, worst: n ? worst : null, dur: n ? sd / n : null };
}
const DOW = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
const DUR = [[0, 60, 'até 1 h'], [60, 240, '1 a 4 h'], [240, 720, '4 a 12 h'], [720, 1440, '12 a 24 h'], [1440, 4320, '1 a 3 dias'], [4320, 10080, '3 a 7 dias'], [10080, Infinity, 'mais de 7 dias']];
const durBucket = (m) => DUR.findIndex(([a, b]) => m >= a && m < b);
const REASON = (r) => ({ stop_loss: 'Stop (limite de perda)', trailing_stop_loss: 'Stop móvel', roi: 'Alvo de lucro', force_exit: 'Fim do período do teste', exit_signal: 'Sinal de saída', time_exit: 'Tempo máximo' }[r] || String(r).replace(/_/g, ' '));

/* ==================== Início ==================== */
function rxFunnel() {
  const hy = rxHyps();
  const expRows = rxRows('exploration'), valRows = rxRows('validation');
  const expPass = expRows.filter((r) => r.gates_all_pass).length, valPass = valRows.filter((r) => r.gates_all_pass).length;
  const dry = hy.filter((x) => x.in_dryrun).length;
  return [['Ideias registradas', hy.length, 'regra escrita antes do teste'], ['Chegaram ao backtest', expRows.length, 'rodaram nos dados de 2017 a 2024'],
    ['Passaram na exploração', expPass, 'em todos os ativos em que foram testadas'], ['Fizeram a validação', valRows.length, 'prova com dados recentes'],
    ['Passaram na validação', valPass, 'em todos os ativos testados'], ['Em dry-run', dry, 'ao vivo, dinheiro simulado'], ['Operando dinheiro real', 0, 'bloqueado até haver evidência']];
}
function pageInicio() {
  const A = rxAnim();
  const fun = rxFunnel(), [reg, bt, expPass, , valPass, dry] = fun.map((f) => f[1]);
  const exp = rxRows('exploration'), robust = exp.filter((r) => (r.min_trades_pair || 0) >= rxMin() && statusKey(r.status) !== 'referencia');
  const best = [...robust].sort((a, b) => (b.roi_pct ?? -1e9) - (a.roi_pct ?? -1e9));
  const dryHy = rxHyps().filter((x) => x.in_dryrun);
  const nTrades = exp.reduce((a, r) => a + (r.trades || 0), 0) + rxRows('validation').reduce((a, r) => a + (r.trades || 0), 0);
  const hero = h('p', { class: 'rx-hero' }, 'Das ', h('em', null, `${reg} ideias`), ` registradas, ${bt} chegaram ao backtest, ${expPass} passaram na primeira prova e `,
    h('em', null, valPass ? `${valPass}` : 'nenhuma'), ` ${valPass > 1 ? 'foram aprovadas' : 'foi aprovada'} nas duas. ${dry} ${plural(dry, 'está', 'estão')} em dry-run juntando evidência.`);
  const reasons = {}; for (const x of rxHyps()) { const k = x.invalid ? 'Código não seguia a regra registrada' : ['exp_aprovada', 'validada'].includes(statusKey(x.status)) ? 'Aprovada até agora' : statusKey(x.status) === 'referencia' ? 'Referência' : dropReason(x.status); reasons[k] = (reasons[k] || 0) + 1; }
  const dest = {}; for (const x of rxHyps()) { const k = destOf(x); dest[k] = (dest[k] || 0) + 1; }
  const parts = DEST.map(([k, label, color]) => ({ label, color, v: dest[k] || 0 }));
  const heatRows = best.slice(0, 14), pairs = (state.pairs || []).filter((p) => heatRows.some((r) => r.pairs.includes(p)));
  const heatAbs = heatRows.flatMap((r) => r.per_pair.map((c) => Math.abs(c.roi_pct || 0))).sort((a, b) => a - b), heatScale = Math.max(10, heatAbs[Math.floor(heatAbs.length * 0.75)] || 10);
  return h('div', { class: 'rx rx-stack' + A },
    h('div', { class: 'bento' },
      h('section', { class: 'card b-7 rx-herocard beam' },
        h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, 'Visão geral do projeto'), hero,
          h('p', { class: 'rx-lede' }, 'Cada ideia é uma regra de compra e venda escrita antes do teste. Ela passa por duas provas com dados históricos (', term('rx_explo', 'exploração'), ' e ', term('rx_valid', 'validação'), ') e só depois roda ao vivo em ', term('dryrun', 'dry-run'), '. Nenhuma estratégia opera dinheiro real hoje.')),
        h('div', { class: 'rx-kpis' },
          rxKpi('Operações simuladas', cnt(nTrades, fmtInt), `em ${(state.pairs || []).length} criptomoedas`),
          rxKpi(term('rx_ret', 'Melhor retorno médio'), best[0] ? h('span', { class: 'pos rx-glow' }, cnt(best[0].roi_pct, (v) => sp(v, 0))) : dash, best[0] ? h('a', { href: '#/strategy/' + best[0].id }, best[0].id + ', exploração') : null),
          rxKpi(term('dryrun', 'Em dry-run'), nf0.format(dry), listPt(dryHy.map((x) => x.id)) || 'nenhuma'),
          rxKpi('Dinheiro real', '0', 'nenhuma passou nas duas provas'))),
      card('O destino das ideias', `Onde cada uma das ${reg} hipóteses registradas parou. Passe o mouse no anel.`,
        h('div', { class: 'rx-stack' },
          h('div', { class: 'rx-dest' }, donut(parts, { center: cnt(reg, fmtInt), sub: 'ideias' }),
            h('ul', { class: 'rx-legend-list' }, parts.filter((p) => p.v).map((p) => h('li', null, h('i', { style: `background:${p.color}` }), h('span', null, p.label), h('b', null, nf0.format(p.v)))))),
          det('rx-why', 'Motivo detalhado de cada parada', hbars(Object.entries(reasons).sort((a, b) => b[1] - a[1]).map(([label, v]) => ({ label, v, color: /Aprovada/.test(label) ? 'var(--good)' : /Referência/.test(label) ? 'var(--accent)' : 'var(--bad)' }))))),
        { cls: 'b-5' }),
      card('O caminho de uma ideia até o dinheiro real', 'Cada etapa filtra a anterior; a barrinha mostra quantas das ideias registradas chegaram ali. O dry-run também recebe estratégias reprovadas na validação, para juntar evidência ao vivo.', pipeline(fun), { cls: 'b-12' }),
      card('As que mais renderam na primeira prova', 'Exploração (2017 a jul/2024), só estratégias com pelo menos 30 operações em cada ativo (a referência H-001 fica de fora). Rendimento passado não garante o futuro: por isso existem a validação e o dry-run.',
        h('div', { class: 'rx-gallery rx-gtop' }, best.slice(0, 6).map((r, i) => stratCard(r, { i }))), { cls: 'b-12', actions: h('a', { href: '#/leaderboard', 'data-fkey': 'rx-all' }, `Ver as ${exp.length} no ranking →`) }),
      card('Mapa do laboratório', `Cada bloco é uma das ${exp.length} estratégias que fizeram o backtest, agrupadas pelo resultado. A cor é o retorno médio na exploração: verde mais forte é mais lucro, vermelho é prejuízo. O ponto ciano marca as que estão em dry-run. Clique para abrir.`, labMap(exp), { cls: 'b-12' }),
      card('Onde cada estratégia funciona', 'Retorno de cada estratégia em cada criptomoeda, na exploração. Verde é lucro, vermelho é prejuízo; quanto mais forte a cor, maior o número. Traço: não testada naquele ativo.',
        h('div', { class: 'tablewrap' }, h('table', { class: 'rx-heat' }, h('thead', null, h('tr', null, h('th', null, 'Estratégia'), pairs.map((p) => h('th', { class: 'num' }, short(p))), h('th', { class: 'num' }, 'Média'))),
          h('tbody', null, heatRows.map((r) => h('tr', null, h('td', null, h('a', { href: '#/strategy/' + r.id }, r.id), ' ', h('span', { class: 'sub' }, humanName(r.family))),
            pairs.map((p) => { const c = r.per_pair.find((x) => x.pair === p); return c ? h('td', { class: 'num', style: `background:${heatBg(c.roi_pct, heatScale)}` }, sp(c.roi_pct, 0)) : h('td', { class: 'num sub' }, '—'); }),
            h('td', { class: 'num', style: `background:${heatBg(r.roi_pct, heatScale)};font-weight:600` }, sp(r.roi_pct, 0))))))), { cls: 'b-7' }),
      dryrunSummary('b-5'),
      typeof ixHomeCard === 'function' ? ixHomeCard('b-12') : null,
      attentionSummary('b-12')));
}
function rxKpi(label, value, note) { return h('div', { class: 'rx-kpi' }, h('span', { class: 'l' }, label), h('span', { class: 'v' }, value), note ? h('span', { class: 's' }, note) : null); }
function dryrunSummary(cls) {
  const items = (state.forward_test && state.forward_test.hypotheses) || [];
  /* one rule for every page: lab/config/dryrun.json, sent by the server (the old fixed 30 per pair / 28 days are gone) */
  const rule = (state.forward_test && state.forward_test.rule) || { need_trades: 60, need_days: 14, discard_after_days: 2 };
  const body = items.length ? items.map((d) => {
    const pairs = Object.values(d.pairs || {}), closed = pairs.reduce((a, p) => a + (p.closed || 0), 0), open = pairs.reduce((a, p) => a + (p.open || 0), 0);
    const days = d.frozen_at ? Math.max(0, (Date.now() - Date.parse(d.frozen_at)) / 86400000) : 0, hy = rxHy(d.id), target = rule.need_trades;
    const left = !closed && ok(rule.discard_after_days) ? rule.discard_after_days - days : null;
    return h('div', { class: 'rx-dry' }, h('div', { class: 'row' }, h('a', { href: '#/strategy/' + d.id }, h('b', null, d.id)), h('span', { class: 'sub' }, hy ? humanName(hy.family) : ''), d.freeze_ok ? badge(ST.pass, 'Congelada') : badge(ST.fail, 'Congelamento alterado')),
      h('div', { class: 'rx-dryrings' },
        h('div', { class: 'rx-part' }, ring(closed / target, { size: 62, text: nf0.format(closed), sub: `de ${target}`, label: `${closed} de ${target} operações fechadas` }), h('small', null, 'operações')),
        h('div', { class: 'rx-part' }, ring(days / rule.need_days, { size: 62, color: 'var(--teal)', text: days.toFixed(1).replace('.', ','), sub: 'dias no ar', label: `${days.toFixed(1)} dias no ar` }), h('small', null, 'dias rodando')),
        h('p', { class: 'sub' }, `${open} ${plural(open, 'operação aberta', 'operações abertas')} agora. Decide com ${rule.need_trades} trades e ${rule.need_days} dias`
          + (ok(rule.discard_after_days) ? `; sai se passar ${rule.discard_after_days} dias sem trade` : '') + (ok(left) ? (left > 0 ? ` (faltam ${left < 1 ? Math.max(1, Math.round(left * 24)) + ' h' : left.toFixed(1).replace('.', ',') + ' d'}).` : ' (sai no próximo ciclo).') : '.'))));
  }) : [emptyState('Nenhum bot em dry-run.')];
  return card('Rodando agora em dry-run', 'Bots congelados: a regra não muda durante a coleta, para a evidência valer.', h('div', { class: 'rx-stack' }, body), { cls, actions: h('a', { href: '#/dryrun' }, 'Detalhes →') });
}
function attentionSummary(cls) {
  const open = openItems();
  return card('Precisa de atenção', open.length ? `${open.length} ${plural(open.length, 'item aberto', 'itens abertos')} no sistema.` : 'Nada pendente.',
    h('div', { class: 'rx-stack' }, open.slice(0, 6).map((a) => h('div', { class: 'row' }, badge(a.level === 'critical' ? ST.fail : a.level === 'warning' ? ST.warn : ST.info, a.level === 'critical' ? 'Crítico' : a.level === 'warning' ? 'Aviso' : 'Info'), h('span', null, a.text)))),
    { cls, actions: h('a', { href: '#/data' }, 'Sistema →') });
}

/* ==================== Ranking ==================== */
const VIEWS = [
  ['all', 'Todas', () => true], ['lucro', 'Mais lucrativas', (r) => (r.roi_pct || 0) > 0 && (r.min_trades_pair || 0) >= rxMin()],
  ['consist', 'Mais consistentes', (r) => r.n_pairs > 0 && r.pairs_positive === r.n_pairs && (r.positive_year_share || 0) >= 0.6],
  ['custo', 'Aguentam custo alto', (r) => (r.roi_stress_pct || 0) > 0], ['day', 'Day trade (15m)', (r) => tfOf(rxHy(r.id)) === '15m'],
  ['dry', 'Em dry-run', (r) => r.in_dryrun], ['aprov', 'Aprovadas', (r) => r.gates_all_pass], ['reprov', 'Reprovadas', (r) => r.gates_any_rejected],
];
/* card-mode ordering: [key, label, value, direction (-1 = highest first)] */
const CSORT = [['roi', 'Maior retorno médio', (r) => r.roi_pct, -1], ['score', 'Maior nota', (r) => r.score, -1], ['wr', 'Maior win rate', (r) => r.winrate, -1],
  ['payoff', 'Maior payoff', (r) => r.payoff, -1], ['stress', 'Melhor com custo alto', (r) => r.roi_stress_pct, -1], ['risk', 'Menor risco', (r) => r.max_dd_pct, 1], ['trades', 'Mais operações', (r) => r.trades, -1]];
function scoreCell(r) {
  const p = r.score_parts || {}, parts = [['profit', 'Lucro'], ['risk', 'Risco'], ['sample', 'Amostra'], ['consistency', 'Consistência']];
  return h('div', { class: 'rx-score', title: parts.map(([k, l]) => `${l}: ${nf0.format((p[k] || 0) * 100)}/100`).join(' · ') + (p.capped_by_sample ? ' · limitada a 40 (amostra pequena)' : '') + (p.capped_by_gates ? ' · limitada a 60 (reprovada)' : '') },
    h('b', null, ok(r.score) ? nf0.format(r.score) : dash), h('span', { class: 'bars' }, parts.map(([k]) => h('i', { style: `height:${Math.max(8, (p[k] || 0) * 100)}%` }))));
}
function rankCols(withSel, rows = []) {
  const S = { roi: pmax(rows.map((r) => r.roi_pct)), stress: pmax(rows.map((r) => r.roi_stress_pct)), trades: pmax(rows.map((r) => r.trades), 1) };
  return [
    withSel && { key: 'sel', label: 'Comparar', cell: (r) => h('input', { type: 'checkbox', 'aria-label': 'Comparar ' + r.id, 'data-fkey': 'rxsel:' + r.id, checked: rx.sel.includes(r.id), onchange: (e) => { rx.sel = e.target.checked ? [...rx.sel, r.id].slice(-4) : rx.sel.filter((x) => x !== r.id); render(); } }) },
    { key: 'name', label: 'Estratégia', val: (r) => r.id, cell: (r) => nameCell(r, rxHy(r.id)) },
    { key: 'status', label: 'Situação', val: (r) => Object.keys(RXS).indexOf(statusKey(r.status)), cell: statusLine },
    { key: 'score', label: 'Nota', term: 'rx_score', num: true, val: (r) => r.score, cell: scoreCell },
    { key: 'risk', label: 'Risco', term: 'rx_risk', num: true, val: (r) => riskOf(r.max_dd_pct), cell: (r) => riskBadge(r.max_dd_pct) },
    { key: 'trades', label: 'Operações', term: 'rx_trades', num: true, val: (r) => r.trades, cell: (r) => dbar(r.trades, S.trades, h('span', null, nf0.format(r.trades), (r.min_trades_pair || 0) < rxMin() ? h('span', { class: 'rx-low', title: 'Pouca amostra: algum ativo teve menos de 30 operações' }, ' !') : null), 'var(--muted)') },
    { key: 'wr', label: 'Win rate', term: 'rx_wr', num: true, val: (r) => r.winrate, cell: (r) => dbar(r.winrate, 1, wr(r.winrate), 'var(--accent)') },
    { key: 'payoff', label: 'Payoff', term: 'rx_payoff', num: true, val: (r) => r.payoff, cell: (r) => n2(r.payoff) },
    { key: 'roi', label: 'Retorno médio', term: 'rx_ret', num: true, val: (r) => r.roi_pct, cell: (r) => dbar(r.roi_pct, S.roi, signedSpan(r.roi_pct, 1, true)) },
    { key: 'stress', label: 'Com custo alto', term: 'rx_stress', num: true, val: (r) => r.roi_stress_pct, cell: (r) => dbar(r.roi_stress_pct, S.stress, signedSpan(r.roi_stress_pct)) },
    { key: 'curve', label: 'No tempo', cell: (r) => rxSpark(r.curve, 88) },
  ].filter(Boolean);
}
function pageRanking() {
  const st = rx.rank, all = rxRows(st.stage), q = st.q.trim().toLowerCase(), view = VIEWS.find((v) => v[0] === st.view) || VIEWS[0];
  const counts = {}; for (const r of all) { const k = statusKey(r.status); counts[k] = (counts[k] || 0) + 1; }
  const tfs = [...new Set(all.map((r) => tfOf(rxHy(r.id))).filter(Boolean))].sort();
  const rows = all.filter((r) => view[2](r) && (st.status === 'all' || statusKey(r.status) === st.status) && (st.tf === 'all' || tfOf(rxHy(r.id)) === st.tf)
    && (st.pair === 'all' || r.pairs.includes(st.pair)) && (!st.sample || (r.min_trades_pair || 0) >= rxMin())
    && (!q || `${r.id} ${humanName(r.family)} ${r.family}`.toLowerCase().includes(q))).map((r) => ({ ...r, key: r.key }));
  const robust = all.filter((r) => (r.min_trades_pair || 0) >= rxMin());
  const notRef = robust.filter((r) => statusKey(r.status) !== 'referencia'), top = (f, list = notRef) => [...list].filter((r) => ok(f(r))).sort((a, b) => f(b) - f(a))[0];
  const hl = [['Maior retorno médio', top((r) => r.roi_pct), (r) => sp(r.roi_pct, 0), (r) => `win rate ${wr(r.winrate)} · payoff ${n2(r.payoff)}`],
    ['Maior win rate', top((r) => r.winrate), (r) => wr(r.winrate), (r) => `retorno ${sp(r.roi_pct, 0)} · payoff ${n2(r.payoff)}`],
    ['Menor queda (com lucro)', top((r) => -r.max_dd_pct, notRef.filter((r) => (r.roi_pct || 0) > 0)), (r) => ddText(r.max_dd_pct), (r) => `retorno ${sp(r.roi_pct, 0)}`],
    ['Melhor com custo alto', top((r) => r.roi_stress_pct), (r) => sp(r.roi_stress_pct, 0), () => 'retorno refeito com taxas bem piores']];
  const setR = (k, v) => { st[k] = v; render(); };
  const cs = CSORT.find((c) => c[0] === st.csort) || CSORT[0];
  const cardRows = rows.filter((r) => ok(cs[2](r))).sort((a, b) => (cs[2](a) - cs[2](b)) * cs[3]).concat(rows.filter((r) => !ok(cs[2](r))));
  const listing = st.mode === 'table' ? dataTable({ id: 'rx-rank', cols: rankCols(true, rows), rows, sort0: { key: 'roi', dir: -1 }, label: 'Ranking de estratégias' })
    : rows.length ? h('div', { class: 'rx-gallery' }, cardRows.map((r, i) => stratCard(r, { i, sel: true }))) : emptyState('Nenhuma estratégia com estes filtros.');
  return h('div', { class: 'rx rx-stack' + rxAnim() },
    rxHeader('Ranking', 'Todas as estratégias testadas', `As ${all.length} estratégias com resultado na ${RX_STAGE[st.stage].toLowerCase()} (${RX_PERIOD[st.stage]}), aprovadas ou não. Clique no título de uma coluna para ordenar e no nome para abrir a estratégia.`),
    h('div', { class: 'rx-toolbar' },
    h('div', { class: 'rx-views', role: 'group', 'aria-label': 'Visões prontas' }, VIEWS.map(([k, l, f]) => h('button', { type: 'button', class: 'rx-view', 'aria-pressed': st.view === k ? 'true' : 'false', 'data-fkey': 'rxv:' + k, onclick: () => setR('view', k) }, l, h('small', null, String(all.filter(f).length))))),
    h('div', { class: 'rx-controls' },
      segmented('Ver como', 'rx-mode', st.mode, [['cards', 'Cartões'], ['table', 'Tabela']], (v) => setR('mode', v)),
      st.mode === 'table' ? null : selectBox('Ordenar por', 'rx-csort', st.csort, CSORT.map(([k, l]) => [k, l]), (v) => setR('csort', v)),
      segmented('Prova', 'rx-stage', st.stage, [['exploration', `Exploração · ${rxRows('exploration').length}`], ['validation', `Validação · ${rxRows('validation').length}`]], (v) => setR('stage', v)),
      selectBox('Situação', 'rx-status', st.status, [['all', 'Todas'], ...Object.keys(RXS).filter((k) => counts[k]).map((k) => [k, `${RXS[k].label} (${counts[k]})`])], (v) => setR('status', v)),
      selectBox('Tempo gráfico', 'rx-tf', st.tf, [['all', 'Todos'], ...tfs.map((x) => [x, x])], (v) => setR('tf', v)),
      selectBox('Ativo', 'rx-pair', st.pair, [['all', 'Todos'], ...(state.pairs || []).map((p) => [p, short(p)])], (v) => setR('pair', v)),
      h('label', null, 'Buscar', h('input', { type: 'search', value: st.q, placeholder: 'H-047, momentum…', 'data-fkey': 'rx-q', oninput: (e) => setR('q', e.target.value) })),
      h('label', { class: 'rx-check' }, h('input', { type: 'checkbox', checked: st.sample, 'data-fkey': 'rx-sample', onchange: (e) => setR('sample', e.target.checked) }), ' Só amostra confiável (30+ operações por ativo)'))),
    h('div', { class: 'rx-cards' }, hl.filter((x) => x[1]).map(([l, r, v, c]) => h('a', { class: 'rx-hl', href: '#/strategy/' + r.id, 'data-fkey': 'rxhl:' + l }, h('span', { class: 'l' }, l), h('b', null, v(r)), h('span', null, `${r.id} · ${humanName(r.family)}`), h('small', null, c(r))))),
    h('p', { class: 'sub' }, 'Os destaques consideram só estratégias com 30 ou mais operações em cada ativo e deixam de fora a referência (H-001).'),
    det('rx-how', 'Como ler esta tabela', h('ul', { class: 'rx-list' },
      h('li', null, h('b', null, 'Retorno médio'), ' é o número principal: quanto o capital cresceu, na média dos ativos testados.'),
      h('li', null, h('b', null, 'Win rate alto não basta. '), 'Uma estratégia pode acertar 40 de cada 100 e ganhar muito, se o payoff for alto. O gráfico abaixo da tabela mostra isso.'),
      h('li', null, h('b', null, 'Com custo alto'), ' negativo quer dizer que a estratégia só lucra com taxas baixas: é frágil.'),
      h('li', null, h('b', null, 'Nota'), ' resume quatro notas (passe o mouse sobre as barrinhas). ', h('b', null, 'Risco'), ' vai de 1 (baixo) a 10 (alto), pela pior queda.'),
      h('li', null, 'Marque até quatro estratégias na primeira coluna para compará-las lado a lado.'))),
    rx.sel.length ? h('div', { class: 'rx-selbar' }, h('span', null, `${rx.sel.length} ${plural(rx.sel.length, 'selecionada', 'selecionadas')}: ${rx.sel.join(', ')}`),
      h('button', { type: 'button', class: 'primary', 'data-fkey': 'rx-cmp-go', onclick: () => { rx.cmp.ids = [...rx.sel]; rx.cmp.stage = st.stage; rxGo('#/compare'); } }, 'Comparar lado a lado'),
      h('button', { type: 'button', 'data-fkey': 'rx-cmp-clear', onclick: () => { rx.sel = []; render(); } }, 'Limpar')) : null,
    listing,
    h('p', { class: 'sub' }, `${rows.length} de ${all.length} estratégias.`, st.mode === 'table' ? '' : ' Em "Ver como", escolha Tabela para ordenar por qualquer coluna.'),
    h('div', { class: 'rx-grid g2' },
      card('Acertar muito ou ganhar muito?', 'Cada bolha é uma estratégia (maior = mais operações). Acima da linha tracejada, os ganhos compensam as perdas antes das taxas. À direita acerta mais; no alto ganha mais quando acerta.', scatterWrPayoff(rows),
        { actions: h('div', { class: 'legend' }, [['var(--teal)', 'Em dry-run'], ['var(--info)', 'Aprovada nesta prova'], ['var(--muted)', 'Lucro, mas reprovada'], ['var(--bad)', 'Prejuízo']].map(([c, l]) => h('span', null, h('span', { class: 'key', style: `border-top-color:${c}` }), l))) }),
      card(term('rx_drop', 'Da exploração para a validação'), 'Retorno médio nos dados antigos (●) e nos dados novos (◆), para quem fez as duas provas. Linha longa para a esquerda = perdeu força nos dados novos.', dumbbell())),
    det('rx-untested', `${rxHyps().filter((x) => !rxRow(x.id, 'exploration')).length} ideias que não chegaram ao backtest`,
      h('div', { class: 'tablewrap' }, simpleTable(['Hipótese', 'Família', 'Motivo', 'Registrada'], rxHyps().filter((x) => !rxRow(x.id, 'exploration')).map((x) => [x.id, humanName(x.family), x.invalid ? 'Código não seguia a regra registrada' : dropReason(x.status), dayUtc(x.proposed_at_utc)])))));
}
function rxHeader(eyebrow, title, text) { return h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, eyebrow), h('h1', { class: 'rx-h1' }, title), h('p', { class: 'rx-lede' }, text)); }
function scatterWrPayoff(rows) {
  const pr = rows.filter((r) => ok(r.winrate) && ok(r.payoff) && r.trades >= 10);
  if (!pr.length) return emptyState('Sem estratégias com dados suficientes.');
  const W = 720, H = 330, L = 44, R = 12, T = 12, B = 34;
  const ymax = Math.min(8, Math.max(3, ...pr.map((r) => r.payoff)) * 1.08), xmax = Math.max(70, ...pr.map((r) => r.winrate * 100)) * 1.04;
  const X = (x) => L + x / xmax * (W - L - R), Y = (y) => T + (1 - y / ymax) * (H - T - B);
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': 'Win rate contra payoff, uma bolha por estratégia', class: 'rx-chart' });
  for (const v of niceTicks(0, ymax, 5)) svg.append(sv('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), stroke: 'var(--line)' }), sv('text', { x: L - 6, y: Y(v) + 4, 'text-anchor': 'end' }, nfv.format(v)));
  for (const v of niceTicks(0, xmax, 7)) svg.append(sv('text', { x: X(v), y: H - 16, 'text-anchor': 'middle' }, nf0.format(v) + '%'));
  svg.append(sv('text', { x: W - R, y: H - 2, 'text-anchor': 'end' }, 'win rate →'), sv('text', { x: L + 4, y: T + 10 }, '↑ payoff'));
  let d = ''; for (let x = 10; x <= xmax; x += 0.5) { const y = (100 - x) / x; if (y <= ymax) d += (d ? 'L' : 'M') + X(x).toFixed(1) + ' ' + Y(y).toFixed(1); }
  svg.append(sv('path', { d, fill: 'none', stroke: 'var(--warn)', 'stroke-dasharray': '5 4', 'stroke-width': 1.4 }), sv('text', { x: X(60), y: Y(40 / 60) - 8, style: 'fill:var(--warn)' }, 'linha do empate'));
  const color = (r) => r.in_dryrun ? 'var(--teal)' : r.gates_all_pass ? 'var(--info)' : (r.roi_pct || 0) > 0 ? 'var(--muted)' : 'var(--bad)';
  const labeled = new Set([...pr].sort((a, b) => (b.roi_pct || 0) - (a.roi_pct || 0)).slice(0, 4).map((r) => r.id));
  for (const r of [...pr].sort((a, b) => b.trades - a.trades)) {
    const rad = Math.max(3.5, Math.min(13, Math.sqrt(r.trades) / 2.2)), cx = X(r.winrate * 100), cy = Y(Math.min(r.payoff, ymax)), c = color(r);
    svg.append(sv('circle', { cx: cx.toFixed(1), cy: cy.toFixed(1), r: rad.toFixed(1), fill: c, 'fill-opacity': 0.5, stroke: c, class: 'rx-dot',
      onclick: () => rxGo('#/strategy/' + r.id), onmousemove: (e) => showTip(e, `${r.id} · ${humanName(r.family)}`, [{ value: wr(r.winrate), label: ' win rate' }, { value: n2(r.payoff), label: ' payoff' }, { value: sp(r.roi_pct), label: ' retorno médio' }, { value: nf0.format(r.trades), label: ' operações' }]), onmouseleave: hideTip }));
    if (labeled.has(r.id)) svg.append(sv('text', { x: cx + rad + 4, y: cy + 4, style: 'fill:var(--ink2)' }, r.id));
  }
  return svg;
}
function dumbbell() {
  const pairs = rxRows('validation').map((v) => ({ v, e: rxRow(v.id, 'exploration') })).filter((x) => x.e && ok(x.e.roi_pct) && ok(x.v.roi_pct)).sort((a, b) => b.e.roi_pct - a.e.roi_pct);
  if (!pairs.length) return emptyState('Nenhuma estratégia fez a validação ainda.');
  const W = 720, rowH = 30, T = 20, B = 26, L = 150, R = 20, H = T + B + pairs.length * rowH;
  const vals = pairs.flatMap((x) => [x.e.roi_pct, x.v.roi_pct]), ticks = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals), 6), x0 = Math.min(ticks[0], ...vals), x1 = Math.max(ticks[ticks.length - 1], ...vals);
  const X = (x) => L + (x - x0) / ((x1 - x0) || 1) * (W - L - R);
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': 'Retorno na exploração contra a validação', class: 'rx-chart' });
  for (const t of ticks) svg.append(sv('line', { x1: X(t), x2: X(t), y1: T - 6, y2: H - B, stroke: t === 0 ? 'var(--line2)' : 'var(--line)' }), sv('text', { x: X(t), y: H - 8, 'text-anchor': 'middle' }, nf0.format(t) + '%'));
  pairs.forEach(({ e, v }, i) => {
    const y = T + i * rowH + rowH / 2, worse = v.roi_pct < e.roi_pct;
    svg.append(sv('text', { x: 8, y: y + 4, style: 'fill:var(--ink2)' }, `${e.id} ${humanName(e.family).slice(0, 16)}`),
      sv('line', { x1: X(e.roi_pct), x2: X(v.roi_pct), y1: y, y2: y, stroke: worse ? 'var(--bad)' : 'var(--good)', 'stroke-width': 2.5, 'stroke-opacity': 0.6 }),
      sv('circle', { cx: X(e.roi_pct), cy: y, r: 5, fill: 'var(--accent)' }),
      sv('rect', { x: X(v.roi_pct) - 5, y: y - 5, width: 10, height: 10, transform: `rotate(45 ${X(v.roi_pct)} ${y})`, fill: worse ? 'var(--bad)' : 'var(--good)' }),
      sv('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: 'transparent', class: 'rx-dot', onclick: () => rxGo('#/strategy/' + e.id),
        onmousemove: (ev) => showTip(ev, `${e.id} · ${humanName(e.family)}`, [{ value: sp(e.roi_pct), label: ' exploração (2017–2024)' }, { value: sp(v.roi_pct), label: ' validação (2024–2026)' }, { value: `${v.pairs_positive}/${v.n_pairs}`, label: ' ativos positivos na validação' }]), onmouseleave: hideTip }));
  });
  return svg;
}

/* ==================== Operações ==================== */
const GROUPS = [['hyp', 'Estratégia'], ['pair', 'Ativo'], ['reason', 'Motivo de saída'], ['dow', 'Dia da semana'], ['hour', 'Hora do dia'], ['dur', 'Duração'], ['year', 'Ano'], ['month', 'Mês'], ['none', 'Nenhum (operação a operação)']];
function opsFilter(I, st, skip = '') {
  const out = [];
  for (let i = 0; i < I.rows.length; i++) {
    const t = I.rows[i], c = I.cells[t[0]];
    if (st.stage !== 'all' && c.split !== st.stage) continue;
    if (st.hyp !== 'all' && c.id !== st.hyp) continue;
    if (st.pair !== 'all' && c.pair !== st.pair) continue;
    if (st.tf !== 'all' && I.tfOfCell[t[0]] !== st.tf) continue;
    if (st.res === 'win' ? t[3] <= 0 : st.res === 'loss' ? t[3] > 0 : false) continue;
    if (st.reason !== 'all' && I.reasons[t[5]] !== st.reason) continue;
    if (skip !== 'cell' && st.dow !== 'all' && I.dow[i] !== +st.dow) continue;
    if (skip !== 'cell' && st.hour !== 'all' && I.hour[i] !== +st.hour) continue;
    if (st.dur !== 'all' && durBucket(t[2]) !== +st.dur) continue;
    out.push(i);
  }
  return out;
}
function groupKey(I, g, i) {
  const t = I.rows[i], c = I.cells[t[0]];
  if (g === 'hyp') return c.id; if (g === 'pair') return c.pair; if (g === 'reason') return I.reasons[t[5]];
  if (g === 'dow') return I.dow[i]; if (g === 'hour') return I.hour[i]; if (g === 'dur') return durBucket(t[2]);
  const d = new Date(t[1] * 60000).toISOString(); return g === 'year' ? d.slice(0, 4) : d.slice(0, 7);
}
function groupLabel(g, k) {
  if (g === 'hyp') { const hy = rxHy(k); return h('div', { class: 'rx-name' }, h('span', { class: 'nowrap' }, h('a', { href: '#/strategy/' + encodeURIComponent(k) }, k), ' ', h('span', null, hy ? humanName(hy.family) : '')), hy ? statusDot(hy.status) : null); }
  if (g === 'pair') return h('b', null, short(k)); if (g === 'reason') return REASON(k); if (g === 'dow') return DOW[k];
  if (g === 'hour') return `${String(k).padStart(2, '0')}h`; if (g === 'dur') return DUR[k] ? DUR[k][2] : '?'; return String(k);
}
function pageOperacoes() {
  const I = tradeIndex();
  const head = rxHeader('Operações', 'Todas as operações dos backtests', 'Cada compra e venda simulada de todas as estratégias. Filtre e agrupe para ver quem acerta mais e quem lucra mais; escolha "Nenhum" em "Agrupar por" para ver operação a operação. Clique numa célula do mapa de dia e hora para filtrar.');
  if (!I) return h('div', { class: 'rx rx-stack' }, head, indexPending());
  const st = rx.ops, set = (k, v) => { st[k] = v; st.page = 0; render(); };
  const list = opsFilter(I, st), s = tradeStats(I, list);
  const ids = [...new Set(I.cells.map((c) => c.id))].sort(), reasons = [...new Set(I.rows.map((t) => t[5]))].map((k) => I.reasons[k]).sort();
  const controls = h('div', { class: 'rx-controls' },
    selectBox('Agrupar por', 'rx-og', st.group, GROUPS, (v) => { st.group = v; st.page = 0; st.sort = v === 'none' ? { key: 'p', dir: -1 } : { key: 'sum', dir: -1 }; render(); }),
    segmented('Prova', 'rx-os', st.stage, [['exploration', 'Exploração'], ['validation', 'Validação'], ['all', 'Ambas']], (v) => set('stage', v)),
    selectBox('Estratégia', 'rx-oh', st.hyp, [['all', 'Todas'], ...ids.map((id) => { const hy = rxHy(id); return [id, `${id} · ${hy ? humanName(hy.family) : ''}`]; })], (v) => set('hyp', v)),
    selectBox('Ativo', 'rx-op', st.pair, [['all', 'Todos'], ...(state.pairs || []).map((p) => [p, short(p)])], (v) => set('pair', v)),
    selectBox('Tempo gráfico', 'rx-otf', st.tf, [['all', 'Todos'], ...['15m', '1h', '4h', '1d'].map((x) => [x, x])], (v) => set('tf', v)),
    segmented('Resultado', 'rx-or', st.res, [['all', 'Todas'], ['win', 'Ganhos'], ['loss', 'Perdas']], (v) => set('res', v)),
    selectBox('Motivo de saída', 'rx-orz', st.reason, [['all', 'Todos'], ...reasons.map((r) => [r, REASON(r)])], (v) => set('reason', v)),
    selectBox('Duração', 'rx-odu', st.dur, [['all', 'Todas'], ...DUR.map((d, i) => [String(i), d[2]])], (v) => set('dur', v)),
    h('button', { type: 'button', 'data-fkey': 'rx-oreset', onclick: () => { Object.assign(st, { stage: 'exploration', hyp: 'all', pair: 'all', tf: 'all', res: 'all', reason: 'all', dow: 'all', hour: 'all', dur: 'all', page: 0 }); render(); } }, 'Limpar filtros'));
  const cellChip = st.dow !== 'all' || st.hour !== 'all' ? h('div', { class: 'rx-selbar' }, h('span', null, 'Filtrado pelo mapa: ', st.dow !== 'all' ? DOW[+st.dow] : 'todos os dias', ', ', st.hour !== 'all' ? `${st.hour}h` : 'todas as horas'), h('button', { type: 'button', 'data-fkey': 'rx-ocell', onclick: () => { st.dow = 'all'; st.hour = 'all'; render(); } }, 'Tirar filtro do mapa')) : null;
  const kpis = h('div', { class: 'rx-kpis' },
    rxKpi(term('rx_trades', 'Operações'), cnt(s.n, fmtInt)),
    rxKpi(term('rx_wr', 'Win rate'), wr(s.wr), `${nf0.format(s.wins)} ganhos de cada ${nf0.format(s.n)} · ${s.n ? nf0.format(Math.round(s.wr * 100)) : 0} de cada 100`),
    rxKpi(term('rx_avg', 'Média por operação'), signedSpan(s.avg, 2)),
    rxKpi(term('rx_payoff', 'Payoff'), n2(s.payoff), `ganho médio ${sp(s.aw, 2)} · perda média ${sp(s.al, 2)}`),
    rxKpi(term('pf', 'Profit factor'), h('span', { class: ok(s.pf) ? (s.pf >= 1 ? 'pos' : 'neg') : '' }, n2(s.pf))),
    rxKpi('Duração média', durText(s.dur)));
  let table;
  if (st.group !== 'none') {
    const groups = new Map(); for (const i of list) { const k = groupKey(I, st.group, i); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(i); }
    const rows = [...groups].map(([k, idx]) => ({ key: String(k), k, ...tradeStats(I, idx) }));
    const S = { n: pmax(rows.map((r) => r.n), 1), sum: pmax(rows.map((r) => r.sum)) };
    table = dataTable({ id: 'rx-ops-' + st.group, label: 'Operações agrupadas', sort0: { key: st.group === 'dow' || st.group === 'hour' || st.group === 'dur' ? 'k' : 'sum', dir: st.group === 'dow' || st.group === 'hour' || st.group === 'dur' ? 1 : -1 }, rows, cols: [
      { key: 'k', label: GROUPS.find((x) => x[0] === st.group)[1], val: (r) => typeof r.k === 'number' ? r.k : String(r.k), cell: (r) => groupLabel(st.group, r.k) },
      { key: 'n', label: 'Operações', num: true, val: (r) => r.n, cell: (r) => dbar(r.n, S.n, nf0.format(r.n), 'var(--muted)') },
      { key: 'wr', label: 'Win rate', term: 'rx_wr', num: true, val: (r) => r.wr, cell: (r) => dbar(r.wr, 1, wr(r.wr), 'var(--accent)') },
      { key: 'avg', label: 'Média por operação', term: 'rx_avg', num: true, val: (r) => r.avg, cell: (r) => signedSpan(r.avg, 2) },
      { key: 'sum', label: 'Resultado somado', term: 'rx_sum', num: true, val: (r) => r.sum, cell: (r) => dbar(r.sum, S.sum, signedSpan(r.sum, 1, true)) },
      { key: 'pf', label: 'Profit factor', term: 'pf', num: true, val: (r) => r.pf, cell: (r) => h('span', { class: ok(r.pf) ? (r.pf >= 1 ? 'pos' : 'neg') : '' }, n2(r.pf)) },
      { key: 'payoff', label: 'Payoff', term: 'rx_payoff', num: true, val: (r) => r.payoff, cell: (r) => n2(r.payoff) },
      { key: 'best', label: 'Melhor', num: true, val: (r) => r.best, cell: (r) => signedSpan(r.best) },
      { key: 'worst', label: 'Pior', num: true, val: (r) => r.worst, cell: (r) => signedSpan(r.worst) },
      { key: 'dur', label: 'Duração média', num: true, val: (r) => r.dur, cell: (r) => durText(r.dur) },
    ] });
  } else table = tradeList(I, list, st);
  return h('div', { class: 'rx rx-stack' + rxAnim() }, head, controls, cellChip, kpis,
    card('Calendário de resultados', 'Cada quadradinho é um dia (data de fechamento, horário de Brasília), com os filtros acima. Verde: o dia somou lucro; vermelho: prejuízo; cinza: nenhuma operação fechou. Embaixo, o total de cada mês.', calendarHeat(I, list, st)),
    table,
    h('p', { class: 'sub' }, '"Resultado somado" usa % do capital de cada backtest (100 USDT antes de 08/11/2026, 1.000 depois), então estratégias com capitais diferentes ficam comparáveis. Tudo é backtest simulado, cenário de custo base.'),
    h('div', { class: 'rx-grid g2' },
      card(term('rx_hour', 'Quando as operações funcionam'), 'Entradas por dia da semana e hora (horário de Brasília), com os outros filtros acima. Clique numa célula para filtrar a página.', weekHour(I, opsFilter(I, st, 'cell'), st, true)),
      card('Como os resultados se distribuem', 'Quantas operações caíram em cada faixa de resultado. Estratégias de tendência costumam ter muitas perdas pequenas e poucos ganhos grandes (cauda à direita).', histogramOf(I, list))));
}
function tradeList(I, list, st) {
  const per = 50, sorters = { date: (i) => I.rows[i][1], p: (i) => I.rows[i][3], a: (i) => I.rows[i][4], d: (i) => I.rows[i][2] };
  const key = sorters[st.sort.key] ? st.sort.key : 'p', dir = st.sort.dir, f = sorters[key];
  const sorted = list.slice().sort((x, y) => (f(x) - f(y)) * dir), pages = Math.max(1, Math.ceil(sorted.length / per));
  st.page = Math.min(st.page, pages - 1);
  const th = (k, label, num) => h('th', { class: num ? 'num' : '', 'aria-sort': sorters[k] ? (key === k ? (dir > 0 ? 'ascending' : 'descending') : 'none') : null },
    sorters[k] ? h('button', { type: 'button', class: 'sortbtn', 'data-fkey': 'rxts:' + k, onclick: () => { st.sort = { key: k, dir: key === k ? -dir : -1 }; st.page = 0; render(); } }, label + (key === k ? (dir > 0 ? ' ▴' : ' ▾') : '')) : label);
  return h('div', { class: 'rx-stack' }, h('div', { class: 'tablewrap' }, h('table', { 'aria-label': 'Operações' },
    h('thead', null, h('tr', null, th('date', 'Entrada'), th('', 'Estratégia'), th('', 'Ativo'), th('', 'Prova'), th('d', 'Duração', true), th('p', 'Resultado', true), th('a', 'Em USDT', true), th('', 'Saída'))),
    h('tbody', null, sorted.slice(st.page * per, (st.page + 1) * per).map((i) => { const t = I.rows[i], c = I.cells[t[0]];
      return h('tr', null, h('td', { class: 'nw' }, dayUtc(new Date(t[1] * 60000).toISOString())), h('td', null, h('a', { href: '#/strategy/' + c.id }, c.id)), h('td', null, short(c.pair)), h('td', null, RX_STAGE[c.split]),
        h('td', { class: 'num' }, durText(t[2])), h('td', { class: 'num' }, signedSpan(t[3], 2, true)), h('td', { class: 'num' }, h('span', { class: toneOf(t[4]) }, n2(t[4]))), h('td', null, REASON(I.reasons[t[5]]),
        ' ', h('a', { href: '#/chart/' + encodeURIComponent(c.experiment_id), class: 'sub', title: 'Ver os candles deste backtest' }, 'gráfico'))); })))),
    h('div', { class: 'rx-pager' }, h('span', { class: 'sub' }, `${nf0.format(sorted.length)} operações · página ${st.page + 1} de ${pages}`),
      h('button', { type: 'button', disabled: st.page === 0, 'data-fkey': 'rx-prev', onclick: () => { st.page--; render(); } }, 'Anterior'),
      h('button', { type: 'button', disabled: st.page + 1 >= pages, 'data-fkey': 'rx-next', onclick: () => { st.page++; render(); } }, 'Próxima')));
}
function weekHour(I, list, st, interactive) {
  const cells = Array.from({ length: 7 }, () => Array.from({ length: 24 }, () => []));
  for (const i of list) cells[I.dow[i]][I.hour[i]].push(i);
  const metric = st.metric || 'wr', vals = cells.map((row) => row.map((idx) => idx.length ? tradeStats(I, idx) : null));
  const value = (s) => !s ? null : metric === 'wr' ? (s.wr - 0.5) * 100 : metric === 'avg' ? s.avg : s.n;
  const scale = metric === 'n' ? Math.max(1, ...vals.flat().map((s) => s ? s.n : 0)) : metric === 'wr' ? 25 : Math.max(0.5, ...vals.flat().map((s) => s && ok(s.avg) ? Math.abs(s.avg) : 0));
  const bg = (s) => !s ? 'transparent' : metric === 'n' ? `color-mix(in srgb, var(--accent) ${Math.round(s.n / scale * 60 + 5)}%, transparent)` : heatBg(value(s), scale);
  const order = [1, 2, 3, 4, 5, 6, 0];
  const grid = h('div', { class: 'rx-wh', role: 'table', 'aria-label': 'Operações por dia da semana e hora' },
    h('span', null), Array.from({ length: 24 }, (_, hr) => h('span', { class: 'hd' }, hr % 3 ? '' : String(hr).padStart(2, '0'))),
    order.map((d) => [h('span', { class: 'dl' }, DOW[d]), vals[d].map((s, hr) => {
      const on = st.dow === String(d) && st.hour === String(hr);
      return h(interactive ? 'button' : 'span', { type: interactive ? 'button' : null, class: 'c' + (on ? ' on' : ''), style: `background:${bg(s)}`, 'aria-label': `${DOW[d]} ${hr}h: ${s ? `${s.n} operações, win rate ${wr(s.wr)}` : 'sem operações'}`,
        onmousemove: (e) => showTip(e, `${DOW[d]}, ${String(hr).padStart(2, '0')}h (Brasília)`, s ? [{ value: nf0.format(s.n), label: ' operações' }, { value: wr(s.wr), label: ' win rate' }, { value: sp(s.avg, 2), label: ' média por operação' }] : [{ value: '—', label: ' sem operações' }]),
        onmouseleave: hideTip, onclick: interactive ? () => { if (on) { st.dow = 'all'; st.hour = 'all'; } else { st.dow = String(d); st.hour = String(hr); } st.page = 0; render(); } : null });
    })]));
  return h('div', { class: 'rx-stack' }, segmented('Cor mostra', 'rx-whm-' + (interactive ? 'o' : 's'), metric, [['wr', 'Win rate'], ['avg', 'Média por operação'], ['n', 'Quantidade']], (v) => { st.metric = v; render(); }),
    h('div', { class: 'tablewrap' }, grid),
    h('p', { class: 'sub' }, metric === 'wr' ? 'Verde: acerta mais de 50 de cada 100 naquela hora; vermelho: menos.' : metric === 'avg' ? 'Verde: em média lucrou naquela hora; vermelho: perdeu.' : 'Mais forte: mais entradas naquela hora.'));
}
function histogramOf(I, list) {
  const bins = Array.from({ length: 20 }, (_, i) => ({ lo: i - 10, n: 0 }));
  for (const i of list) bins[Math.max(0, Math.min(19, Math.floor(I.rows[i][3]) + 10))].n++;
  const W = 720, H = 190, L = 44, B = 24, T = 8, m = Math.max(1, ...bins.map((b) => b.n)), bw = (W - L - 8) / bins.length;
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': 'Distribuição do resultado por operação', class: 'rx-chart' });
  for (const v of niceTicks(0, m, 4)) { const y = T + (1 - v / m) * (H - T - B); svg.append(sv('line', { x1: L, x2: W - 8, y1: y, y2: y, stroke: 'var(--line)' }), sv('text', { x: L - 6, y: y + 4, 'text-anchor': 'end' }, compact(v))); }
  bins.forEach((b, i) => { const hh = b.n / m * (H - T - B), x = L + i * bw;
    svg.append(sv('rect', { x: (x + 1).toFixed(1), y: (H - B - hh).toFixed(1), width: (bw - 2).toFixed(1), height: hh.toFixed(1), rx: 2, fill: b.lo < 0 ? 'var(--bad)' : 'var(--good)', 'fill-opacity': 0.7,
      onmousemove: (e) => showTip(e, b.lo === -10 ? 'até −9%' : b.lo === 9 ? '+9% ou mais' : `${b.lo}% a ${b.lo + 1}%`, [{ value: nf0.format(b.n), label: ' operações' }]), onmouseleave: hideTip }));
    if (i % 2 === 0) svg.append(sv('text', { x: x + bw / 2, y: H - 8, 'text-anchor': 'middle' }, b.lo === -10 ? '≤−10%' : sgn((b.lo > 0 ? '+' : '') + b.lo) + '%')); });
  return svg;
}

/* ==================== Comparar ==================== */
function pageComparar() {
  const st = rx.cmp, fromQ = idList(route.q.ids);
  if (fromQ.length) st.ids = fromQ.slice(0, 4);
  if (!st.ids) st.ids = [...rxRows('exploration')].filter((r) => (r.min_trades_pair || 0) >= rxMin()).sort((a, b) => (b.roi_pct || 0) - (a.roi_pct || 0)).slice(0, 3).map((r) => r.id);
  const rows = st.ids.map((id) => rxRow(id, st.stage)).filter(Boolean), color = (i) => rxSeries(i);
  const M = [['Situação', null, (r) => h('span', { class: 'row' }, statusBadge(r.status), r.in_dryrun ? dryBadge() : null)], ['Tempo gráfico', null, (r) => tfOf(rxHy(r.id)) || '?'],
    [term('rx_score', 'Nota'), (r) => r.score, (r) => scoreCell(r)], [term('rx_risk', 'Risco'), (r) => -(riskOf(r.max_dd_pct) || 99), (r) => riskBadge(r.max_dd_pct)],
    [term('rx_ret', 'Retorno médio'), (r) => r.roi_pct, (r) => signedSpan(r.roi_pct, 1, true)], [term('rx_stress', 'Com custo alto'), (r) => r.roi_stress_pct, (r) => signedSpan(r.roi_stress_pct)],
    [term('rx_wr', 'Win rate'), (r) => r.winrate, (r) => wr(r.winrate)], [term('rx_payoff', 'Payoff'), (r) => r.payoff, (r) => n2(r.payoff)], [term('pf', 'Profit factor'), (r) => r.profit_factor, (r) => n2(r.profit_factor)],
    [term('rx_dd', 'Pior queda'), (r) => ok(r.max_dd_pct) ? -r.max_dd_pct : null, (r) => ddText(r.max_dd_pct)], [term('rx_trades', 'Operações'), (r) => r.trades, (r) => nf0.format(r.trades)],
    [term('rx_avg', 'Média por operação'), (r) => r.expectancy_pct, (r) => signedSpan(r.expectancy_pct, 2)], ['Duração média', null, (r) => durText((r.avg_duration_h || 0) * 60)],
    [term('rx_pairs', 'Ativos positivos'), (r) => r.pairs_positive / Math.max(1, r.n_pairs), (r) => `${r.pairs_positive}/${r.n_pairs}`], ['Aprovada em', (r) => Object.values(r.decisions || {}).filter((d) => d === 'candidate_for_portfolio').length / Math.max(1, r.n_pairs), (r) => `${Object.values(r.decisions || {}).filter((d) => d === 'candidate_for_portfolio').length}/${r.n_pairs} ativos`]];
  const options = rxRows(st.stage).filter((r) => !st.ids.includes(r.id)).sort((a, b) => a.id.localeCompare(b.id));
  return h('div', { class: 'rx rx-stack' + rxAnim() },
    rxHeader('Comparar', 'Estratégias lado a lado', 'Escolha até quatro estratégias (ou marque no Ranking). As curvas mostram o resultado acumulado na média dos ativos; na tabela, o melhor valor de cada linha fica destacado.'),
    h('div', { class: 'rx-controls' }, segmented('Prova', 'rx-cs', st.stage, [['exploration', 'Exploração'], ['validation', 'Validação']], (v) => { st.stage = v; render(); }),
      h('div', { class: 'rx-pick' }, st.ids.map((id, i) => h('span', { class: 'p' }, h('i', { style: `background:${color(i)}` }), id, h('button', { type: 'button', 'aria-label': 'Remover ' + id, 'data-fkey': 'rxrm:' + id, onclick: () => { st.ids = st.ids.filter((x) => x !== id); if (route.q.ids) rxGo('#/compare'); else render(); } }, '×'))),
        st.ids.length < 4 ? selectBox('Adicionar', 'rx-cadd', '', [['', '+ estratégia'], ...options.map((r) => [r.id, `${r.id} · ${humanName(r.family)}`])], (v) => { if (v) { st.ids = [...st.ids, v]; if (route.q.ids) rxGo('#/compare'); else render(); } }) : null)),
    st.ids.length > rows.length ? h('p', { class: 'sub' }, `${st.ids.length - rows.length} das escolhidas não têm resultado na ${RX_STAGE[st.stage].toLowerCase()}.`) : null,
    rows.length ? [
      h('div', { class: 'rx-gallery' }, rows.map((r, i) => h('div', { class: 'rx-cmpcard', style: `--c:${color(i)}` }, stratCard(r, { i })))),
      card('Resultado acumulado', `${RX_STAGE[st.stage]} (${RX_PERIOD[st.stage]}): soma dos resultados em % do capital, na média dos ativos de cada estratégia.`, rxLine(rows.map((r, i) => ({ label: r.id, color: color(i), pts: r.curve })), { label: 'Resultado acumulado comparado' }),
        { actions: h('div', { class: 'legend' }, rows.map((r, i) => h('span', null, h('span', { class: 'key', style: `border-top-color:${color(i)}` }), r.id))) }),
      card(term('rx_underwater', 'Queda desde o pico'), 'Quanto cada estratégia ficou abaixo do seu melhor momento. Mais fundo e mais longo é mais difícil de aguentar.', rxLine(rows.map((r, i) => ({ label: r.id, color: color(i), pts: underwater(r.curve) })), { height: 200, label: 'Queda desde o pico comparada' })),
      h('div', { class: 'tablewrap' }, h('table', { class: 'rx-cmp' }, h('thead', null, h('tr', null, h('th', null, 'Métrica'), rows.map((r, i) => h('th', null, h('span', { style: `color:${color(i)}` }, '● '), h('a', { href: '#/strategy/' + r.id }, r.id), h('div', { class: 'sub' }, humanName(r.family)))))),
        h('tbody', null, M.map(([label, val, cell]) => { const vs = val ? rows.map(val) : [], best = val ? Math.max(...vs.filter(ok)) : null, tie = vs.filter((x) => x === best).length === rows.length;
          return h('tr', null, h('td', null, label), rows.map((r, i) => h('td', { class: 'num' + (val && rows.length > 1 && !tie && vs[i] === best ? ' rx-best' : '') }, cell(r)))); }))))] : emptyState('Escolha ao menos uma estratégia.'));
}

/* ==================== Estratégia (relatório de uma página) ==================== */
const CRISES = [['Bear de 2018', '2018-01-07', '2018-12-15'], ['Crash da covid', '2020-02-13', '2020-03-16'], ['Alta de 2020–21', '2020-10-01', '2021-04-14'],
  ['Queda de maio/2021', '2021-05-10', '2021-07-20'], ['Bear de 2022 (LUNA e FTX)', '2022-03-29', '2022-11-21'], ['Alta de 2023–24', '2023-10-01', '2024-03-14']];
function pageEstrategia(idArg) {
  const id = idArg || ((state.strategies || [])[0] || {}).id;
  const hy = id && rxHy(id);
  if (!hy) return h('div', { class: 'rx rx-stack' }, rxHeader('Estratégia', 'Não encontrada', `Não existe ${id || 'estratégia'} no registro.`), h('a', { href: '#/leaderboard' }, '← Ranking'));
  const stages = ['exploration', 'validation'].filter((s) => rxRow(id, s));
  const sentence = String(hy.notes || '').split(/ Calibrated| \[/)[0];
  const exp = rxRow(id, 'exploration'), val = rxRow(id, 'validation'), parts = (exp && exp.score_parts) || {};
  return h('div', { class: 'rx rx-stack' + rxAnim() },
    h('div', { class: 'sub' }, h('a', { href: '#/leaderboard', 'data-fkey': 'rx-back' }, '← Ranking'), ' / ', id),
    h('section', { class: 'card rx-shero' + (hy.in_dryrun ? ' beam' : '') },
      h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, [id, tfOf(hy) || '?', 'registrada em ' + dayUtc(hy.proposed_at_utc)].join(' · ')), h('h1', { class: 'rx-h1' }, humanName(hy.family)),
        h('div', { class: 'row' }, statusBadge(hy.status), hy.in_dryrun ? dryBadge() : null),
        h('p', { class: 'rx-lede' }, RXS[statusKey(hy.status)].why, sentence ? ' A ideia: ' + sentence + '.' : '', ' ', h('span', { class: 'sub' }, '(descrição registrada em inglês)')),
        exp ? h('div', { class: 'rx-shero-nums' },
          h('div', null, h('span', { class: 'l' }, term('rx_explo', 'Exploração'), ' · 2017–2024'), h('b', { class: toneOf(exp.roi_pct) + ' rx-glow' }, cnt(exp.roi_pct, (v) => sp(v, 1)))),
          val ? h('span', { class: 'rx-arrow', 'aria-hidden': 'true' }, '→') : null,
          val ? h('div', null, h('span', { class: 'l' }, term('rx_valid', 'Validação'), ' · 2024–2026'), h('b', { class: toneOf(val.roi_pct) + ' rx-glow' }, cnt(val.roi_pct, (v) => sp(v, 1)))) : null,
          val && ok(perYear(exp)) && ok(perYear(val)) ? h('div', { class: 'rx-delta ' + (perYear(val) >= perYear(exp) ? 'up' : 'down') }, h('span', { class: 'l' }, term('rx_annual', 'Por ano')),
            h('b', null, `${sp(perYear(exp), 1)} → ${sp(perYear(val), 1)}`)) : null,
          h('div', null, h('span', { class: 'l' }, term('rx_risk', 'Risco')), riskMeter(exp.max_dd_pct))) : null,
        exp && val ? h('div', { class: 'rx-chg', 'aria-label': 'Da exploração para a validação' }, [
          ['Win rate', wr(exp.winrate), wr(val.winrate), exp.winrate, val.winrate], ['Payoff', n2(exp.payoff), n2(val.payoff), exp.payoff, val.payoff],
          ['Ativos aprovados', `${approvedOf(exp)}/${exp.n_pairs}`, `${approvedOf(val)}/${val.n_pairs}`, approvedOf(exp) / Math.max(1, exp.n_pairs), approvedOf(val) / Math.max(1, val.n_pairs)],
          ['Com custo alto', sp(exp.roi_stress_pct, 0), sp(val.roi_stress_pct, 0), exp.roi_stress_pct, val.roi_stress_pct]]
          .map(([l, a, b, x, y]) => h('span', { class: 'rx-chip' + (ok(x) && ok(y) ? (y >= x ? ' up' : ' down') : '') }, h('small', null, l), h('span', null, a), h('i', { 'aria-hidden': 'true' }, ok(x) && ok(y) ? (y >= x ? '↗' : '↘') : '→'), h('b', null, b)))) : null),
      exp ? h('div', { class: 'rx-shero-side' },
        h('div', { class: 'rx-part' }, ring(ok(exp.score) ? exp.score / 100 : 0, { size: 112, stroke: 10, text: ok(exp.score) ? nf0.format(exp.score) : dash, sub: 'de 100', label: `Nota de evidência ${ok(exp.score) ? nf0.format(exp.score) : 'sem nota'} de 100` }), h('small', null, term('rx_score', 'Nota de evidência'))),
        h('div', { class: 'rx-parts' }, PARTS.map(([k, l]) => h('div', { class: 'rx-part' }, ring(parts[k] || 0, { size: 54, stroke: 5, color: 'var(--teal)', text: nf0.format((parts[k] || 0) * 100), label: `${l}: ${nf0.format((parts[k] || 0) * 100)} de 100` }), h('small', null, l))))) : null),
    stages.length ? h('div', { class: 'rx-stack' }, h('div', { class: 'rx-stagebar' }, h('h2', null, 'Relatório da prova'),
        stages.length > 1 ? segmented('Prova', 'rx-ss', rx.st.stage && stages.includes(rx.st.stage) ? rx.st.stage : stages[0], stages.map((s) => [s, `${RX_STAGE[s]} · ${RX_PERIOD[s]}`]), (v) => { rx.st.stage = v; render(); })
          : h('span', { class: 'sub' }, `${RX_STAGE[stages[0]]} · ${RX_PERIOD[stages[0]]}`)),
      stageReport(hy, rxRow(id, rx.st.stage && stages.includes(rx.st.stage) ? rx.st.stage : stages[0])))
      : card('Sem backtest completo', null, emptyState(hy.invalid ? 'Código não seguia a regra registrada.' : dropReason(hy.status) + '.')),
    det('rx-rule', 'Regra exata registrada antes do teste', h('p', { class: 'rx-rule' }, hy.rule || '—')));
}
function stageReport(hy, r) {
  const I = tradeIndex(), costs = SCENARIOS.map(([k, lab]) => { const cells = hy.cells.filter((c) => c.split === r.stage); const v = cells.map((c) => c.profit_by_cost && ok(c.profit_by_cost[k]) ? c.profit_by_cost[k] / (c.wallet || 100) * 100 : null).filter(ok); return { label: lab[0].toUpperCase() + lab.slice(1), v: v.length ? v.reduce((a, b) => a + b, 0) / v.length : null }; });
  const bh = (() => { const v = r.per_pair.map((p) => (hy.cells.find((c) => c.experiment_id === p.experiment_id) || {}).buy_and_hold_pct).filter(ok); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; })();
  const list = I ? opsFilter(I, { stage: r.stage, hyp: r.id, pair: 'all', tf: 'all', res: 'all', reason: 'all', dow: 'all', hour: 'all', dur: 'all' }) : null;
  const pairCols = [
    { key: 'pair', label: 'Ativo', val: (p) => p.pair, cell: (p) => h('span', { class: 'nowrap' }, h('span', { class: 'key', style: `border-top-color:${rxPairColor(p.pair)}` }), short(p.pair)) },
    { key: 'dec', label: 'Decisão', val: (p) => p.decision, cell: (p) => badge(p.decision === 'candidate_for_portfolio' ? { icon: '✓', cls: 'good', label: 'Aprovada' } : p.decision === 'rejected' ? { icon: '✕', cls: 'bad', label: 'Reprovada' } : { icon: '?', cls: 'warn', label: 'Inconclusiva' }) },
    { key: 'trades', label: 'Operações', num: true, val: (p) => p.trades, cell: (p) => nf0.format(p.trades) },
    { key: 'wr', label: 'Win rate', term: 'rx_wr', num: true, val: (p) => p.winrate, cell: (p) => wr(p.winrate) },
    { key: 'roi', label: 'Retorno', term: 'rx_ret', num: true, val: (p) => p.roi_pct, cell: (p) => signedSpan(p.roi_pct, 1, true) },
    { key: 'stress', label: 'Com custo alto', term: 'rx_stress', num: true, val: (p) => p.roi_stress_pct, cell: (p) => signedSpan(p.roi_stress_pct) },
    { key: 'dd', label: 'Pior queda', term: 'rx_dd', num: true, val: (p) => ok(p.max_dd_pct) ? -p.max_dd_pct : null, cell: (p) => ddText(p.max_dd_pct) },
    { key: 'bh', label: 'Comprar e segurar', term: 'rx_bh', num: true, val: (p) => (hy.cells.find((c) => c.experiment_id === p.experiment_id) || {}).buy_and_hold_pct, cell: (p) => sp((hy.cells.find((c) => c.experiment_id === p.experiment_id) || {}).buy_and_hold_pct, 0) },
    { key: 'go', label: '', cell: (p) => h('span', { class: 'row' }, h('a', { href: '#/chart/' + encodeURIComponent(p.experiment_id) }, 'Gráfico'), h('a', { href: '#/experiments/' + encodeURIComponent(p.experiment_id) }, 'Critérios')) },
  ];
  const failing = [...new Set(hy.cells.filter((c) => c.split === r.stage).flatMap((c) => (c.failing_gates || []).map((g) => GATE[g.gate] || g.gate)))];
  return h('div', { class: 'rx-stack' },
    h('p', { class: 'sub' }, `${RX_STAGE[r.stage]}, ${RX_PERIOD[r.stage]}. `, r.gates_all_pass ? 'Aprovada em todos os ativos.' : `Aprovada em ${Object.values(r.decisions).filter((d) => d === 'candidate_for_portfolio').length} de ${r.n_pairs} ativos.`, failing.length ? ` Critérios que barraram: ${listPt(failing)}.` : ''),
    h('div', { class: 'rx-kpis' },
      rxKpi(term('rx_ret', 'Retorno médio'), signedSpan(r.roi_pct, 1), h('span', null, term('rx_bh', 'comprar e segurar'), ': ', sp(bh, 0))),
      rxKpi(term('rx_wr', 'Win rate'), wr(r.winrate), `${nf0.format(r.wins ?? Math.round((r.winrate || 0) * r.trades))} de ${nf0.format(r.trades)} operações`),
      rxKpi(term('rx_payoff', 'Payoff'), n2(r.payoff), `ganho ${sp(r.avg_win_pct, 2)} · perda ${sp(r.avg_loss_pct, 2)}`),
      rxKpi(term('pf', 'Profit factor'), h('span', { class: ok(r.profit_factor) ? (r.profit_factor >= 1 ? 'pos' : 'neg') : '' }, n2(r.profit_factor))),
      rxKpi(term('rx_dd', 'Pior queda'), ddText(r.max_dd_pct), riskBadge(r.max_dd_pct)),
      rxKpi(term('rx_stress', 'Com custo alto'), signedSpan(r.roi_stress_pct, 1))),
    card('Resultado acumulado e queda desde o pico', 'Em cima: soma dos resultados em % do capital, na média dos ativos. Embaixo: quanto o capital estava abaixo do seu melhor momento.',
      h('div', { class: 'rx-stack' }, rxLine([{ label: r.id, color: 'var(--accent)', pts: r.curve }], { fill: true, label: 'Resultado acumulado' }), rxLine([{ label: 'queda', color: 'var(--bad)', pts: underwater(r.curve) }], { height: 150, area: true, label: 'Queda desde o pico' })),
      { actions: h('a', { href: '#/trades', 'data-fkey': 'rx-goops', onclick: () => { Object.assign(rx.ops, { stage: r.stage, hyp: r.id, pair: 'all', tf: 'all', res: 'all', reason: 'all', dow: 'all', hour: 'all', dur: 'all', group: 'pair', page: 0 }); } }, `Ver as ${nf0.format(r.trades)} operações →`) }),
    h('div', { class: 'rx-stack' },
      card('Capital por ativo', 'Saldo de cada criptomoeda, em % do capital inicial do backtest.', rxLine(hy.cells.filter((c) => c.split === r.stage && c.equity).map((c) => ({ label: short(c.pair), color: rxPairColor(c.pair), pts: c.equity.map(([t, v]) => [t, v / (c.wallet || 100) * 100 - 100]) })), { height: 240, label: 'Capital por ativo' }),
        { actions: h('div', { class: 'legend' }, hy.cells.filter((c) => c.split === r.stage).map((c) => h('span', null, h('span', { class: 'key', style: `border-top-color:${rxPairColor(c.pair)}` }), short(c.pair)))) }),
      card('Mês a mês', 'Resultado de cada mês em % do capital (média dos ativos). Verde é lucro, vermelho é prejuízo.', monthGrid(r.monthly))),
    h('div', { class: 'rx-grid g2' },
      card('De cada 100 operações', 'Cada quadradinho é uma operação, em escala de 100. Verde fechou no lucro; vermelho, no prejuízo.', h('div', { class: 'rx-wf' }, waffle(r.winrate),
        h('div', { class: 'rx-wf-txt' },
          h('p', null, h('b', { class: 'pos' }, `${ok(r.winrate) ? Math.round(r.winrate * 100) : 0} ganham`), ' e ', h('b', { class: 'neg' }, `${ok(r.winrate) ? 100 - Math.round(r.winrate * 100) : 0} perdem`), '.'),
          h('p', { class: 'sub' }, `Quando ganha, ganha em média ${sp(r.avg_win_pct, 2)}; quando perde, perde ${sp(r.avg_loss_pct, 2)}. `,
            ok(r.payoff) ? (r.payoff >= 1 ? `Cada ganho vale ${nfv.format(r.payoff)} vezes uma perda: é isso que decide o resultado, não só o acerto.` : `Cada ganho vale menos que uma perda (payoff ${nfv.format(r.payoff)}): precisa acertar muito para lucrar.`) : '')))),
      card('Quanto as taxas pesam', 'Retorno médio refeito com quatro níveis de custo, do mais barato ao pior caso.', hbars(costs.map((c) => ({ label: c.label, v: c.v, color: (c.v || 0) >= 0 ? 'var(--good)' : 'var(--bad)', tone: toneOf(c.v) })), (v) => sp(v)))),
    card('Nos grandes movimentos do cripto', 'Resultado médio por ativo nas fases marcantes do mercado (datas aproximadas). Mostra como a regra se comporta em pânico e em euforia.', crisisTable(I, list, r)),
    h('div', { class: 'rx-grid g2' },
      card(term('rx_hour', 'Quando funciona'), 'Entradas por dia da semana e hora (horário de Brasília).', I ? weekHour(I, list, rx.ops, false) : indexPending()),
      card('Como as operações terminam', 'Motivo de saída de cada operação.', hbars(Object.entries(r.exit_reasons || {}).slice(0, 7).map(([k, v]) => ({ label: REASON(k), v }))))),
    card('Por ativo', null, dataTable({ id: 'rx-pairs-' + r.key, cols: pairCols, rows: r.per_pair.map((p) => ({ ...p, key: p.experiment_id })), sort0: { key: 'roi', dir: -1 }, label: 'Resultado por ativo' })));
}
function monthGrid(monthly) {
  if (!monthly || !monthly.length) return emptyState('Sem resultados mensais.');
  const by = {}; for (const [ym, v] of monthly) { const [y, m] = ym.split('-'); (by[y] = by[y] || {})[+m] = v; }
  const years = Object.keys(by).sort(), MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  return h('div', { class: 'tablewrap' }, h('table', { class: 'rx-month' }, h('thead', null, h('tr', null, h('th', null, 'Ano'), MES.map((m) => h('th', { class: 'num' }, m)), h('th', { class: 'num' }, 'Ano'))),
    h('tbody', null, years.map((y) => { const tot = Object.values(by[y]).reduce((a, b) => a + (b || 0), 0);
      return h('tr', null, h('th', null, y), MES.map((_, i) => { const v = by[y][i + 1]; return h('td', { class: 'num', style: `background:${heatBg(v, 8)}`, title: ok(v) ? `${MES[i]}/${y}: ${sp(v, 2)}` : 'sem operações fechadas' }, ok(v) ? sgn(nf1.format(v)) : ''); }),
        h('td', { class: 'num', style: `background:${heatBg(tot, 25)};font-weight:600` }, sp(tot))); }))));
}
function crisisTable(I, list, r) {
  if (!I) return indexPending();
  const nCells = Math.max(1, r.n_pairs);
  return h('div', { class: 'tablewrap' }, simpleTable(['Fase', 'Período', 'Operações', 'Win rate', 'Por ativo'], CRISES.map(([name, a, b]) => {
    const t0 = Date.parse(a + 'T00:00:00Z') / 60000, t1 = Date.parse(b + 'T23:59:59Z') / 60000;
    const sel = list.filter((i) => { const t = I.rows[i]; const close = t[1] + t[2]; return close >= t0 && close <= t1; });
    if (!sel.length) return [name, `${dayUtc(a + 'T00:00:00Z')} a ${dayUtc(b + 'T00:00:00Z')}`, '0', dash, h('span', { class: 'sub' }, 'fora do período ou sem operações')];
    const s = tradeStats(I, sel);
    return [name, `${dayUtc(a + 'T00:00:00Z')} a ${dayUtc(b + 'T00:00:00Z')}`, nf0.format(s.n), wr(s.wr), signedSpan(s.sum / nCells, 1, true)];
  }), [2, 3, 4]));
}
