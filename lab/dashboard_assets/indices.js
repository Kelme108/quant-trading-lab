/* ==================== Índices (WIN/WDO): pesquisa nos mercados substitutos (docs/plano-portal-proxies.md) ====================
   Inlined into the page's script by lab.dashboard.render_page (after results.js), so it shares the page helpers
   (h, sv, card, kpi, badge, ST, dataTable, selectBox, emptyState, loadingState, term, det, showTip, render, route).
   Data: GET /api/indices (lab/indices_portal.py), fetched when an Índices page opens; the static export embeds it in
   state.indices. Trade lists: GET /api/indices/trades?file=... Text written by agents is inserted as text only.
   Origin of every number: BACKTEST on the MetaQuotes-Demo proxies (index CFDs standing in for WIN/WDO-like futures),
   1 unit per trade, base cost scenario unless the label says otherwise. */

// Every path this module reads; a test keeps it equal to lab.indices_portal.INDICES_CONTRACT.
const IX_CONTRACT = ['generated_at', 'program', 'funnel', 'summary', 'board', 'rules', 'cycles', 'markets', 'measurements', 'alerts'];
const IX = { data: null, at: 0, loading: false, error: null, trades: {}, f: { mkt: 'all', dec: 'all', origin: 'all', split: 'exploration' } };
const IX_ROUTES = ['indices', 'indices-placar', 'indices-regra', 'indices-ciclos', 'indices-mercados'];
const IX_SPLIT = { exploration: 'Exploração', validation: 'Validação', final_test: 'Teste final' };
const IX_SPLITS = ['exploration', 'validation', 'final_test'];
const IX_DEC = { passed: { icon: '✓', cls: 'good', label: 'Passou' }, rejected: { icon: '✕', cls: 'bad', label: 'Rejeitada' }, inconclusive: { icon: '!', cls: 'warn', label: 'Inconclusiva' } };
const IX_OUTCOME = { done: { icon: '✓', cls: 'good', label: 'Concluído' }, error: { icon: '✕', cls: 'bad', label: 'Erro' }, invalid: { icon: '!', cls: 'warn', label: 'Proposta inválida' },
  implementation_failed: { icon: '!', cls: 'warn', label: 'Código reprovado' }, interrupted: { icon: '!', cls: 'warn', label: 'Interrompido' }, running: { icon: '…', cls: 'info', label: 'Rodando' } };
const IX_STEP = { agent: 'Agente', registered: 'Regra registrada (commit antes do teste)', exploration: 'Exploração lida', validation: 'Validação lida', cycle_end: 'Fim do ciclo',
  cycle_error: 'Erro', proposal_invalid: 'Proposta reprovada no formato', implementation_rejected: 'Código reprovado nas verificações', paused: 'Pipeline pausado', program_stop: 'Limite do programa' };
const IX_AGENT = { 'proxy-research': 'pesquisador', 'proxy-developer': 'programador' };

function ixTerms() {
  return {
    ix_proxy: ['Mercado substituto', 'Não há conta de demonstração com WIN e WDO, então a pesquisa usa índices parecidos do servidor de demonstração da MetaQuotes: S&P 500 (US500), Nasdaq (USTEC), Dow (US30), Russell (US2000) e DAX (DE40). Os custos usados são os dos contratos futuros reais que eles representam, não os da corretora de demonstração.'],
    ix_bar: ['Régua', 'Retorno líquido mínimo para passar, somado ao longo da etapa. Começa em 1% e sobe 10% (0,1 ponto) a cada combinação regra × mercado já testada, porque cada tentativa a mais aumenta a chance de achar um resultado bom só por sorte.'],
    ix_xcost: ['Múltiplo do custo', 'Ganho bruto médio por operação dividido pelo custo de ida e volta (0,01% no cenário base). Abaixo de 1x a regra perde para o custo; o plano pede 3x ou mais para sobrar margem.'],
    ix_cons: ['Custo conservador', 'O dobro do custo base (0,02% ida e volta, e 0,01% a mais em cada stop). É o cenário que decide: a regra precisa passar nele também.'],
    ix_combo: ['Combinação', 'Uma regra testada em um mercado. A mesma regra em dois mercados conta como duas combinações, e cada uma sobe a régua.'],
    ix_stage: ['Etapas', 'Exploração (dados até 2023), validação (2024 a jun/2025, lida uma única vez) e teste final (jul/2025 em diante, só com o seu desbloqueio). Uma regra só avança se passar na etapa anterior no mesmo mercado.'],
    ix_stopslip: ['Deslizamento no stop', 'O backtest executaria o stop exatamente no preço, mas na prática o preço salta. Por decisão de 14/11, cada stop em índice paga 0,005% a mais no cenário base.'],
    ix_program: ['Programa de agentes', 'Agentes de IA propõem e programam regras novas sozinhos, no máximo 3 por semana. Os critérios (b3/config/gates_proxies.json) decidem; o agente não aprova nada.'],
  };
}

