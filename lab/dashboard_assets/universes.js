/* ==================== Universos: as mesmas páginas de Resultados para Cripto, B3 (WIN/WDO) e Substitutos ====================
   Inlined into the page's script by lab.dashboard.render_page (right after results.js), so it shares the page helpers, the
   state and the CSP nonce. Strings only become text nodes.

   Owner, 2026-11-16: "a seção que estava usando para os cripto, a seção para esses novos ativos, mini índice, mini
   dólar, também para os outros que vão entrar". Each universe (lab/universes.py) ships the SAME structures the crypto
   pages read (hypotheses, strategies, experiments, trade index), so Início, Ranking, Operações, Comparar, Estratégia
   and the candle chart run unchanged: inUniverse(id, fn) swaps those keys of `state` while the page is drawn.
   A new universe = one entry in lab/universes.py UNIVERSES + one in UX_META below (its routes are generated). */

let UNI = 'crypto';
const UX_META = {
  b3: { group: 'B3: WIN e WDO', short: 'B3', title: 'B3 (WIN/WDO)', unit: '% do valor de 1 contrato', markets: 'contratos',
    chart: 'Operações do backtest no motor da B3 (o mesmo do robô), sobre os candles de 15 minutos do WIN$N e do WDO$N exportados da conta de demonstração da Clear. Preços em pontos, sem ajuste de rolagem; resultados em % do valor de 1 contrato, já com os custos do cenário base em reais. Histórico simulado: nenhuma ordem foi enviada.' },
  proxies: { group: 'Substitutos', short: 'Substitutos', title: 'Substitutos (EUA e DAX)', unit: '% do valor de 1 unidade', markets: 'mercados',
    chart: 'Operações do backtest no motor da B3, sobre os candles da MetaQuotes-Demo (índices dos EUA, DAX e câmbio), que serviram de ponte antes dos dados da B3. Resultados em % do valor de 1 unidade, custo base. Histórico simulado.' },
};
const UX_PAGES = [['overview', 'Início'], ['leaderboard', 'Ranking'], ['trades', 'Operações'], ['compare', 'Comparar'], ['strategy', 'Estratégia'], ['chart', 'Gráfico']];
const UX_ROUTE = Object.fromEntries(Object.keys(UX_META).map((u) => [u, Object.fromEntries(UX_PAGES.map(([p]) => [p, p === 'overview' ? u : `${u}-${p}`]))]));
/* the crypto Resultados route of a page, in the current universe ('experiments' has no universe twin: the chart) */
const rxR = (page) => '#/' + (UNI === 'crypto' ? page : (UX_ROUTE[UNI][page] || UX_ROUTE[UNI][page === 'experiments' ? 'chart' : 'overview']));
const UX = {};
const uxCur = () => (UNI === 'crypto' ? null : (UX[UNI] && UX[UNI].data));
const rxPeriod = (s) => { const d = uxCur(); return d && d.periods ? (d.periods[s] || s) : RX_PERIOD[s]; };
const rxMarkets = () => (UNI === 'crypto' ? 'criptomoedas' : UX_META[UNI].markets);
const rxUnitLabel = () => (UNI === 'crypto' ? 'Em USDT' : 'Em % do contrato');
const rxCapNote = () => (UNI === 'crypto' ? '"Resultado somado" usa % do capital de cada backtest (100 USDT antes de 08/11/2026, 1.000 depois)'
  : `"Resultado somado" soma o resultado de cada operação em ${UX_META[UNI].unit} (sem juros compostos)`);
const uxChartNote = () => UX_META[UNI].chart;

