/* ==================== Dry-run: what each bot did (trades, profit) and the live chart per asset ====================
   Data: GET /api/dryrun (bots) and GET /api/live?pair=&tf= (candles from Binance public data + every bot's trades).
   Everything here is dry-run: virtual wallet, real prices, no order is ever sent. Read-only.
   Look (Nebula v7, same vocabulary as the Resultados pages): a header sentence, a hero card with the totals, one card
   per bot with its own colour (the same colour marks that bot's trades on the live chart), then the detail tables. */
const dl = { bots: null, botsErr: null, botsAt: 0, loadingBots: false, live: null, liveErr: null, loadingLive: false, pair: 'BTC/USDT', tf: '1h', hide: {}, refs: null, open: {}, range: null, ids: [] };
/* one colour per bot, stable across both pages: index in the sorted list of every bot id seen so far */
const DL_TOKENS = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--accent2', '--teal'];
function dlKnow(ids) { const all = [...new Set([...dl.ids, ...ids])].sort(); const changed = all.length !== dl.ids.length; dl.ids = all; return changed; }
const dlTok = (id) => DL_TOKENS[Math.max(0, dl.ids.indexOf(id)) % DL_TOKENS.length];
const dlColor = (id) => cssVar(dlTok(id)) || '#a07cff';
const dlVar = (id) => `var(${dlTok(id)})`;
const DL_VERDICT = { collecting: { icon: '…', cls: 'warn', label: 'Coletando' }, approved_for_review: { icon: '✓', cls: 'good', label: 'Aprovada para análise' }, rejected: { icon: '✕', cls: 'bad', label: 'Reprovada' },
  inactive: { icon: '⏸', cls: 'bad', label: 'Inativa: descartar' } };
