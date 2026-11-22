/* ==================== B3: Esteira (strategy conveyor for WIN/WDO) ====================
   Inlined into the page's script by lab.dashboard.render_page. Strings only become text nodes.
   Owner, 2026-11-22: "pode criar a seção Esteira no portal". GET /api/esteira (lab/esteira_portal.py) regroups what the
   conveyor already wrote: the hourly cycle and its agent cost against the nightly cap, why variants are cut in the
   screen, the exit menus (S1-S4 in V, B1-B5 in R$) and the P-rule gate. Exploration figures only; read-only. */

const ES = { data: null, at: 0, loading: false, error: null, menu: 'all', all: false };
function esLoad(force) {
  if (!LIVE || ES.loading || (!force && ES.data && Date.now() - ES.at < 30000)) return;
  ES.loading = true;
  fetch('/api/esteira', { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((d) => { ES.data = d; ES.error = null; ES.at = Date.now(); })
    .catch((e) => { ES.error = String(e && e.message ? e.message : e); ES.at = Date.now(); })
    .finally(() => { ES.loading = false; if (route.id === 'b3-esteira') render(); });
}
if (LIVE) setInterval(() => { if (route.id === 'b3-esteira') esLoad(true); }, 60000);

const esPct = (v, d = 0) => ok(v) ? (v * 100).toFixed(d).replace('.', ',') + '%' : dash;
const esBrl = (v) => ok(v) ? h('span', { class: tone(v) }, (v < 0 ? MINUS : v > 0 ? '+' : '') + 'R$ ' + nf2.format(Math.abs(v))) : dash;
const esUsd = (v) => ok(v) ? 'US$ ' + nf2.format(v) : dash;
const esWhen = (iso) => iso ? new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' }) : dash;
const esDay = (s) => s ? s.slice(8, 10) + '/' + s.slice(5, 7) : dash;
const ES_OUTCOME = { done: 'lote triado', limit: 'teto atingido', rejected: 'lote recusado', 'em andamento': 'em andamento',
  'limite de uso': 'limite de uso do Claude', erro: 'erro', 'tempo esgotado': 'tempo esgotado', pausada: 'pausada' };
const esVariant = (v) => { const [fam, mk, tf, p] = String(v || '').split('|'); return { fam, mk, tf, p: (p || '').replaceAll(',', ', ') }; };
const esDist = (d) => !Array.isArray(d) ? dash : d[0] === 'brl' ? 'R$ ' + nf0.format(d[1]) : nfv.format(d[1]) + ' V';

function esStatus(d) {
  const s = d.status, b = s.budget, t = d.totals, ep = d.exit_picks;
  const state = s.paused ? { cls: 'bad', icon: '‖', label: 'pausada' } : s.cycle_running ? { cls: 'good', icon: '●', label: 'ciclo rodando agora' }
    : ok(b.cap_usd) && b.spent_usd + b.per_call_usd > b.cap_usd ? { cls: 'warn', icon: '■', label: 'teto da noite atingido' } : { cls: 'info', icon: '○', label: 'aguardando o próximo ciclo' };
  const left = ok(b.cap_usd) ? Math.max(0, b.cap_usd - b.spent_usd) : null;
  return h('div', { class: 'kpis' },
    kpi('Estado', badge(state), s.paused ? 'Motivo: ' + s.paused : 'Último registro: ' + esWhen(s.last_event.at_utc) + ' (' + (ES_OUTCOME[s.last_event.outcome] || s.last_event.event || dash) + ')', 'Os ciclos começam na hora cheia.'),
    kpi('Gasto da noite', esUsd(b.spent_usd), `Teto ${esUsd(b.cap_usd)}; restam ${esUsd(left)}. A noite começa às ${b.starts_at_hour}h.`, `Uma chamada pode custar até ${esUsd(b.per_call_usd)}. Agente no ${s.agent_model === 'sonnet' ? 'Sonnet' : s.agent_model}.`),
    kpi('Famílias', nf0.format(t.families), `${nf0.format(s.families_today)} triadas hoje; ${nf0.format(t.families_rejected)} recusadas na checagem.`, 'Última: ' + (t.last_family || dash)),
    kpi('Versões lidas', nf0.format(t.screen_reads + t.exit_reads), `${nf0.format(t.screen_reads)} na triagem e ${nf0.format(t.exit_reads)} nos menus de saída.`, 'Só exploração. A validação continua sem leitura.'),
    kpi('Candidatas nos menus', nf0.format(ep.good), `de ${nf0.format(ep.picks)} escolhas: p90 > 0 e acima da entrada aleatória.`, 'Ainda não são aprovadas.'));
}

function esScreen(d) {
  const sc = d.screen, r = d.screen_rules, ex = d.default_exit;
  const rows = sc.fails.map((f) => [f.label, nf0.format(f.count), esPct(f.share)]);
  return card('Triagem: por que as versões caem', `${nf0.format(sc.variants)} versões triadas, ${nf0.format(sc.passed)} passaram em todos os critérios. Uma versão pode cair em mais de um.`,
    h('div', { class: 'rx-stack' },
      h('div', { class: 'tablewrap' }, simpleTable(['Critério', 'Versões', 'Parcela'], rows, [1, 2], [0])),
      h('p', { class: 'sub' }, `Saída padrão da triagem: alvo R$ ${nf0.format(ex.target_brl)}, stop R$ ${nf0.format(ex.stop_brl)}, até ${nf0.format(ex.max_hold_min)} min. ` +
        `Critérios: pelo menos ${nf0.format(r.min_trades_per_year)} trades/ano, resultado médio > 0 no custo medido, ${r.min_positive_slices} de ${r.time_slices} fatias de tempo positivas, ` +
        `${esPct(r.plateau_min_positive_neighbour_share)} dos vizinhos da grade positivos, no máximo ${esPct(r.max_overlap_with_selected)} de sobreposição com uma já selecionada.`)));
}

function esPicks(d) {
  const ep = d.exit_picks;
  const every = ep.top.filter((r) => ES.menu === 'all' || r.menu === ES.menu).map((r) => ({ ...r, key: r.variant + ' ' + r.exit, label: r.variant }));
  const rows = ES.all ? every : every.slice(0, 25);
  const more = every.length > 25 ? h('button', { type: 'button', 'data-fkey': 'es-all', onclick: () => { ES.all = !ES.all; render(); } }, ES.all ? 'Mostrar só as 25 primeiras' : `Mostrar todas (${every.length})`) : null;
  const cols = [
    { key: 'family', label: 'Família', val: (r) => r.family, cell: (r) => h('span', { title: r.title || '' }, r.family) },
    { key: 'tf', label: 'Mercado', val: (r) => r.variant, cell: (r) => { const v = esVariant(r.variant); return v.mk + ' ' + v.tf; } },
    { key: 'params', label: 'Parâmetros', nw: false, cell: (r) => esVariant(r.variant).p },
    { key: 'exit', label: 'Saída', val: (r) => r.exit, cell: (r) => h('span', { title: r.exit_what || '' }, r.exit) },
    { key: 'hit', label: 'Acerto', num: true, val: (r) => r.hit, cell: (r) => esPct(r.hit, 1) },
    { key: 'net', label: 'Líquido/trade', num: true, val: (r) => r.net, cell: (r) => esBrl(r.net) },
    { key: 'p90', label: 'Líquido p90', num: true, val: (r) => r.p90, cell: (r) => esBrl(r.p90) },
    { key: 'random', label: 'Entrada aleatória', num: true, dim: true, val: (r) => r.random, cell: (r) => esBrl(r.random) },
    { key: 'tpy', label: 'Trades/ano', num: true, val: (r) => r.trades_per_year, cell: (r) => ok(r.trades_per_year) ? nf0.format(r.trades_per_year) : dash },
    { key: 'npy', label: 'R$/ano (1 contrato)', num: true, val: (r) => r.net_per_year, cell: (r) => esBrl(r.net_per_year) },
    { key: 'slices', label: 'Fatias +', num: true, val: (r) => r.positive_slices, cell: (r) => ok(r.positive_slices) ? r.positive_slices + '/8' : dash },
  ];
  const seg = segmented('Menu', 'es-menu', ES.menu, [['all', 'Todos'], ['R$', 'Em reais (B1–B5)'], ['V', 'Em V (S1–S4)']], (v) => { ES.menu = v; render(); });
  return card('Melhores saídas por família', `A versão e a saída que cada menu escolheu para cada família (uma família pode aparecer uma vez em cada menu), só as que têm p90 > 0 e ganham da entrada aleatória, ordenadas por acerto. ${nf0.format(ep.runs)} execuções dos menus.`,
    h('div', { class: 'rx-stack' }, seg,
      rows.length ? dataTable({ id: 'es-picks', cols, rows, sort0: { key: 'hit', dir: -1 }, label: 'Melhores saídas por família' }) : emptyState('Nenhuma escolha neste menu.', ''), more,
      h('p', { class: 'sub' }, 'Exploração (2021-11 a 2024-06), 1 contrato, custo medido (R$ 1,30 por ida e volta no WIN); p90 = custo pessimista (R$ 3,00). ' +
        'Antes de pensar em validação, a candidata ainda precisa passar no teste de robustez (t da média por trade acima do mínimo para o número de versões lidas); veja ' + d.note + '.')));
}

function esExits(d) {
  const rows = Object.entries(d.exits).sort(([a], [b]) => a.localeCompare(b)).map(([k, e]) => [k, esDist(e.stop), esDist(e.target), ok(e.hold_min) ? e.hold_min + ' min' : dash, e.what || dash]);
  return card('Saídas testadas', 'V = movimento médio de 30 min do contrato (volatilidade). B1 é a base do dono; B2 a B5 são vizinhas, para checar o planalto.',
    h('div', { class: 'tablewrap' }, simpleTable(['Saída', 'Stop', 'Alvo', 'Tempo', 'Descrição'], rows, [], [4])));
}

function esGates(d) {
  const g = d.gates, mt = g.multiple_testing || {};
  return card('Portão das regras P (WIN/WDO)', 'O que uma regra precisa para passar de etapa (b3/config/gates_b3.json).',
    h('ul', null,
      h('li', null, 'Custo: ', h('b', null, g.cost_basis === 'measured' ? 'medido' : (g.cost_basis || 'fixo antigo')), g.cost_basis === 'measured' ? ' (base = custo medido; conservador = p90).' : '.'),
      h('li', null, 'Barra estatística: ', h('b', null, mt.method === 't_stat_expected_max' ? `t da média por trade ≥ máx(${nfv.format(mt.t_floor)}; √(2 ln N))` : 'barra linear antiga'), ', com N = versões já lidas + 1, e líquido > 0 no base e no conservador.'),
      h('li', null, `Mínimo de ${nf0.format(g.minimum_trades)} trades; queda máxima de ${nf0.format(g.max_drawdown_pct)}%; ${esPct(g.positive_years_share)} dos anos positivos; positiva sem o melhor trade.`),
      h('li', null, 'Validação lida uma vez só; teste final trancado (só o dono destranca).')));
}

function esSelected(d) {
  if (!d.selected.length) return null;
  const rows = d.selected.map((s) => { const v = esVariant(s.variant); return [v.fam, v.mk + ' ' + v.tf, v.p, esPct(s.hit, 1), esBrl(s.net), ok(s.trades_per_year) ? nf0.format(s.trades_per_year) : dash, s.status === 'awaiting_demo' ? 'aguardando demo' : (s.status || dash), esWhen(s.selected_at_utc)]; });
  return card('Selecionadas pela triagem', 'Passaram em todos os critérios com a saída padrão (R$ 30/R$ 30). A demo não é evidência: serve para observar.',
    h('div', { class: 'tablewrap' }, simpleTable(['Família', 'Mercado', 'Parâmetros', 'Acerto', 'Líquido/trade', 'Trades/ano', 'Situação', 'Quando'], rows, [3, 4, 5], [2])));
}

function esCycles(d) {
  const rows = d.cycles.map((c) => [esWhen(c.start), ES_OUTCOME[c.outcome] || c.outcome || dash, c.batch != null ? 'B-' + String(c.batch).padStart(3, '0') : dash,
    c.registered ? nf0.format(c.registered) : dash, c.variants ? `${nf0.format(c.passed)} de ${nf0.format(c.variants)}` : dash,
    c.selected.length ? c.selected.join(', ') : dash, [c.exit_v, c.exit_brl].map((x, i) => x ? `${i ? 'R$' : 'V'}: ${x.ok ? x.picks + ' escolha(s)' : 'falhou'}` : null).filter(Boolean).join(' · ') || dash,
    c.cost_usd ? esUsd(c.cost_usd) : dash, c.notes.join(' · ') || '']);
  return card('Ciclos recentes', 'Um ciclo por hora: o agente escreve um lote de famílias, a triagem roda e os menus de saída rodam sobre o lote.',
    h('div', { class: 'tablewrap' }, simpleTable(['Início', 'Resultado', 'Lote', 'Famílias', 'Passaram', 'Selecionadas', 'Menus de saída', 'Custo', 'Observações'], rows, [3, 4, 7], [5, 6, 8])));
}

function esNights(d) {
  const rows = d.nights.map((n) => [esDay(n.day) + ' 21h → ' + esDay(new Date(Date.parse(n.day + 'T12:00:00Z') + 864e5).toISOString().slice(0, 10)), esUsd(n.cost_usd), nf0.format(n.agent_calls), nf0.format(n.batches), nf0.format(n.families)]);
  return card('Gasto por noite', 'Custo dos agentes por "noite" (das 21h às 21h do dia seguinte, horário de Brasília).',
    h('div', { class: 'tablewrap' }, simpleTable(['Noite', 'Custo', 'Chamadas', 'Lotes', 'Famílias'], rows, [1, 2, 3, 4])));
}

function pageEsteira() {
  const head = rxHeader('B3: WIN e WDO', 'Esteira de estratégias', 'Agentes escrevem famílias de regras simples para o mini índice e o mini dólar; cada versão é triada na exploração com uma saída padrão e depois com os menus de saída (stop e alvo em V ou em reais). Tudo aqui é backtest na exploração: nada foi lido na validação nem no teste final.');
  if (!LIVE) return h('div', { class: 'rx rx-stack' }, head, card('Esteira', null, notAvailable('Esteira', 'o snapshot estático não lê os arquivos da esteira. Abra o painel com python -m lab.dashboard serve.')));
  esLoad(false);
  if (!ES.data) return h('div', { class: 'rx rx-stack' }, head, ES.error ? emptyState('Não foi possível ler a esteira.', ES.error) : loadingState('Lendo a esteira…'));
  const d = ES.data;
  return h('div', { class: 'rx rx-stack' }, head, ES.error ? emptyState('Última leitura falhou; mostrando a anterior.', ES.error) : null,
    esStatus(d), esPicks(d), h('div', { class: 'grid g2' }, esScreen(d), esGates(d)), esExits(d), esSelected(d), esCycles(d), esNights(d),
    h('p', { class: 'sub' }, 'Atualizado em ' + esWhen(d.generated_at_utc) + '. A página relê os arquivos a cada minuto.'));
}