/* the universe's data: embedded in a static export, fetched once a minute from /api/universe on the live page */
function uxData(uid) {
  const u = UX[uid] || (UX[uid] = { data: null, at: 0, loading: false, error: null, merged: null, base: null });
  if (state.universes && state.universes[uid]) { u.data = state.universes[uid]; return u.data; }
  if (!LIVE) return u.data;
  if (!u.loading && (!u.data || Date.now() - u.at > 60000)) {
    u.loading = true;
    fetch('/api/universe?id=' + encodeURIComponent(uid), { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then((d) => { u.data = d; u.error = null; u.at = Date.now(); u.merged = null; })
      .catch((e) => { u.error = String(e && e.message ? e.message : e); u.at = Date.now(); })
      .finally(() => { u.loading = false; if (route.id.startsWith(uid)) render(); });
  }
  return u.data;
}
/* run fn with the universe's keys in `state` (one merged object per data version, so caches keyed by state hold) */
function inUniverse(uid, fn) {
  if (uid === 'crypto') { const prev = UNI; UNI = 'crypto'; try { return fn(); } finally { UNI = prev; } }
  const d = uxData(uid), u = UX[uid];
  if (!d) return null;
  if (!u.merged || u.base !== state || u.mergedData !== d) {
    u.base = state; u.mergedData = d;
    u.merged = { ...state, pairs: d.pairs || [], hypotheses: d.hypotheses || [], allHypotheses: d.hypotheses || [], strategies: d.strategies || [],
      experiments: d.experiments || { items: [] }, gate_bar: { ...(state.gate_bar || {}), ...(d.gate_bar || {}) }, trade_index: d.trade_index || null,
      forward_test: { hypotheses: [], rule: (state.forward_test || {}).rule }, universe: d };
  }
  const prevState = state, prevUni = UNI;
  state = u.merged; UNI = uid;
  try { return fn(); } finally { state = prevState; UNI = prevUni; }
}

/* tabs at the top of every universe page: the same page in the other universes */
function uxTabs(page) {
  const all = [['crypto', 'Cripto']].concat(Object.entries(UX_META).map(([k, m]) => [k, m.title]));
  const href = (u) => '#/' + (u === 'crypto' ? page : UX_ROUTE[u][page]);
  return h('nav', { class: 'ux-tabs', 'aria-label': 'Universo de ativos' }, all.map(([u, label]) => h('a', { href: href(u), class: 'ux-tab', 'aria-current': u === UNI ? 'page' : null, 'data-fkey': 'ux:' + u + ':' + page }, label)));
}
function uxBanner(uid) {
  const d = uxCur(), m = UX_META[uid];
  if (!d) return null;
  const g = d.gate_bar || {};
  return h('div', { class: 'notice info ux-note', role: 'note' }, h('span', { class: 'ic info', 'aria-hidden': 'true' }, 'i'),
    h('div', null, h('b', null, m.title + '. '), d.note || '', ` Cada operação vale ${m.unit}. Régua atual de lucro mínimo na exploração: `,
      h('b', null, ok(g.current_bar_pct) ? nf1.format(g.current_bar_pct) + '%' : dash), ` (1% × (1 + 0,1 × ${nf0.format(g.trials || 0)} tentativas já lidas)).`,
      d.error ? h('span', { class: 'neg' }, ' Erro ao montar este universo: ' + d.error) : null));
}
/* the crypto screen on WIN/WDO (research/b3/crypto_screen.json), on the B3 home page */
function uxScreenCard() {
  const d = uxCur(), s = d && d.screen;
  if (!s) return null;
  const rows = (s.rows || []).filter((r) => ok(r.net_conservative_pct)).sort((a, b) => b.net_conservative_pct - a.net_conservative_pct);
  return card('As estratégias de cripto no WIN e no WDO', `Triagem registrada antes de qualquer leitura (b3/config/crypto_screen_b3.json): ${nf0.format(s.reads)} de ${nf0.format(s.expected_reads)} leituras feitas. Passa na triagem quem ganha, por operação, pelo menos 3 vezes o custo e fica positiva no custo conservador; as 10 melhores seguem o protocolo completo.`,
    h('div', { class: 'rx-stack' },
      h('div', { class: 'rx-kpis' }, rxKpi('Leituras', nf0.format(s.reads), `de ${nf0.format(s.expected_reads)} previstas`), rxKpi('Passaram na triagem', nf0.format(s.passing_triage), 'ganho ≥ 3× custo e positivo no conservador'),
        rxKpi('Passaram nos critérios', nf0.format((s.top_passing_gates || []).length), listPt(s.top_passing_gates || []) || 'nenhuma'), rxKpi('Com erro', nf0.format(s.errors || 0), 'não rodaram no motor')),
      dataTable({ id: 'ux-screen', label: 'Triagem das estratégias de cripto', rows: rows.slice(0, 40).map((r) => ({ ...r, key: r.rule + '@' + r.symbol })), sort0: { key: 'cons', dir: -1 },
        cols: [{ key: 'rule', label: 'Estratégia', val: (r) => r.rule, cell: (r) => h('a', { href: rxR('strategy') + '/' + encodeURIComponent(r.rule) }, r.rule.replace(/^C-/, '')) },
          { key: 'sym', label: 'Contrato', val: (r) => r.symbol, cell: (r) => r.symbol },
          { key: 'n', label: 'Operações', num: true, val: (r) => r.trades, cell: (r) => nf0.format(r.trades || 0) },
          { key: 'gc', label: 'Ganho ÷ custo', num: true, val: (r) => r.gross_over_cost, cell: (r) => ok(r.gross_over_cost) ? nf1.format(r.gross_over_cost) + '×' : dash },
          { key: 'base', label: 'Líquido base', num: true, val: (r) => r.net_base_pct, cell: (r) => signedSpan(r.net_base_pct, 1) },
          { key: 'cons', label: 'Líquido conservador', num: true, val: (r) => r.net_conservative_pct, cell: (r) => signedSpan(r.net_conservative_pct, 1, true) },
          { key: 'tri', label: 'Triagem', val: (r) => r.passes_triage ? 1 : 0, cell: (r) => r.passes_triage ? badge({ icon: '✓', cls: 'good', label: 'passa' }) : h('span', { class: 'sub' }, 'não') }] })), { cls: 'b-12' });
}
function uxPage(uid, page, fn) {
  return () => {
    const d = uxData(uid), u = UX[uid] || {};
    uxOwn(uid);
    if (!d) return h('div', { class: 'rx rx-stack' }, u.error ? emptyState('Não foi possível carregar ' + UX_META[uid].title + '.', u.error) : loadingState('Carregando ' + UX_META[uid].title + '…'));
    return inUniverse(uid, () => h('div', { class: 'rx-stack' }, uxTabs(page), page === 'overview' ? uxBanner(uid) : null,
      fn(), page === 'overview' && uid === 'b3' ? uxScreenCard() : null));
  };
}
/* the Resultados filters (ui.rx: ranking, operations, comparison) are kept per universe: rx always holds the filters
   of the universe whose page is on screen, the others wait in RX_STORE */
const RX_STORE = {};
const RX_DEFAULTS = structuredClone(rx);      /* this file is inlined right after results.js: rx is still pristine */
let RX_OWNER = 'crypto';
function uxOwn(uid) {
  if (typeof rx === 'undefined' || RX_OWNER === uid) return;
  RX_STORE[RX_OWNER] = structuredClone(rx);
  const next = RX_STORE[uid] || RX_DEFAULTS;
  for (const k of Object.keys(rx)) delete rx[k];
  Object.assign(rx, structuredClone(next));
  RX_OWNER = uid;
}
/* a crypto Resultados page: claim the filters for crypto, then draw it under the universe tabs */
const uxCrypto = (page, fn) => (r) => { uxOwn('crypto'); const node = fn(r); return page && page !== 'strategy' ? h('div', { class: 'rx-stack' }, uxTabs(page), node) : node; };
/* routes of every universe, appended to ROUTES by index.html */
function uxRoutes() {
  const out = [];
  for (const [u, m] of Object.entries(UX_META)) {
    out.push({ id: u, icon: 'overview', group: m.group, title: 'Início', ctx: `${m.title}: conclusão, funil e as melhores regras`, page: (r) => uxPage(u, 'overview', () => pageInicio())(r) });
    out.push({ id: `${u}-leaderboard`, icon: 'leaderboard', group: m.group, title: 'Ranking', ctx: `${m.title}: todas as regras testadas, com filtros`, page: (r) => uxPage(u, 'leaderboard', () => pageRanking())(r) });
    out.push({ id: `${u}-trades`, icon: 'trades', group: m.group, title: 'Operações', ctx: `${m.title}: todas as operações, filtros e quando funcionam`, page: (r) => uxPage(u, 'trades', () => pageOperacoes())(r) });
    out.push({ id: `${u}-compare`, icon: 'compare', group: m.group, title: 'Comparar', ctx: `${m.title}: até quatro regras lado a lado`, page: (r) => uxPage(u, 'compare', () => pageComparar())(r) });
    out.push({ id: `${u}-strategy`, hidden: true, title: 'Estratégia', ctx: `${m.title}: relatório de uma regra`, page: (r) => uxPage(u, 'strategy', () => pageEstrategia(r.arg))(r) });
    out.push({ id: `${u}-chart`, hidden: true, title: 'Gráfico do backtest', ctx: `${m.title}: candles e operações de uma leitura`, page: (r) => uxPage(u, 'chart', () => pageTrades(r))(r) });
  }
  return out;
}
const UX_STYLE = `.ux-tabs{display:flex;flex-wrap:wrap;gap:6px}.ux-tab{padding:6px 12px;border:1px solid var(--line);border-radius:999px;text-decoration:none;color:var(--fg);font-size:13px;background:var(--panel)}
.ux-tab[aria-current=page]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}.ux-note{margin:0}`;
(() => { const st = document.createElement('style'); st.textContent = UX_STYLE; document.head.append(st); })();