/* days the bot has left before the automatic discard (owner rule: 2 days without a closed trade), from /api/dryrun */
function dlLeft(b) {
  const r = b.inactivity, m = b.pooled;
  if (!r || !ok(m.days_running)) return null;
  if (m.trades < r.min_trades_by_then) return r.discard_after_days - m.days_running;
  return ok(m.days_since_last_trade) ? r.max_days_without_trade - m.days_since_last_trade : null;
}
const dlLeftText = (d) => (!ok(d) ? '' : d <= 0 ? 'sai do dry-run no próximo ciclo' : d < 1 ? `sai em ${Math.max(1, Math.round(d * 24))} h sem trade` : `sai em ${dlDays(d)} d sem trade`);
const dlPct = (v, d = 2) => (ok(v) ? (v > 0 ? '+' : '') + v.toFixed(d).replace('.', ',').replace('-', MINUS) + '%' : dash);
const dlWhen = (s) => (s ? s.replace('T', ' ') : dash);
const dlTone = (v) => (ok(v) ? (v > 0 ? 'pos' : v < 0 ? 'neg' : '') : '');
const dlName = (b) => { const hy = typeof rxHy === 'function' ? rxHy(b.id) : null; return hy ? humanName(hy.family) : humanName(String(b.strategy || '').replace(/_H\d+_v\d+$/, '')); };
const dlDays = (v) => ok(v) ? v.toFixed(1).replace('.', ',') : dash;
/* verdict reasons come from lab/dryrun.py in English; translate the fixed words, keep the numbers */
const DL_WORDS = [[/^running /, 'rodando há '], [/trades\/day/g, 'trades/dia'], [/more days to/g, 'dias a mais até'], [/at this pace/g, 'neste ritmo'],
  [/^warning: /, 'aviso: '], [/no closed trade yet after/g, 'nenhum trade fechado após'], [/discard at/g, 'descarte com'], [/with < (\d+) trades/g, 'e menos de $1 trade(s)'],
  [/^INACTIVE: /, 'INATIVA: '], [/closed trades in/g, 'trades fechados em'], [/needs (\d+) within/g, 'precisa de $1 em'], [/no closed trade for/g, 'nenhum trade fechado há'],
  [/\(limit /g, '(limite '], [/slow pace, more than/g, 'ritmo lento: mais de'], [/to the minimum trade count/g, 'até o mínimo de trades'],
  [/closed trades/g, 'trades fechados'], [/(\d) days/g, '$1 dias'], [/early reject/g, 'reprovação antecipada'], [/profit factor/g, 'fator de lucro'],
  [/expectancy/g, 'expectativa'], [/per trade/g, 'por trade'], [/P\(mean trade > 0\)/g, 'P(trade médio > 0)'], [/profit without the best trade/g, 'lucro sem o melhor trade'],
  [/drawdown/g, 'queda'], [/of wallet/g, 'da carteira'], [/observed entry cost/g, 'custo de entrada observado'], [/conservative scenario/g, 'cenário conservador'],
  [/\/side/g, '/lado'], [/net profit/g, 'lucro líquido'], [/^at (\d+) trades/, 'com $1 trades'], [/ after (\d+) trades/, ' após $1 trades'], [/n\/a/g, 'n/d']];
function dlReason(text) {
  const s = String(text), pass = /^pass: /.test(s), fail = /^(FAIL|INACTIVE): /.test(s);
  const body = DL_WORDS.reduce((a, [re, to]) => a.replace(re, to), s.replace(/^(pass|FAIL): /, '')).replace(/(\d)\.(\d)/g, '$1,$2');
  return h('li', { class: pass ? 'good' : fail ? 'bad' : '' }, h('i', { 'aria-hidden': 'true' }, pass ? '✓' : fail ? '✕' : '•'), h('span', null, body));
}

function dlLoadBots(force) {
  if (!LIVE || dl.loadingBots || (!force && dl.bots && Date.now() - dl.botsAt < 8000)) return;
  dl.loadingBots = true;
  fetch('/api/dryrun', { cache: 'no-store' })
    .then(async (r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then((body) => { dl.bots = body.bots; dl.retired = body.retired || []; dl.inactivity = body.inactivity || null; dl.botsErr = null; dl.botsAt = Date.now(); })
    .catch((e) => { dl.botsErr = String(e && e.message ? e.message : e); })
    .finally(() => {
      dl.loadingBots = false;
      const recolour = dl.bots ? dlKnow(dl.bots.map((b) => b.id)) : false;
      if (route.id === 'dryrun' || (route.id === 'aovivo' && recolour)) render();
    });
}
function dlLoadLive(refreshOnly) {
  if (!LIVE || dl.loadingLive) return;
  dl.loadingLive = true;
  fetch(`/api/live?pair=${encodeURIComponent(dl.pair)}&tf=${dl.tf}`, { cache: 'no-store' })
    .then(async (r) => { const body = await r.json().catch(() => ({})); if (!r.ok) throw new Error(body.error || 'HTTP ' + r.status); return body; })
    .then((body) => { dl.live = body; dl.liveErr = null; dlKnow(body.bots.map((b) => b.id)); })
    .catch((e) => { dl.liveErr = String(e && e.message ? e.message : e); })
    .finally(() => {
      dl.loadingLive = false;
      if (route.id !== 'aovivo') return;
      if (refreshOnly && dl.refs && dl.live && dl.refs.pair === dl.live.pair && dl.refs.tf === dl.live.tf) dlUpdate(); else render();
    });
}
if (LIVE) setInterval(() => { if (route.id === 'dryrun') dlLoadBots(true); else if (route.id === 'aovivo') dlLoadLive(true); }, 10000);

/* ---------- page: strategies in dry-run ---------- */
const dlBar = (frac, color) => h('span', { class: 'dl-bar', 'aria-hidden': 'true' }, h('i', { style: `width:${Math.max(0, Math.min(100, (ok(frac) ? frac : 0) * 100)).toFixed(1)}%;background:${color}` }));
function dlProgress(bots) {
  return h('ul', { class: 'dl-prog' }, bots.map((b) => {
    const m = b.pooled, v = DL_VERDICT[b.verdict] || { cls: 'na', label: b.verdict };
    return h('li', { style: `--c:${dlVar(b.id)}` },
      h('a', { href: '#/strategy/' + encodeURIComponent(b.id), class: 'id' }, h('i', { class: 'dot', 'aria-hidden': 'true' }), b.id),
      h('div', { class: 'bars' },
        h('div', { title: `${m.trades} de ${b.need_trades} trades fechados` }, dlBar(m.trades / b.need_trades, dlVar(b.id)), h('small', null, `${nf0.format(m.trades)}/${nf0.format(b.need_trades)} trades`)),
        h('div', { title: `${dlDays(m.days_running)} dias no ar (o mínimo para decidir é ${b.need_days} dias de trades)` }, dlBar(m.days_running / b.need_days, 'var(--teal)'),
          h('small', null, `${dlDays(m.days_running)} d no ar · ${ok(m.trades_per_day) ? nf2.format(m.trades_per_day) : dash} trades/dia`))),
      h('span', { class: 'rx-sdot ' + v.cls, title: dlLeftText(dlLeft(b)) }, v.label));
  }));
}
function dlBotCard(b, i) {
  if (b.error) return h('article', { class: 'rx-sc dl-card', style: `--c:${dlVar(b.id)}` }, h('header', null, h('b', null, b.id), badge(ST.bad, 'Erro')), notAvailable('Leitura deste bot', b.error));
  const m = b.pooled, v = DL_VERDICT[b.verdict] || { icon: '?', cls: 'na', label: b.verdict };
  const roi = b.wallet ? (m.net_profit / b.wallet) * 100 : null;
  const pairs = Object.entries(b.pairs || {});
  const pairRows = pairs.map(([pair, x]) => [h('a', { href: `#/aovivo?pair=${encodeURIComponent(pair)}`, 'data-fkey': 'dl-pair:' + b.id + pair }, pair), nf0.format(x.trades), nf0.format(x.open),
    ok(x.win_rate) ? pct0(x.win_rate * 100) : dash, ok(x.profit_factor) ? nf2.format(x.profit_factor) : dash, h('span', { class: dlTone(x.net_profit) }, usdt(x.net_profit)), pct0(x.max_drawdown_pct)]);
  const openRows = b.open.map((t) => [t.pair, dlWhen(t.open_date) + ' UTC', nf2.format(t.open_rate), nf2.format(t.stake), h('span', { class: dlTone(t.unrealised_pct) }, ok(t.unrealised_pct) ? dlPct(t.unrealised_pct) : dash)]);
  const closedRows = b.closed.slice(0, 25).map((t) => [t.pair, dlWhen(t.open_date), dlWhen(t.close_date), ok(t.minutes) ? durText(t.minutes) : dash, t.reason ? REASON(t.reason) : dash, h('span', { class: dlTone(t.profit) }, dlPct(t.profit_pct)), h('span', { class: dlTone(t.profit) }, usdt(t.profit))]);
  const tables = h('div', { class: 'rx-stack dl-tables' },
    h('h3', null, 'Por ativo'), h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Fechados', 'Abertos', 'Acerto', 'Fator de lucro', 'Lucro', 'Queda máx.'], pairRows, [1, 2, 3, 4, 5, 6])),
    h('h3', null, 'Posições abertas agora'),
    openRows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Aberta em', 'Preço de entrada', 'Valor (USDT)', 'Resultado agora'], openRows, [2, 3, 4])) : h('p', { class: 'sub' }, 'Nenhuma posição aberta agora.'),
    h('h3', null, 'Últimos trades fechados'),
    closedRows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Par', 'Entrada (UTC)', 'Saída (UTC)', 'Duração', 'Motivo', 'Resultado', 'Lucro'], closedRows, [3, 5, 6]))
      : h('p', { class: 'sub' }, `Ainda nenhum trade fechado em ${dlDays(m.days_running)} dias. Day trade precisa operar: sem trade em ${b.inactivity ? b.inactivity.discard_after_days : 2} dias, o robô sai do dry-run.`));
  const stat = (label, value, frac) => h('div', null, h('dt', null, label), h('dd', null, value), frac == null ? null : h('span', { class: 'mini' }, h('i', { style: `width:${Math.max(0, Math.min(100, frac * 100)).toFixed(1)}%;background:var(--c)` })));
  return h('article', { class: 'rx-sc dl-card', style: `--c:${dlVar(b.id)};--i:${i}` },
    h('header', null,
      h('div', { class: 'dl-title' }, h('span', { class: 'dl-id' }, h('i', { class: 'dot', 'aria-hidden': 'true' }), h('a', { href: '#/strategy/' + encodeURIComponent(b.id), 'data-fkey': 'dl-s:' + b.id }, b.id)),
        h('b', null, dlName(b)), h('small', null, `no ar desde ${dlWhen(b.frozen_at)} UTC (${dlDays(m.days_running)} d) · carteira ${nf0.format(b.wallet)} USDT`),
        dlLeftText(dlLeft(b)) ? h('small', { class: dlLeft(b) < 1 ? 'neg' : '' }, '⏱ ' + dlLeftText(dlLeft(b))) : null),
      badge(v)),
    h('div', { class: 'dl-hero' },
      h('div', { class: 'rx-part' }, ring(m.trades / b.need_trades, { size: 70, color: dlVar(b.id), text: nf0.format(m.trades), sub: `de ${b.need_trades}`, label: `${m.trades} de ${b.need_trades} trades fechados` }), h('small', null, 'trades')),
      h('div', { class: 'rx-part' }, ring(m.days_running / b.need_days, { size: 70, color: 'var(--teal)', text: dlDays(m.days_running), sub: 'dias no ar', label: `${dlDays(m.days_running)} dias no ar desde o congelamento` }),
        h('small', null, ok(m.trades_per_day) ? `${nf2.format(m.trades_per_day)} trades/dia` : 'no ar')),
      h('div', { class: 'rx-sc-big dl-money' }, h('small', null, 'Lucro fechado'), h('b', { class: toneOf(m.net_profit) }, usdt(m.net_profit)),
        h('small', null, ok(roi) && m.trades ? `${sp(roi, 2)} da carteira · ${nf0.format(b.open.length)} ${plural(b.open.length, 'aberta', 'abertas')}` : `${nf0.format(b.open.length)} ${plural(b.open.length, 'posição aberta', 'posições abertas')} agora`))),
    h('dl', { class: 'rx-sc-stats' },
      stat('Acerto', ok(m.win_rate) ? pct0(m.win_rate * 100) : dash, ok(m.win_rate) ? m.win_rate : 0),
      stat('Payoff', ok(m.payoff) ? nf2.format(m.payoff) : dash, ok(m.payoff) ? Math.min(1, m.payoff / 3) : 0),
      stat('Fator lucro', ok(m.profit_factor) ? nf2.format(m.profit_factor) : dash, ok(m.profit_factor) ? Math.min(1, m.profit_factor / 3) : 0),
      stat('Queda máx.', pct0(m.max_drawdown_pct), ok(m.max_drawdown_pct) ? Math.min(1, m.max_drawdown_pct / 25) : 0)),
    h('div', { class: 'dl-pairs' }, pairs.map(([pair, x]) => h('a', { class: 'dl-chip', href: `#/aovivo?pair=${encodeURIComponent(pair)}`, title: `Ver ${pair} no gráfico ao vivo`, 'data-fkey': 'dl-chip:' + b.id + pair },
      h('i', { style: `background:${pairColor(pair)}`, 'aria-hidden': 'true' }), short(pair), h('small', null, `${nf0.format(x.trades)} trades${x.open ? ` · ${x.open} aberta${x.open > 1 ? 's' : ''}` : ''}`)))),
    /* the first reason repeats the rings (trades and days of trades); show the rest: pace, warnings, the checks */
    b.reasons.length > 1 || b.verdict !== 'collecting' ? h('ul', { class: 'dl-reasons' }, (b.verdict === 'collecting' ? b.reasons.slice(1) : b.reasons).map(dlReason)) : null,
    h('footer', null, det('dl-bot:' + b.id, 'Posições, trades e resultado por ativo', tables)));
}
function pageDryrunLive() {
  if (!LIVE) return h('div', null, notAvailable('Dry-run ao vivo', 'o snapshot estático não lê os bots. Abra o painel com python -m lab.dashboard serve.'), pageDryrun());
  dlLoadBots(false);
  const lede = h('p', { class: 'rx-lede' }, 'Carteira virtual com preços reais da Binance: nenhuma ordem é enviada e não há chaves de corretora. O veredito usa o número de trades e todas as métricas juntas (regra em lab/config/dryrun.json); "aprovada para análise" só quer dizer que vale uma olhada humana. ',
    h('a', { href: '#/aovivo', 'data-fkey': 'dl-to-live' }, 'Ver o gráfico ao vivo →'));
  const head = h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, 'Acompanhamento · dry-run'), h('h1', { class: 'rx-h1' }, 'Estratégias rodando com dinheiro simulado'), lede);
  if (dl.botsErr && !dl.bots) return h('div', { class: 'rx rx-stack' }, head, card('Estratégias em dry-run', null, notAvailable('Leitura dos bots', dl.botsErr)));
  if (!dl.bots) return h('div', { class: 'rx rx-stack' }, head, card('Estratégias em dry-run', null, loadingState('Lendo os bots…')));
  dlKnow(dl.bots.map((b) => b.id));
  const A = rxAnim(), good = dl.bots.filter((b) => !b.error);
  const sum = (f) => good.reduce((a, b) => a + (f(b) || 0), 0);
  const trades = sum((b) => b.pooled.trades), open = sum((b) => b.open.length), profit = sum((b) => b.pooled.net_profit), wallet = sum((b) => b.wallet);
  const approved = good.filter((b) => b.verdict === 'approved_for_review').length, rejected = good.filter((b) => b.verdict === 'rejected').length;
  const inactive = good.filter((b) => b.verdict === 'inactive').length, retired = dl.retired || [];
  const soon = good.filter((b) => b.verdict === 'collecting' && ok(dlLeft(b)) && dlLeft(b) < 1).length;
  const hero = h('p', { class: 'rx-hero' }, h('em', null, `${good.length} ${plural(good.length, 'estratégia', 'estratégias')}`), ` ${plural(good.length, 'roda', 'rodam')} ao vivo com dinheiro simulado. `,
    trades ? `Juntas, fecharam ${nf0.format(trades)} ${plural(trades, 'trade', 'trades')}` : 'Nenhum trade fechado ainda', open ? ` e têm ${nf0.format(open)} ${plural(open, 'posição aberta', 'posições abertas')} agora.` : '.',
    approved ? ` ${approved} já ${plural(approved, 'pede', 'pedem')} análise humana.` : '',
    rejected ? ` ${rejected} ${plural(rejected, 'foi reprovada', 'foram reprovadas')}.` : '',
    inactive ? ` ${inactive} ${plural(inactive, 'está inativa e sai', 'estão inativas e saem')} no próximo ciclo.` : '',
    soon ? ` ${soon} ${plural(soon, 'sai', 'saem')} em menos de 1 dia se não operar${soon > 1 ? 'em' : ''}.` : '',
    !approved && !rejected && !inactive && !soon ? ' Todas ainda estão coletando evidência.' : '',
    retired.length ? ` ${retired.length} ${plural(retired.length, 'saiu', 'saíram')} do dry-run por não operar.` : '');
  const herocard = h('section', { class: 'card b-7 rx-herocard beam' },
    h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, h('span', { class: 'dl-live', 'aria-hidden': 'true' }), 'Ao vivo agora'), hero),
    h('div', { class: 'rx-kpis' },
      rxKpi('Trades fechados', cnt(trades, fmtInt), 'todas as estratégias'),
      rxKpi('Posições abertas', cnt(open, fmtInt), 'agora'),
      rxKpi('Lucro fechado', h('span', { class: toneOf(profit) + ' rx-glow' }, usdt(profit)), 'após taxas do dry-run'),
      rxKpi('Carteira virtual', cnt(wallet, fmtInt), 'USDT somados, sem dinheiro real')));
  const rule = dl.inactivity;
  const prog = card('Rumo ao veredito', `Cada robô precisa de ${good.length ? nf0.format(good[0].need_trades) : 60} trades fechados e ${good.length ? good[0].need_days : 14} dias antes de qualquer decisão`
    + (rule ? `, e sai do dry-run se passar ${rule.discard_after_days} dias sem fechar um trade.` : '.') + ' A cor de cada robô é a mesma no gráfico ao vivo.', good.length ? dlProgress(good) : emptyState('Nenhum robô.'), { cls: 'b-5' });
  const order = (b) => (b.error ? -1 : ok(dlLeft(b)) ? dlLeft(b) : 99);                 /* closest to the discard first */
  const cards = dl.bots.length ? h('div', { class: 'rx-gallery dl-gallery' }, [...dl.bots].sort((x, y) => order(x) - order(y)).map(dlBotCard))
    : card('Estratégias em dry-run', null, emptyState('Nenhuma estratégia congelada em dry-run.', 'Quando o autopilot subir um bot, ele aparece aqui.'));
  const gone = retired.length ? card('Retiradas do dry-run', `Saíram por não operar (regra do dono: ${rule ? rule.discard_after_days : 2} dias sem trade). O banco de cada uma continua guardado.`,
    h('div', { class: 'tablewrap' }, simpleTable(['Estratégia', 'Congelada em', 'Retirada em', 'Motivo'], [...retired].reverse().map((x) => [
      h('a', { href: '#/strategy/' + encodeURIComponent(x.hypothesis) }, x.hypothesis), dlWhen(x.frozen_at), dlWhen(String(x.at_utc || '').slice(0, 16)),
      (x.reasons || []).filter((t) => /^INACTIVE/.test(t)).map((t) => DL_WORDS.reduce((a, [re, to]) => a.replace(re, to), t).replace(/(\d)\.(\d)/g, '$1,$2')).join('; ') || x.verdict]))), { cls: 'b-12' }) : null;
  return h('div', { class: 'rx rx-stack' + A }, head, h('div', { class: 'bento' }, herocard, prog),
    sectionTitle('Cada estratégia'), cards, gone ? h('div', { class: 'bento' }, gone) : null, sectionTitle('Qualidade de execução'), pageDryrun());
}
pageDryrunLive = guard(pageDryrunLive, 'Dry-run');