/* ---------- data ---------- */
function ixData() {
  if (state.indices) return state.indices;                 // static export
  if (!LIVE) return null;
  if (!IX.loading && (!IX.data || Date.now() - IX.at > 60000)) {
    IX.loading = true;
    fetch('/api/indices', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then((d) => { IX.data = d; IX.error = null; IX.at = Date.now(); })
      .catch((e) => { IX.error = String(e && e.message ? e.message : e); IX.at = Date.now(); })
      .finally(() => { IX.loading = false; if (IX_ROUTES.includes(route.id) || route.id === 'overview') render(); });
  }
  return IX.data;
}
const ixPending = () => IX.error ? emptyState('Não foi possível carregar os dados de Índices.', IX.error) : loadingState('Carregando a pesquisa de índices…');
function ixTrades(file) {
  const t = IX.trades[file];
  if (t || !LIVE || !file) return t || null;
  IX.trades[file] = { loading: true };
  fetch('/api/indices/trades?file=' + encodeURIComponent(file), { cache: 'no-store' }).then((r) => r.json().then((b) => { if (!r.ok) throw new Error(b.error || 'HTTP ' + r.status); return b; }))
    .then((b) => { IX.trades[file] = b; }).catch((e) => { IX.trades[file] = { error: String(e.message || e) }; }).finally(() => render());
  return IX.trades[file];
}

/* ---------- formatting ---------- */
const ixNf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
const ixPct = (v, d = 2) => ok(v) ? (v > 0 ? '+' : v < 0 ? MINUS : '') + ixNf(d).format(Math.abs(v)) + '%' : dash;
const ixX = (v) => ok(v) ? (v < 0 ? MINUS : '') + ixNf(1).format(Math.abs(v)) + 'x' : dash;
const ixTone = (v) => !ok(v) || v === 0 ? '' : v > 0 ? 'pos' : 'neg';
const ixNum = (v, d = 0) => ok(v) ? ixNf(d).format(v) : dash;
const ixDay = (iso) => iso ? new Date(iso).toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' }) : dash;
const ixWhen = (iso) => iso ? new Date(iso).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : dash;
const ixDecBadge = (d) => d ? badge(IX_DEC[d] || { icon: '?', cls: 'info', label: d }) : h('span', { class: 'sub' }, 'não lida');
const ixRuleLink = (id) => h('a', { href: '#/indices-regra/' + encodeURIComponent(id), 'data-fkey': 'ixr:' + id }, id);
const ixSafeUrl = (u) => /^https:\/\//i.test(String(u || '')) ? String(u) : null;
const ixDaysTo = (d) => d ? Math.round((Date.parse(d + 'T00:00:00-03:00') - Date.now()) / 86400000) : null;
function ixAgentText(text) { return h('div', { class: 'ix-agent' }, h('div', { class: 'sub' }, AGENT_TEXT), h('p', null, text || dash)); }
function ixStyle() {   // once, in <head>: a style inside the page would vanish when the page is redrawn
  if (!document.getElementById('ix-style')) document.head.append(ixCss());
  return null;
}
function ixKv(rows) { return h('table', { class: 'ix-kv' }, h('tbody', null, rows.map(([k, v]) => h('tr', null, h('th', { scope: 'row' }, k), h('td', null, v))))); }
function ixCss() {
  return h('style', { id: 'ix-style' }, `.ix-kv{width:100%;border-collapse:collapse}.ix-kv th{text-align:left;font-weight:500;color:var(--ink2);width:36%;padding:6px 10px 6px 0;vertical-align:top}
.ix-kv td{padding:6px 0;border-bottom:1px solid var(--line)}.ix-kv th{border-bottom:1px solid var(--line)}
.ix-agent p{white-space:pre-wrap;margin:6px 0 0}.ix-steps{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:6px}
.ix-steps li{display:grid;grid-template-columns:96px 1fr;gap:8px;font-size:13px}.ix-bar{height:8px;border-radius:4px;background:var(--accent)}
.ix-funnel{display:grid;gap:10px}.ix-funnel .r{display:grid;grid-template-columns:110px 1fr 90px;gap:10px;align-items:center}
.ix-track{background:var(--na-bg);border-radius:4px;overflow:hidden}.ix-alert{border-left:3px solid var(--warn);padding:6px 10px;margin:6px 0}
.ix-alert.bad{border-left-color:var(--bad)}.ix-pre{white-space:pre-wrap;font-size:12px;max-height:320px;overflow:auto}.ix-grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.ix-years{display:grid;gap:4px}.ix-years .r{display:grid;grid-template-columns:48px 1fr 70px;gap:8px;align-items:center;font-size:12.5px}
.ix-svg{width:100%;height:auto;display:block}`);
}
function ixFrame(eyebrow, title, lede, ...body) { return h('div', { class: 'rx rx-stack' }, ixStyle(), rxHeader(eyebrow, title, lede), ...body); }

/* ---------- shared pieces ---------- */
function ixSentence(d) {
  const s = d.summary, st = (d.program || {}).status || {};
  const head = s.passed_final ? `${s.passed_final} ${plural(s.passed_final, 'combinação aprovada', 'combinações aprovadas')} no teste final.` : 'Nenhuma regra aprovada até agora.';
  const funnel = `${s.rules} regras testadas em ${s.pairs_explored} combinações regra × mercado; ${s.passed_exploration} passaram a exploração, ${s.passed_validation} a validação e ${s.passed_final} o teste final.`;
  const prog = d.program && d.program.paused ? 'O programa de agentes está pausado.' : st.can_register ? `Programa de agentes ativo: ${st.registered_this_week} de ${(d.program.config || {}).max_new_rules_per_week} regras nesta semana.`
    : st.reasons && st.reasons.length ? `Programa de agentes em espera: ${ixReason(st.reasons[0])}.` : '';
  return `${head} ${funnel} ${prog}`;
}
function ixReason(r) {
  const m = /^(\d+) rules already registered this week/.exec(r || '');
  if (m) return `limite de ${m[1]} regras da semana atingido; volta na segunda-feira`;
  if (/project stop/.test(r)) return 'critério de parada do projeto atingido';
  if (/none passed validation/.test(r)) return '15 regras sem nenhuma passar a validação';
  return r;
}
function ixAlerts(d) {
  const list = d.alerts || [];
  if (!list.length) return null;
  return card('Pede a sua atenção', 'Avisos da pesquisa de índices.', h('div', null, list.map((a) => h('div', { class: 'ix-alert' + (a.level === 'bad' ? ' bad' : '') },
    h('div', null, a.rule ? [ixRuleLink(a.rule), ' '] : null, a.text), a.action ? h('div', { class: 'sub' }, 'Como resolver: ', a.action) : null))));
}
function ixFunnel(d) {
  const top = Math.max(1, ...(d.funnel || []).map((f) => f.read));
  return h('div', { class: 'ix-funnel' }, (d.funnel || []).map((f) => h('div', { class: 'r' }, h('b', null, IX_SPLIT[f.split]),
    h('div', { class: 'ix-track' }, h('div', { class: 'ix-bar', style: `width:${Math.max(2, 100 * f.read / top)}%` })),
    h('span', { class: 'num' }, `${f.passed} de ${f.read}`))));
}
function ixProgramCard(d) {
  const p = d.program || {}, st = p.status || {}, cfg = p.config || {}, ps = cfg.project_stop || {};
  const counted = (st.counted_rules || []).length, stopAfter = cfg.stop_after_rules_without_validation_pass;
  const rows = [
    ['Estado', p.paused ? badge(ST.bad, 'Pausado') : st.can_register ? badge(ST.good, 'Ativo') : st.error ? badge(ST.bad, 'Erro ao ler') : badge(ST.warn, 'Em espera')],
    ['Motivo', p.paused || (st.reasons && st.reasons.length ? st.reasons.map(ixReason).join('; ') : 'pode registrar a próxima regra') || st.error || dash],
    ['Regras nesta semana', `${ixNum(st.registered_this_week)} de ${ixNum(cfg.max_new_rules_per_week)}`],
    ['Regras dos agentes que contam', `${counted} de ${ixNum(stopAfter)} (para se nenhuma passar a validação)`],
    ['Passaram a validação', (st.validation_passes || []).length ? st.validation_passes.map((x) => x.join(' em ')).join(', ') : 'nenhuma'],
    ['Parada do projeto', `${st.project_deadline || dash} (${ixDaysTo(st.project_deadline) ?? dash} dias) ou ${ps.new_rules || 15} regras novas sem passar o teste final`],
    ['Mercados', `${d.program.lane_label || 'Substitutos'}${(d.program.ended || []).length ? `; o programa dos ${d.program.ended[0].label.toLowerCase()} terminou em ${ixDay(d.program.ended[0].ended_on + 'T12:00:00Z')} (${d.program.ended[0].rules})` : ''}`],
    ['Dados de bolsa', ((d.program.config || {}).exchange_data || {}).met ? 'cumprido em 16/11/2026: 5 anos de barras de 1 e 5 minutos da conta demo da Clear' : `${st.exchange_data_deadline || dash} (${ixDaysTo(st.exchange_data_deadline) ?? dash} dias): demo de corretora brasileira ou histórico comprado`],
    ['Ciclos', `tentativa a cada ${d.cycles.every_hours} h pelo Agendador de Tarefas; último registro ${ixWhen(d.cycles.last_event_at)}`],
  ];
  return card([term('ix_program', 'Programa de agentes'), d.program.lane === 'b3' ? ' · WIN e WDO' : ''], 'Propõe, programa e testa regras novas sozinho, dentro dos limites que você aprovou.',
    ixKv(rows), { actions: h('a', { href: '#/indices-ciclos', 'data-fkey': 'ix-gocyc' }, 'Ver os ciclos →') });
}

/* ---------- 1. Visão geral ---------- */
function pageIndices() {
  const d = ixData();
  if (!d) return ixFrame('Índices (WIN/WDO)', 'Day trade em índices', 'Pesquisa de day trade nos mercados substitutos do WIN e do WDO.', ixPending());
  const s = d.summary;
  return ixFrame('Índices (WIN/WDO)', 'Day trade em índices', ixSentence(d),
    h('div', { class: 'kpis' },
      kpi('Regras testadas', ixNum(s.rules), `${s.agent_rules} propostas pelos agentes`),
      kpi(term('ix_combo', 'Combinações'), ixNum(s.pairs_explored), `${s.reads} leituras no total`),
      kpi(term('ix_xcost', 'Bruto ≥ 3x o custo'), `${ixNum(s.pairs_at_3x_cost)} de ${ixNum(s.pairs_explored)}`, `${s.pairs_positive_gross} com bruto positivo`),
      kpi(term('ix_bar', 'Régua da próxima'), ixPct(s.next_bar_pct, 1), 'retorno líquido mínimo'),
      kpi('Gasto com agentes', 'US$ ' + nf2.format(s.agent_cost_usd || 0), 'não é resultado de trading')),
    ixAlerts(d),
    h('div', { class: 'ix-grid2' },
      card(term('ix_stage', 'Funil'), 'Combinações lidas e aprovadas em cada etapa.', ixFunnel(d), { actions: h('a', { href: '#/indices-placar', 'data-fkey': 'ix-goboard' }, 'Ver o placar →') }),
      ixProgramCard(d)),
    card('Onde está cada coisa', 'As outras páginas desta seção.', h('ul', null,
      h('li', null, h('a', { href: '#/indices-placar' }, 'Placar'), ': todas as combinações regra × mercado, com filtros.'),
      h('li', null, h('a', { href: '#/indices-ciclos' }, 'Ciclos dos agentes'), ': o que cada ciclo fez, quanto custou e os erros.'),
      h('li', null, h('a', { href: '#/indices-mercados' }, 'Mercados e medições'), ': custos, escopo, qualidade dos dados, tamanho do movimento e eventos.'))));
}

/* ---------- 2. Placar ---------- */
function ixScatter(rows) {
  const pts = rows.filter((r) => r.exploration && ok(r.exploration.gross_x_cost) && ok(r.exploration.trades_per_year));
  if (!pts.length) return emptyState('Sem pontos para o gráfico.', '');
  const W = 1000, H = 300, L = 44, B = 28, maxX = Math.max(10, ...pts.map((r) => r.exploration.trades_per_year)), lx = (v) => Math.log10(1 + v);
  const ys = pts.map((r) => Math.max(-8, Math.min(8, r.exploration.gross_x_cost))), x = (v) => L + (W - L - 10) * lx(v) / lx(maxX), y = (v) => 10 + (H - B - 10) * (8 - v) / 16;
  const line = (v, label, color) => [sv('line', { x1: L, x2: W - 10, y1: y(v), y2: y(v), stroke: color, 'stroke-dasharray': '4 4' }), sv('text', { x: W - 12, y: y(v) - 4, 'text-anchor': 'end', 'font-size': 11, fill: color }, label)];
  return sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'ix-svg', role: 'img', 'aria-label': 'Ganho bruto por operação em múltiplos do custo, contra operações por ano' },
    sv('line', { x1: L, x2: L, y1: 10, y2: H - B, stroke: 'var(--line2)' }), sv('line', { x1: L, x2: W - 10, y1: y(0), y2: y(0), stroke: 'var(--line2)' }),
    line(1, '1x o custo', 'var(--warn)'), line(3, '3x o custo (meta)', 'var(--good)'),
    [1, 10, 100, 1000].filter((v) => v <= maxX).map((v) => sv('text', { x: x(v), y: H - 8, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--ink2)' }, String(v))),
    sv('text', { x: L, y: H - 8, 'text-anchor': 'start', 'font-size': 11, fill: 'var(--ink2)' }, ''),
    [-8, -4, 0, 4, 8].map((v) => sv('text', { x: L - 6, y: y(v) + 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--ink2)' }, v + 'x')),
    pts.map((r, i) => sv('circle', { cx: x(r.exploration.trades_per_year), cy: y(ys[i]), r: 5, fill: r.exploration.decision === 'passed' ? 'var(--good)' : 'var(--bad)', 'fill-opacity': 0.7, tabindex: 0,
      onmousemove: (e) => showTip(e, `${r.rule} em ${r.symbol}`, [{ value: ixX(r.exploration.gross_x_cost), label: ' do custo, bruto por operação' }, { value: ixNum(r.exploration.trades_per_year), label: ' operações por ano' }, { value: (IX_DEC[r.exploration.decision] || {}).label || r.exploration.decision, label: ' na exploração' }]),
      onmouseleave: hideTip, onclick: () => go('#/indices-regra/' + r.rule) })));
}
function pageIndicesPlacar() {
  const d = ixData();
  if (!d) return ixFrame('Índices (WIN/WDO)', 'Placar', '', ixPending());
  const f = IX.f, origin = Object.fromEntries((d.rules || []).map((r) => [r.id, r.origin])), tf = Object.fromEntries((d.rules || []).map((r) => [r.id, r.timeframe_min]));
  const rows = d.board.filter((r) => (f.mkt === 'all' || r.symbol === f.mkt) && (f.origin === 'all' || origin[r.rule] === f.origin)
    && (f.dec === 'all' || (f.dec === 'passed' ? r.exploration && r.exploration.decision === 'passed' : !(r.exploration && r.exploration.decision === 'passed'))));
  const S = (r) => r[f.split] || null;
  const cols = [
    { key: 'rule', label: 'Regra', val: (r) => r.rule, cell: (r) => ixRuleLink(r.rule) },
    { key: 'mkt', label: 'Mercado', val: (r) => r.symbol, cell: (r) => r.symbol },
    { key: 'tf', label: 'Gráfico', val: (r) => tf[r.rule], cell: (r) => tf[r.rule] ? tf[r.rule] + ' min' : dash, num: true },
    { key: 'tpy', label: 'Ops/ano', num: true, val: (r) => (S(r) || {}).trades_per_year, cell: (r) => ixNum((S(r) || {}).trades_per_year) },
    { key: 'gross', label: 'Bruto/op', num: true, val: (r) => (S(r) || {}).mean_gross_pct, cell: (r) => h('span', { class: ixTone((S(r) || {}).mean_gross_pct) }, ixPct((S(r) || {}).mean_gross_pct, 4)) },
    { key: 'x', label: 'x custo', num: true, term: 'ix_xcost', val: (r) => (S(r) || {}).gross_x_cost, cell: (r) => h('span', { class: ixTone((S(r) || {}).gross_x_cost) }, ixX((S(r) || {}).gross_x_cost)) },
    { key: 'nb', label: 'Líquido base', num: true, val: (r) => (S(r) || {}).net_base_pct, cell: (r) => h('span', { class: ixTone((S(r) || {}).net_base_pct) }, ixPct((S(r) || {}).net_base_pct, 1)) },
    { key: 'nc', label: 'Líquido cons.', num: true, term: 'ix_cons', val: (r) => (S(r) || {}).net_conservative_pct, cell: (r) => h('span', { class: ixTone((S(r) || {}).net_conservative_pct) }, ixPct((S(r) || {}).net_conservative_pct, 1)) },
    { key: 'dd', label: 'Pior queda', num: true, val: (r) => (S(r) || {}).max_drawdown_base_pct, cell: (r) => ixPct((S(r) || {}).max_drawdown_base_pct, 1).replace('+', '') },
    ...IX_SPLITS.map((s) => ({ key: 'd-' + s, label: IX_SPLIT[s], val: (r) => r[s] ? r[s].decision : null, cell: (r) => ixDecBadge(r[s] && r[s].decision) })),
  ];
  const expand = (r) => h('div', null, IX_SPLITS.filter((s) => r[s]).map((s) => h('div', null, h('b', null, `${IX_SPLIT[s]} (${r[s].start} a ${r[s].end}), régua ${ixPct(r[s].bar_pct, 1)}: `),
    r[s].fails && r[s].fails.length ? r[s].fails.join('; ') : 'passou em todos os critérios')));
  const markets = [...new Set(d.board.map((r) => r.symbol))].sort();
  return ixFrame('Índices (WIN/WDO)', 'Placar', `${d.board.length} combinações regra × mercado. Os números são da etapa escolhida, custo base, 1 unidade por operação; abra a linha para ver por que cada uma reprovou.`,
    card('Bruto por operação × frequência', 'Exploração. Cada ponto é uma combinação; acima da linha verde o ganho bruto passa de 3x o custo. Clique num ponto para abrir a regra.', ixScatter(rows)),
    card('Todas as combinações', `${rows.length} de ${d.board.length} visíveis.`, h('div', null,
      h('div', { class: 'row' },
        selectBox('Etapa', 'ix-split', f.split, IX_SPLITS.map((s) => [s, IX_SPLIT[s]]), (v) => { f.split = v; render(); }),
        selectBox('Mercado', 'ix-mkt', f.mkt, [['all', 'Todos'], ...markets.map((m) => [m, m])], (v) => { f.mkt = v; render(); }),
        selectBox('Exploração', 'ix-dec', f.dec, [['all', 'Todas'], ['passed', 'Passou'], ['rejected', 'Não passou']], (v) => { f.dec = v; render(); }),
        selectBox('Origem', 'ix-origin', f.origin, [['all', 'Todas'], ['builtin', 'Escritas à mão (P-001 a P-007)'], ['agent', 'Propostas pelos agentes']], (v) => { f.origin = v; render(); })),
      rows.length ? dataTable({ id: 'ix-board', cols, rows: rows.map((r) => ({ ...r, key: `${r.rule}-${r.symbol}`, label: `${r.rule} ${r.symbol}` })), sort0: { key: 'x', dir: -1 }, expand, label: 'Placar regra × mercado' })
        : emptyState('Nenhuma combinação com esses filtros.', ''))));
}

/* ---------- 3. Relatório de uma regra ---------- */
function ixScenarioTable(read) {
  const names = { optimistic: 'Otimista', base: 'Base', conservative: 'Conservador', stress: 'Estresse' };
  return simpleTable(['Cenário de custo', 'Operações', 'Bruto/op', 'Líquido/op', 'Líquido total', 'Pior queda', 'Acerto', 'Profit factor'],
    Object.entries(names).map(([k, label]) => { const m = read.scenarios[k] || {}; return [label, ixNum(m.trades), ixPct(m.mean_gross_pct, 4), ixPct(m.mean_net_pct, 4),
      h('span', { class: ixTone(m.net_return_pct) }, ixPct(m.net_return_pct, 1)), ixPct(m.max_drawdown_pct, 1).replace('+', ''), ok(m.win_rate_pct) ? ixNf(0).format(m.win_rate_pct) + '%' : dash, ixNum(m.profit_factor, 2)]; }), [1, 2, 3, 4, 5, 6, 7]);
}
function ixYears(per) {
  const ys = Object.entries(per || {}).sort();
  if (!ys.length) return null;
  const top = Math.max(0.5, ...ys.map(([, v]) => Math.abs(v)));
  return h('div', { class: 'ix-years' }, ys.map(([y, v]) => h('div', { class: 'r' }, h('span', null, y),
    h('div', { class: 'ix-track' }, h('div', { class: 'ix-bar', style: `width:${Math.max(2, 100 * Math.abs(v) / top)}%;background:${v >= 0 ? 'var(--good)' : 'var(--bad)'}` })),
    h('span', { class: 'num ' + ixTone(v) }, ixPct(v, 1)))));
}
function ixEquity(rows) {
  let eq = 1, peak = 1, minDd = 0; const pts = [];
  for (const t of rows) { eq *= 1 + t[6] / 100; peak = Math.max(peak, eq); minDd = Math.min(minDd, eq / peak - 1); pts.push(eq); }
  const W = 640, H = 180, lo = Math.min(...pts, 1), hi = Math.max(...pts, 1), x = (i) => 40 + (W - 50) * i / Math.max(1, pts.length - 1), y = (v) => 10 + (H - 30) * (hi - v) / Math.max(1e-9, hi - lo);
  return h('div', null, sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'ix-svg', role: 'img', 'aria-label': 'Curva de capital, custo base' },
    sv('line', { x1: 40, x2: W - 10, y1: y(1), y2: y(1), stroke: 'var(--line2)', 'stroke-dasharray': '4 4' }),
    sv('polyline', { points: pts.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' '), fill: 'none', stroke: eq >= 1 ? 'var(--good)' : 'var(--bad)', 'stroke-width': 1.6 }),
    sv('text', { x: 36, y: y(hi) + 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--ink2)' }, ixPct(100 * (hi - 1), 0)),
    sv('text', { x: 36, y: y(lo) + 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--ink2)' }, ixPct(100 * (lo - 1), 0))),
    h('div', { class: 'sub' }, `${rows.length} operações; resultado composto ${ixPct(100 * (eq - 1), 1)}; pior queda ${ixPct(100 * minDd, 1)}.`));
}
function ixByTime(rows, tz) {
  const hours = {}, days = {}, DOW = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
  const fmt = new Intl.DateTimeFormat('en-US', { timeZone: tz, hour: '2-digit', hourCycle: 'h23', weekday: 'short' });
  for (const t of rows) {
    const p = Object.fromEntries(fmt.formatToParts(new Date(t[0])).map((x) => [x.type, x.value]));
    const hh = p.hour, wd = DOW[['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(p.weekday)];
    for (const [bag, k] of [[hours, hh], [days, wd]]) { const b = bag[k] = bag[k] || { n: 0, g: 0, w: 0 }; b.n++; b.g += t[5]; if (t[6] > 0) b.w++; }
  }
  const tbl = (bag, label, order) => simpleTable([label, 'Operações', 'Bruto médio', 'Acerto'], order.filter((k) => bag[k]).map((k) => [k, ixNum(bag[k].n), h('span', { class: ixTone(bag[k].g) }, ixPct(bag[k].g / bag[k].n, 4)), ixNf(0).format(100 * bag[k].w / bag[k].n) + '%']), [1, 2, 3]);
  return h('div', { class: 'ix-grid2' }, h('div', null, h('div', { class: 'sub' }, `Hora de entrada (horário local do mercado, ${tz})`), tbl(hours, 'Hora', Object.keys(hours).sort())),
    h('div', null, h('div', { class: 'sub' }, 'Dia da semana'), tbl(days, 'Dia', DOW)));
}
function ixTradesBlock(read, tz) {
  if (!read.trades_file) return h('p', { class: 'sub' }, read.split === 'exploration'
    ? 'Esta leitura foi feita antes de 15/11 e não guardou as operações; o recálculo da exploração ainda não chegou nela.'
    : 'Esta leitura foi feita antes de 15/11 e não guardou as operações. Validação e teste final não podem ser lidos de novo, então a curva não existe.');
  const t = IX.trades[read.trades_file];
  if (!t) return h('button', { type: 'button', 'data-fkey': 'ixt:' + read.file, onclick: () => { ixTrades(read.trades_file); render(); } }, 'Carregar as operações (curva de capital e horários)');
  if (t.loading) return loadingState('Carregando as operações…');
  if (t.error) return emptyState('Não foi possível carregar as operações.', t.error);
  return h('div', { class: 'rx-stack' }, t.recalculated ? h('p', { class: 'sub' }, `Recalculada com o motor atual (deslizamento no stop e regra dos 90%), não é uma leitura nova: hoje daria ${(IX_DEC[t.decision_now] || {}).label || t.decision_now}, líquido base ${ixPct((t.base_now || {}).net_return_pct, 1)}.`) : null,
    t.rows.length ? [ixEquity(t.rows), ixByTime(t.rows, tz)] : emptyState('Nenhuma operação nesta leitura.', ''));
}
function pageIndicesRegra(id) {
  const d = ixData();
  if (!d) return ixFrame('Índices (WIN/WDO)', id || 'Regra', '', ixPending());
  const r = (d.rules || []).find((x) => x.id === id);
  if (!r) return ixFrame('Índices (WIN/WDO)', 'Regra não encontrada', `Não existe ${id || 'regra'} na pesquisa de índices.`, h('a', { href: '#/indices-placar' }, '← Placar'));
  const p = r.proposal, tzOf = Object.fromEntries((d.markets || []).map((m) => [m.symbol, m.tz]));
  const firstRead = r.reads.map((x) => x.read_at).filter(Boolean).sort()[0];
  const bestText = { passed_final: 'passou o teste final', passed_validation: 'passou a validação', passed_exploration: 'passou a exploração', rejected: 'reprovada', not_run: 'ainda não testada',
    error: 'ciclo com erro (não testada)', invalid: 'proposta inválida (não testada)', implementation_failed: 'código reprovado (não testada)', registered: 'registrada' }[r.best] || r.best;
  const lede = `${r.title || r.name || r.id}. ${r.origin === 'agent' ? 'Proposta e programada pelos agentes' : 'Escrita à mão em 14/11/2026'}; ${bestText}.`;
  const proof = p ? (p.committed ? [`Registrada no commit ${p.committed.commit} em ${ixWhen(p.committed.at)}`, firstRead ? `; primeira leitura em ${ixWhen(firstRead)}` : '',
    firstRead && Date.parse(p.committed.at) <= Date.parse(firstRead) ? ' (registrada antes do teste ✓)' : firstRead ? ' (ATENÇÃO: leitura antes do registro)' : ''].join('') : 'Proposta sem commit de registro (o ciclo não chegou ao teste).')
    : 'Regra escrita à mão em b3/strategies/proxies.py e commitada antes da primeira leitura.';
  const obs = r.reads.filter((x) => x.split === 'exploration');
  return ixFrame('Índices (WIN/WDO) · ' + r.id, r.title || r.id, lede,
    h('div', { class: 'sub' }, h('a', { href: '#/indices-placar', 'data-fkey': 'ix-back' }, '← Placar'), ' / ', r.id),
    h('div', { class: 'ix-grid2' },
      card('A ideia', r.origin === 'agent' ? 'Texto do agente pesquisador.' : 'Resumo da regra publicada.', h('div', { class: 'rx-stack' },
        r.summary ? h('p', null, r.summary) : null,
        p && p.mechanism ? h('div', null, h('b', null, 'Mecanismo (quem está do outro lado)'), ixAgentText(p.mechanism)) : null,
        p && p.why_gross_beats_3x_cost ? det('ix-why-' + r.id, 'Por que deveria ganhar 3x o custo', ixAgentText(p.why_gross_beats_3x_cost)) : null,
        p && p.ex_ante_rule ? det('ix-rule-' + r.id, 'A regra exata, escrita antes do teste', ixAgentText(p.ex_ante_rule)) : null,
        p && p.novelty_vs_tried ? det('ix-nov-' + r.id, 'O que tem de diferente das anteriores', ixAgentText(p.novelty_vs_tried)) : null,
        p && p.sources && p.sources.length ? h('div', null, h('b', null, 'Fontes'), h('ul', null, p.sources.map((s) => h('li', null, ixSafeUrl(s.url) ? h('a', { href: ixSafeUrl(s.url), target: '_blank', rel: 'noopener noreferrer' }, s.title || s.url) : (s.title || s.url))))) : null,
        p && p.problems && p.problems.length ? h('div', null, h('b', null, 'Problemas'), h('ul', null, p.problems.map((x) => h('li', null, x)))) : null)),
      card('Ficha', 'Esperado na proposta × observado na exploração.', ixKv([
        ['Origem', r.origin === 'agent' ? 'agentes (pipeline)' : 'escrita à mão'],
        ['Gráfico', r.timeframe_min ? r.timeframe_min + ' min' : dash],
        ['Mercados', (r.markets || []).join(', ') || dash],
        ['Operações por ano', p ? `esperado ${ixNum(p.expected_trades_per_year)}; observado ${obs.map((x) => `${x.symbol} ${ixNum((x.scenarios.base || {}).trades_per_year)}`).join(', ') || dash}` : obs.map((x) => `${x.symbol} ${ixNum((x.scenarios.base || {}).trades_per_year)}`).join(', ') || dash],
        ['Duração mediana', p ? `esperado ${ixNum(p.expected_median_hold_min)} min; observado ${obs.map((x) => `${x.symbol} ${ixNum((x.scenarios.base || {}).median_hold_min)} min`).join(', ') || dash}` : obs.map((x) => `${x.symbol} ${ixNum((x.scenarios.base || {}).median_hold_min)} min`).join(', ') || dash],
        ['Registro', proof],
        ['Arquivos', p ? [p.rule_file, p.test_file].filter(Boolean).join(' · ') : 'b3/strategies/proxies.py'],
        ['Parâmetros', Object.entries((p && p.parameters) || r.params || {}).map(([k, v]) => `${k} = ${v}`).join('; ') || dash],
      ]))),
    r.reads.length ? r.reads.map((x) => card(`${x.symbol} · ${IX_SPLIT[x.split]}`, `${x.start} a ${x.end} · lida em ${ixWhen(x.read_at)} · régua ${ixPct(x.bar_pct, 1)} · ${x.prior_variants ?? dash} combinações anteriores`,
      h('div', { class: 'rx-stack' },
        h('div', { class: 'row' }, ixDecBadge(x.decision), h('span', null, x.fails && x.fails.length ? 'Reprovou em: ' + x.fails.join('; ') : 'Passou em todos os critérios.')),
        ixScenarioTable(x),
        h('div', { class: 'ix-grid2' },
          h('div', null, h('b', null, 'Retorno por ano (custo base)'), ixYears((x.scenarios.base || {}).per_year_return_pct) || h('p', { class: 'sub' }, dash)),
          h('div', null, h('b', null, 'Detalhe (custo base)'), ixKv([
            ['Compras / vendas', `${ixNum((x.scenarios.base || {}).long_trades)} / ${ixNum((x.scenarios.base || {}).short_trades)}`],
            ['Duração mediana', ixNum((x.scenarios.base || {}).median_hold_min) + ' min'],
            ['Saídas', Object.entries((x.scenarios.base || {}).exit_reasons || {}).map(([k, v]) => `${k} ${v}`).join(', ') || dash],
            ['Lucro sem a melhor operação', ixPct((x.scenarios.base || {}).net_return_excl_best_pct, 1)],
            ['Anos positivos', ok((x.scenarios.base || {}).positive_years_share) ? ixNf(0).format(100 * x.scenarios.base.positive_years_share) + '%' : dash],
            ['Custo ida e volta / stop extra', `${ixPct(x.cost_base_pct, 3).replace('+', '')} / ${ok(x.stop_slippage_base_pct) ? ixPct(x.stop_slippage_base_pct, 3).replace('+', '') : 'não havia (antes de 14/11)'}`],
            ['Dias pulados (menos de 90% do pregão)', ok(x.days_skipped_incomplete) ? ixNum(x.days_skipped_incomplete) : 'regra ainda não existia'],
          ]))),
        det('ix-tr-' + x.file, 'Operações: curva de capital e horários', ixTradesBlock(x, tzOf[x.symbol] || 'America/New_York')))))
      : card('Leituras', '', emptyState('Esta regra ainda não foi lida em nenhum mercado.', p && p.status ? `Situação da proposta: ${p.status}.` : '')));
}

/* ---------- 4. Ciclos dos agentes ---------- */
function pageIndicesCiclos() {
  const d = ixData();
  if (!d) return ixFrame('Índices (WIN/WDO)', 'Ciclos dos agentes', '', ixPending());
  const c = d.cycles, p = d.program || {};
  const items = c.items || [];
  const days = c.cost_by_day || [], top = Math.max(0.01, ...days.map((x) => x.cost_usd));
  return ixFrame('Índices (WIN/WDO)', 'Ciclos dos agentes', `${items.length} ${plural(items.length, 'ciclo', 'ciclos')}, ${c.errors} com erro, US$ ${nf2.format(c.total_cost_usd)} gastos com agentes. Fora dos ciclos, ${c.program_stop_count} ${plural(c.program_stop_count, 'tentativa parou', 'tentativas pararam')} antes de chamar agentes, por limite do programa.`,
    p.paused ? card('Pipeline pausado', 'Nenhum ciclo novo roda enquanto o arquivo de pausa existir.', h('div', null, h('p', null, p.paused), h('p', { class: 'sub' }, `Para retomar, apague ${p.stop_file}.`)), { cls: 'b-12' }) : null,
    h('div', { class: 'ix-grid2' },
      card('Gasto por dia', 'Soma do custo dos agentes nos ciclos de cada dia (US$).', days.length ? h('div', { class: 'ix-years' }, days.map((x) => h('div', { class: 'r' }, h('span', null, x.day.slice(5).split('-').reverse().join('/')),
        h('div', { class: 'ix-track' }, h('div', { class: 'ix-bar', style: `width:${Math.max(2, 100 * x.cost_usd / top)}%` })), h('span', { class: 'num' }, 'US$ ' + nf2.format(x.cost_usd))))) : emptyState('Nenhum ciclo ainda.', '')),
      card('Limites do programa', 'As últimas tentativas que pararam antes de chamar agentes.', (c.program_stops || []).length ? simpleTable(['Quando', 'Motivo'], c.program_stops.slice(-6).reverse().map((s) => [ixWhen(s.at), s.reasons.map(ixReason).join('; ')]), [], [1]) : h('p', { class: 'sub' }, 'Nenhuma.'))),
    card('Cada ciclo', 'Do mais recente para o mais antigo. Um ciclo: o pesquisador propõe, o programador escreve o código, as verificações rodam, a regra é commitada e só então lida.',
      items.length ? h('div', { class: 'rx-stack' }, items.map((x, i) => h('div', { class: 'card' },
        h('div', { class: 'row' }, h('b', null, x.rule ? ixRuleLink(x.rule) : 'sem regra'), badge(IX_OUTCOME[x.outcome] || { icon: '?', cls: 'info', label: x.outcome }), h('span', { class: 'sub' }, `${ixWhen(x.started)} · US$ ${nf2.format(x.cost_usd)}`)),
        h('ul', { class: 'ix-steps' }, x.steps.map((s) => h('li', null, h('span', { class: 'sub' }, ixWhen(s.at)),
          h('div', null, h('b', null, s.event === 'agent' ? `Agente ${IX_AGENT[s.agent] || s.agent}${s.is_error ? ' (falhou)' : ''}` : (IX_STEP[s.event] || s.event)), ok(s.cost_usd) ? h('span', { class: 'sub' }, ` · US$ ${nf2.format(s.cost_usd)}`) : null,
            s.text ? det(`ix-st-${i}-${s.at}`, 'texto', h('div', { class: 'ix-pre' }, s.text)) : null))))))) : emptyState('Nenhum ciclo registrado.', 'Rode python -m b3.proxy_pipeline cycle ou aguarde o agendamento.')),
    det('ix-log', 'Últimas linhas de ops/state/proxy-cycle.log', h('div', { class: 'ix-pre' }, (c.log_tail || []).join('\n') || 'Sem log.')));
}

/* ---------- 5. Mercados, custos e medições ---------- */
function pageIndicesMercados() {
  const d = ixData();
  if (!d) return ixFrame('Índices (WIN/WDO)', 'Mercados e medições', '', ixPending());
  const ms = d.markets || [], ev = (d.measurements || {}).events || {}, dec = ev.decision || {};
  const hz = (m, k) => { const t = m.move_over_cost['1m'] || m.move_over_cost['5m'] || {}; return t[k]; };   // the 1-minute measurement has every window
  const mRows = ms.map((m) => [h('b', null, m.symbol), m.stands_for, `${m.open}–${m.close} (${m.tz.split('/')[1].replace('_', ' ')})`, ixPct(m.cost_base_pct, 3).replace('+', ''),
    ixPct(m.cost_conservative_pct, 3).replace('+', ''), m.stop_slippage_base_pct ? ixPct(m.stop_slippage_base_pct, 3).replace('+', '') : dash,
    m.in_scope ? badge(ST.good, 'No escopo') : h('span', { title: m.out_of_scope_reason || '' }, badge(ST.na, 'Fora'), ' ', h('span', { class: 'sub' }, m.out_of_scope_reason || ''))]);
  const qRows = ms.filter((m) => m.data_quality && m.data_quality['5m']).map((m) => { const q = m.data_quality['5m']; return [m.symbol, ixNum(q.session_days), ixNum(q.days_ge_90pct), ixNum(q.days_50_90pct), ixNum(q.days_lt_50pct), ixNum(q.in_day_holes)]; });
  const moveRows = ms.filter((m) => Object.keys(m.move_over_cost || {}).length).map((m) => [m.symbol, ...['1', '5', '15', '30', '60'].map((k) => ixX(hz(m, k)))]);
  const tickRows = ms.filter((m) => m.ticks).map((m) => [m.symbol, ixPct(m.ticks.spread_pct_median, 4).replace('+', ''), ixPct(m.ticks.bid_jump_pct_p99, 3).replace('+', ''), ixPct(m.ticks.bid_jump_pct_p999, 3).replace('+', ''), ixNum(m.ticks.days)]);
  const candName = { E1_fomc_pre_drift_long: 'E1 · compra antes do FOMC (10:00 → 13:55)', E2_fomc_15min_continuation: 'E2 · FOMC: segue os primeiros 15 min', E3_fomc_30min_continuation: 'E3 · FOMC: segue os primeiros 30 min',
    E4_macro_morning_continuation: 'E4 · dia de CPI/emprego: segue a manhã', E5_de40_release_continuation: 'E5 · DAX: segue a divulgação americana' };
  const eRows = Object.entries(candName).map(([k, label]) => { const x = dec[k] || {}; return [label, (x.markets_at_3x_cost || []).join(', ') || 'nenhum', ixPct(x.pooled_mean_gross_pct, 4), ixNum(x.pooled_t, 2), x.goes_on ? badge(ST.good, 'Segue') : badge(ST.rej, 'Encerrada')]; });
  return ixFrame('Índices (WIN/WDO)', 'Mercados e medições', 'Os mercados substitutos, o que cada um custa e o que as medições mostraram. Tudo medido só na exploração (dados até 2023).',
    card(term('ix_proxy', 'Mercados'), 'Custos dos contratos reais que cada um representa, escritos antes de qualquer backtest.', simpleTable(['Mercado', 'Representa', 'Pregão', 'Custo base', term('ix_cons', 'Conservador'), term('ix_stopslip', 'Stop extra'), 'Escopo'], mRows, [3, 4, 5], [1, 6])),
    h('div', { class: 'ix-grid2' },
      card('Tamanho do movimento × custo', 'Movimento mediano do preço em cada janela, em múltiplos do custo base. Mede quanto o preço anda, não quanto dá para prever.', moveRows.length ? simpleTable(['Mercado', '1 min', '5 min', '15 min', '30 min', '60 min'], moveRows, [1, 2, 3, 4, 5]) : emptyState('Sem medição.', '')),
      card('Qualidade dos dados (5 min)', 'Dias com menos de 90% das barras do pregão não abrem operação desde 14/11.', qRows.length ? simpleTable(['Mercado', 'Dias de pregão', '≥ 90%', '50–90%', '< 50%', 'Buracos no dia'], qRows, [1, 2, 3, 4, 5]) : emptyState('Sem medição.', ''))),
    card('Eventos com hora marcada', `Decisões do FOMC, inflação (CPI) e emprego (NFP), com datas oficiais (${Object.entries(ev.counts || {}).map(([k, n]) => `${k}: ${n}`).join(', ')}). Cinco regras fixadas antes de rodar; a linha seguiria se alguma chegasse a 3x o custo em 2 mercados com t ≥ 2.`,
      h('div', { class: 'rx-stack' }, simpleTable(['Regra medida', 'Mercados com ≥ 3x', 'Bruto médio', 't', 'Resultado'], eRows, [2, 3], [0]),
        h('p', { class: 'sub' }, dec.event_line_goes_on ? 'Pelo menos uma regra passou a medição.' : 'Nenhuma passou: a linha de eventos foi encerrada em 14/11, como o plano previa.'))),
    card('Fidelidade em ticks', 'Amostra de 10 pregões de nov–dez/2023: spread e saltos do preço entre ticks (o backtest executa o stop no preço exato).', tickRows.length ? simpleTable(['Mercado', 'Spread mediano', 'Salto 1 em 100', 'Salto 1 em 1.000', 'Pregões'], tickRows, [1, 2, 3, 4]) : emptyState('Sem medição.', '')));
}

/* ---------- Início: cartão resumo ---------- */
function ixHomeCard(cls) {
  const d = ixData();
  return card('Day trade em índices (WIN/WDO)', 'Pesquisa nos mercados substitutos, com custo de 0,01% ida e volta.',
    d ? h('div', { class: 'rx-stack' }, h('p', null, ixSentence(d)),
      h('div', { class: 'rx-kpis' }, rxKpi('Combinações', ixNum(d.summary.pairs_explored), `${d.summary.rules} regras`), rxKpi('Aprovadas no teste final', ixNum(d.summary.passed_final), `${d.summary.passed_validation} passaram a validação`),
        rxKpi('Avisos', ixNum((d.alerts || []).length), (d.alerts || []).length ? 'veja na visão geral' : 'nenhum')))
      : ixPending(), { cls, actions: h('a', { href: '#/indices', 'data-fkey': 'ix-home' }, 'Abrir Índices →') });
}