/* ---------- page: live chart per asset ---------- */
const dlRgba = (color, a) => {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(color || '').trim());
  if (!m) return color;
  const x = m[1].length === 3 ? m[1].split('').map((c) => c + c).join('') : m[1];
  return `rgba(${parseInt(x.slice(0, 2), 16)},${parseInt(x.slice(2, 4), 16)},${parseInt(x.slice(4, 6), 16)},${a})`;
};
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
const dlCandles = (live) => live.candles.map(([time, open, high, low, close]) => ({ time, open, high, low, close }));
const dlVolume = (live) => { const up = dlRgba(cssVar('--good'), 0.28), down = dlRgba(cssVar('--bad'), 0.28); return live.candles.map(([time, open, , , close, vol]) => ({ time, value: vol || 0, color: close >= open ? up : down })); };
function dlDraw(el, live) {
  const LW = window.LightweightCharts;
  if (dl.refs) { try { dl.range = dl.refs.chart.timeScale().getVisibleRange(); } catch (e) { /* sem faixa */ } dl.refs.chart.remove(); dl.refs = null; }
  if (!LW) { el.replaceChildren(notAvailable('Gráfico', 'a biblioteca de gráficos não carregou.')); return; }
  const grid = dlRgba(cssVar('--p-t-400') || '#888888', 0.12);
  const chart = LW.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: 'rgba(0,0,0,0)' }, textColor: cssVar('--muted'), fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', attributionLogo: true },
    grid: { vertLines: { color: grid }, horzLines: { color: grid } },
    rightPriceScale: { borderVisible: false }, timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false },
    localization: { locale: 'pt-BR' },
    crosshair: { mode: LW.CrosshairMode.Normal, vertLine: { color: dlRgba(cssVar('--accent'), 0.55), labelBackgroundColor: cssVar('--accent') }, horzLine: { color: dlRgba(cssVar('--accent'), 0.55), labelBackgroundColor: cssVar('--accent') } },
  });
  const up = cssVar('--good'), down = cssVar('--bad');
  const volume = LW.HistogramSeries ? chart.addSeries(LW.HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'vol', lastValueVisible: false, priceLineVisible: false }) : null;
  if (volume) { chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } }); volume.setData(dlVolume(live)); }
  const candle = chart.addSeries(LW.CandlestickSeries, { upColor: up, downColor: down, wickUpColor: up, wickDownColor: down, borderVisible: false, priceLineColor: cssVar('--accent') });
  candle.priceScale().applyOptions({ scaleMargins: { top: 0.08, bottom: 0.2 } });
  candle.setData(dlCandles(live));
  const markers = LW.createSeriesMarkers(candle, dlMarkers(live));
  dl.refs = { chart, candle, volume, markers, lines: [], pair: live.pair, tf: live.tf };
  dlLines(live);
  if (dl.range) { try { chart.timeScale().setVisibleRange(dl.range); } catch (e) { chart.timeScale().fitContent(); } }
  else { chart.timeScale().fitContent(); requestAnimationFrame(() => { if (dl.refs && dl.refs.chart === chart) chart.timeScale().fitContent(); }); } /* again after autoSize settles the width */
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
/* last-24h numbers from the candles already on screen */
function dlDay(live) {
  const c = live.candles; if (!c.length) return null;
  const last = c[c.length - 1], from = last[0] + live.step - 86400, day = c.filter((k) => k[0] >= from);
  const base = day.length ? day[0][1] : null, price = ok(live.last_price) ? live.last_price : last[4];
  return { price, change: ok(base) && base ? (price / base - 1) * 100 : null, high: Math.max(...day.map((k) => k[2])), low: Math.min(...day.map((k) => k[3])), vol: day.reduce((a, k) => a + (k[5] || 0), 0) };
}
const dlStamp = (live) => `atualizado às ${new Date(live.served_at * 1000).toLocaleTimeString('pt-BR')} · fonte: ${live.source}`;
const dlFmtPrice = (v) => (ok(v) ? (v >= 100 ? nf2 : new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })).format(v) : dash);
function dlStats(live) {
  const d = dlDay(live) || {}, base = short(live.pair);
  return h('div', { class: 'dl-quote' },
    h('div', { class: 'dl-price' }, h('b', { id: 'dl-price' }, dlFmtPrice(d.price)), h('span', { class: 'dl-unit' }, 'USDT'),
      ok(d.change) ? h('span', { class: 'dl-chg ' + toneOf(d.change) }, (d.change >= 0 ? '▲ ' : '▼ ') + nf2.format(Math.abs(d.change)) + '%', h('small', null, ' 24 h')) : null),
    h('dl', { class: 'dl-day' },
      h('div', null, h('dt', null, 'Máxima 24 h'), h('dd', null, dlFmtPrice(d.high))), h('div', null, h('dt', null, 'Mínima 24 h'), h('dd', null, dlFmtPrice(d.low))),
      h('div', null, h('dt', null, `Volume 24 h (${base})`), h('dd', null, ok(d.vol) ? nf0.format(d.vol) : dash)),
      h('div', null, h('dt', null, 'Robôs neste ativo'), h('dd', null, nf0.format(live.bots.length)))));
}
function dlUpdate() {
  const r = dl.refs, live = dl.live; if (!r || !live) return;
  r.candle.setData(dlCandles(live));
  if (r.volume) r.volume.setData(dlVolume(live));
  r.markers.setMarkers(dlMarkers(live)); dlLines(live);
  const stats = document.getElementById('dl-stats'); if (stats) stats.replaceChildren(dlStats(live));
  const stamp = document.getElementById('dl-stamp'); if (stamp) stamp.textContent = dlStamp(live);
  const open = document.getElementById('dl-open'); if (open) open.replaceChildren(dlOpenList(live));
  const recent = document.getElementById('dl-recent'); if (recent) recent.replaceChildren(dlRecent(live));
}
const dlBotTag = (id) => h('span', { class: 'dl-bt', style: `--c:${dlVar(id)}` }, h('i', { class: 'dot', 'aria-hidden': 'true' }), id);
function dlOpenList(live) {
  const rows = [];
  for (const b of live.bots) for (const t of b.trades.filter((x) => x.is_open)) rows.push([dlBotTag(b.id), dlWhen(new Date(t.open_ts * 1000).toISOString().slice(0, 16)) + ' UTC', dlFmtPrice(t.open_rate), nf2.format(t.stake || 0), h('b', { class: dlTone(t.unrealised_pct) }, ok(t.unrealised_pct) ? dlPct(t.unrealised_pct) : dash)]);
  return rows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Estratégia', 'Aberta em', 'Entrada', 'Valor (USDT)', 'Resultado agora'], rows, [2, 3, 4])) : emptyState('Nenhuma posição aberta neste ativo agora.', 'Quando um robô comprar, a entrada aparece aqui e como linha tracejada no gráfico.');
}
function dlRecent(live) {
  const rows = [];
  for (const b of live.bots) for (const t of b.trades.filter((x) => !x.is_open && x.close_ts)) rows.push({ b: b.id, t });
  rows.sort((x, y) => y.t.close_ts - x.t.close_ts);
  return rows.length ? h('div', { class: 'tablewrap' }, simpleTable(['Estratégia', 'Saída (UTC)', 'Entrada', 'Saída', 'Resultado'], rows.slice(0, 12).map(({ b, t }) => [dlBotTag(b),
    new Date(t.close_ts * 1000).toISOString().slice(0, 16).replace('T', ' '), dlFmtPrice(t.open_rate), dlFmtPrice(t.close_rate), h('b', { class: dlTone(t.profit_pct) }, dlPct(t.profit_pct))]), [2, 3, 4]))
    : emptyState('Nenhuma operação fechada neste ativo ainda.', 'Day trade precisa operar: um robô que passa 2 dias sem trade sai do dry-run automaticamente.');
}
function pageAoVivo(r) {
  if (!LIVE) return notAvailable('Gráfico ao vivo', 'o snapshot estático não busca preços. Abra o painel com python -m lab.dashboard serve.');
  if (r.q.pair && r.q.pair !== dl.pair) { dl.pair = r.q.pair; dl.live = null; dl.range = null; }
  if (r.q.tf && TFS_LIVE.includes(r.q.tf) && r.q.tf !== dl.tf) { dl.tf = r.q.tf; dl.live = null; dl.range = null; }
  dlLoadBots(false);
  const head = h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, 'Acompanhamento · ao vivo'), h('h1', { class: 'rx-h1' }, 'O mercado agora e o que cada robô fez nele'),
    h('p', { class: 'rx-lede' }, 'Preço real da Binance (dados públicos, sem chave) com as entradas (▲) e saídas (▼) de cada robô em dry-run neste ativo. A cor identifica o robô; a linha tracejada é uma posição aberta agora. ',
      h('a', { href: '#/dryrun', 'data-fkey': 'dl-to-dry' }, '← Resultado por estratégia')));
  if (!dl.live && !dl.liveErr) { dlLoadLive(false); return h('div', { class: 'rx rx-stack' }, head, card(`${dl.pair} · ao vivo`, null, loadingState('Buscando candles e operações…'))); }
  if (!dl.live) return h('div', { class: 'rx rx-stack' }, head, card('Gráfico ao vivo', null, h('div', null, notAvailable('Gráfico', dl.liveErr), h('div', { class: 'btnrow', style: 'margin-top:8px' }, h('button', { type: 'button', 'data-fkey': 'dl-retry', onclick: () => { dl.liveErr = null; render(); } }, 'Tentar de novo')))));
  const A = rxAnim(), live = dl.live;
  const go = (pair, tf) => { location.hash = `#/aovivo?pair=${encodeURIComponent(pair)}&tf=${tf}`; };
  const pairBar = h('div', { class: 'dl-pills', role: 'group', 'aria-label': 'Ativo' }, live.pairs.map((p) => h('button', { type: 'button', class: 'dl-pill', 'data-fkey': 'dl-p:' + p, 'aria-pressed': p === live.pair ? 'true' : 'false', onclick: () => go(p, dl.tf) },
    h('i', { style: `background:${pairColor(p)}`, 'aria-hidden': 'true' }), short(p))));
  const tfBar = h('div', { class: 'dl-pills', role: 'group', 'aria-label': 'Tempo de cada candle' }, h('span', { class: 'sub' }, 'Candle'), TFS_LIVE.map((t) => h('button', { type: 'button', class: 'dl-pill', 'data-fkey': 'dl-tf:' + t, 'aria-pressed': t === dl.tf ? 'true' : 'false', onclick: () => go(dl.pair, t) }, t)));
  const chips = h('div', { class: 'dl-toggles', role: 'group', 'aria-label': 'Robôs mostrados no gráfico' }, live.bots.length ? live.bots.map((b) => {
    const n = b.trades.length, off = !!dl.hide[b.id];
    return h('button', { type: 'button', class: 'dl-toggle', style: `--c:${dlVar(b.id)}`, 'aria-pressed': off ? 'false' : 'true', 'data-fkey': 'dl-bot:' + b.id, title: off ? 'Mostrar no gráfico' : 'Esconder do gráfico',
      onclick: (e) => { dl.hide[b.id] = !dl.hide[b.id]; e.currentTarget.setAttribute('aria-pressed', dl.hide[b.id] ? 'false' : 'true'); if (dl.refs) { dl.refs.markers.setMarkers(dlMarkers(live)); dlLines(live); } } },
    h('i', { class: 'dot', 'aria-hidden': 'true' }), b.id, h('small', null, `${n} ${n === 1 ? 'operação' : 'operações'}`));
  }) : [h('span', { class: 'sub' }, 'Nenhum robô em dry-run opera este ativo.')]);
  const chartEl = h('div', { class: 'trchart dl-chart', role: 'img', 'aria-label': `Candles de ${live.pair} com as operações dos robôs em dry-run` });
  queueMicrotask(() => { if (chartEl.isConnected && live.candles.length) dlDraw(chartEl, live); });
  const hero = h('section', { class: 'card b-12 rx-herocard dl-livehero' },
    h('div', { class: 'dl-top' },
      h('div', { class: 'rx-head' }, h('span', { class: 'rx-eyebrow' }, h('span', { class: 'dl-live', 'aria-hidden': 'true' }), `${live.pair} · candles de ${live.tf}`), h('div', { id: 'dl-stats' }, dlStats(live))),
      h('div', { class: 'dl-ctrls' }, pairBar, tfBar)),
    live.error ? h('div', { class: 'notice warn' }, h('div', null, 'Sem conexão com a Binance agora: mostrando os candles do arquivo local (podem estar atrasados).')) : null);
  const chartCard = card(`${live.pair} · gráfico`, h('span', { id: 'dl-stamp' }, dlStamp(live)),
    h('div', { class: 'rx-stack' }, live.candles.length ? chartEl : notAvailable('Candles', 'sem dados para este ativo.'),
      h('div', { class: 'dl-legend sub' }, h('span', null, h('b', { class: 'pos' }, '▲'), ' entrada'), h('span', null, h('b', { class: 'neg' }, '▼'), ' saída com resultado'), h('span', null, h('i', { class: 'dash' }), ' posição aberta'),
        h('span', null, 'Atualiza sozinho a cada 10 s · ', h('a', { href: 'https://www.tradingview.com/', target: '_blank', rel: 'noopener noreferrer' }, 'TradingView Lightweight Charts')))),
    { cls: 'b-12', actions: chips });
  return h('div', { class: 'rx rx-stack' + A }, head, h('div', { class: 'bento' }, hero, chartCard,
    card('Posições abertas neste ativo', 'Resultado calculado com o último preço.', h('div', { id: 'dl-open' }, dlOpenList(live)), { cls: 'b-6' }),
    card('Últimas operações neste ativo', 'As 12 saídas mais recentes de todos os robôs.', h('div', { id: 'dl-recent' }, dlRecent(live)), { cls: 'b-6' })));
}
const TFS_LIVE = ['15m', '1h'];
pageAoVivo = guard(pageAoVivo, 'Gráfico ao vivo');
