# Portal: reconstrução (2026-11-04)

Servidor: `python -m lab.dashboard serve` → http://127.0.0.1:8765 (somente leitura, só loopback, CSP com nonce).
Verificação ponta a ponta em Chrome real: `node research/tools/portal_e2e.mjs` (40 checagens; precisa do servidor no ar).

## 1. Auditoria (o que existia)

- **Stack:** backend Python (stdlib) em `lab/dashboard.py`; front-end em HTML + JS puro numa página só (`index.html`, `trades_view.js`), gráficos SVG próprios e `lightweight-charts` (vendorizado, usado nos candles). Sem build, sem CDN, sem dependências novas.
- **Dados:** `research/lab.sqlite` (hipóteses, experimentos, métricas, decisões, agentes) e, por experimento, o zip de backtest do Freqtrade (trades, `profit_abs`, ratios `sharpe/sortino/calmar`), candles em `user_data/data`. Cada resultado é uma célula hipótese × par × etapa (exploração / validação) × 4 cenários de custo.
- **Páginas antigas (8):** visão geral, pesquisa com IA, trades, experimentos, estratégias, carteira, risco e validação, dados. Tinham funil, gates, curvas por par, tabela de experimentos e candles; **não** tinham ranking, win rate, profit factor, expectancy, comparação real, nem análise por estratégia.
- **Limitações reais dos dados:**
  - Só existe **backtest**. Não há trades de dry-run (carteira virtual vazia; nenhuma estratégia chegou ao forward test) nem operações reais (o laboratório não tem chaves de corretora). As abas "Dry-run" e "Operações reais" dizem isso e não mostram número inventado.
  - Parâmetros e indicadores de cada estratégia estão só no **texto da regra ex-ante**; não há campos estruturados, então o painel mostra o texto.
  - Taxas pagas são **estimadas** (stake × fee do export); curvas de capital são marcadas nos fechamentos de trades.
  - O ROI depende da **exposição** calibrada por hipótese (15%, 20%...); por isso não é comparável como "quem rende mais" sem olhar o risco.
  - Hipóteses inválidas (H-004) ficam fora: o laboratório descarta seus números.
  - Etapas **nunca são misturadas**: exploração e validação são linhas separadas.

## 2. Nova arquitetura de informação

Menu agrupado: **Análise** (Visão geral, Ranking, Explorador, Comparar) · **Execução** (Backtests, Operações, Experimentos) · **Laboratório** (Pesquisa com IA, Hipóteses, Risco e validação) · **Sistema**. Busca global `Ctrl K` (páginas e estratégias). URLs são compartilháveis (`#/strategy/H-009?stage=exploration&pair=BTC/USDT`, `#/compare?ids=H-005,H-009&stage=exploration`).

| Página | Responde |
|---|---|
| Visão geral | Quem vai melhor, quem tem maior win rate / rentabilidade / menor risco, quem está piorando, quem merece novos testes, como está o sistema. As "respostas" são **calculadas** dos dados |
| Ranking | Estratégias ordenadas por qualquer coluna; filtros de etapa, gates, trades mínimos, ano; seleção para comparar; sparkline e sinais |
| Explorador | Uma estratégia: 6 métricas, curva de capital e drawdown por par, distribuição de ganhos/perdas, calendário mensal, custos, motivos de saída, exploração × validação, backtests, regra |
| Comparar | 2 a 6 estratégias: lucro acumulado sobreposto, risco × retorno, métricas lado a lado (melhor destacado), consistência por ano |
| Backtests | Execuções com período, capital inicial/final, resultado, taxas, gates; versões da mesma família; **abas Backtest / Dry-run / Operações reais separadas** |
| Operações | Candles + operações de um backtest (página existente) |
| Sistema | Modo, bot, banco, dados, ciclo, alertas, integridade, custo da IA |

## 3. Como os números e sinais são calculados (`lab/analytics.py`, testado)

- Win rate com intervalo de Wilson de 95%; profit factor (vazio se não houver perdas, nunca infinito); expectancy (% e USDT); payoff; sequências; histograma; resultado mensal. Sharpe, Sortino e Calmar vêm do Freqtrade.
- **Evidência (0 a 100), não é win rate:** rentabilidade 30 (profit factor e robustez ao cenário de estresse) + risco 25 (queda máxima e retorno/queda) + amostra 20 (trades por par e total) + consistência 25 (pares lucrativos, lucro sem o melhor trade, anos positivos). Limitada a 40 com algum par abaixo de 30 trades e a 60 se os gates rejeitaram: o score nunca contradiz os gates. O win rate não entra na conta (há teste).
- **Sinais**, cada um com o número que o acionou: amostra pequena, drawdown acima do limite, prejuízo, dependência de um trade, sensibilidade a custos, inconsistência entre pares, piorando (último terço com expectativa menor que metade da dos 2/3 iniciais, mínimo de 20 trades), possível overfitting (lucro na exploração e queda forte ou prejuízo na validação), "sem validação".

## 4. Identidade visual e design system

Grafite com elevação por camadas (não por cor), um acento frio (índigo), cores de sinal só com significado (verde ganho, vermelho perda, âmbar cautela). Tipografia: Inter se instalada, senão Segoe UI Variable/system-ui (sem fonte remota por causa da CSP); números tabulares. Tokens em 3 camadas (`--p-*` primitivos → `--bg/--ink/--good…` semânticos → `--card-*/--ctl-*/--row-*` de componente); tema claro e escuro; densidade confortável/compacta; foco visível, alvos de 44px em toque, `prefers-reduced-motion`, alto contraste, impressão.

Referências estudadas (princípios, sem copiar): Linear (hierarquia, elevação por opacidade, densidade), TradingView/Coinbase (gráficos grandes, painéis), Vercel/Stripe (monitoramento e métricas financeiras).

## 5. O que foi preservado e o que mudou no código

- Preservados sem alteração de lógica: banco, gates, runner, cálculos, estratégias, bot, APIs existentes (`/api/state`, `/api/trades`), contrato de dados e seus testes.
- Novos: `lab/analytics.py`, bloco `strategies` no estado (`lab/dashboard.py`), `portal.js`, tokens e componentes em `index.html`, testes `test_lab_analytics.py` e `test_lab_portal_state.py`, `research/tools/portal_e2e.mjs`.
- Removido o código morto da visão geral antiga. O resumo em linguagem natural e o "próximo passo" foram mantidos; a frase sobre validação foi corrigida (dizia que hipóteses já validadas ainda "aguardavam" validação).

## 6. Limites conhecidos

- O layout em tela estreita/celular **não foi verificado visualmente** (o Chrome headless tem largura mínima de janela); as regras responsivas existem, mas sem captura de prova.
- Abaixo de ~1700 px a tabela do Ranking rola na horizontal (as colunas de gráfico e sinais ficam à direita).
- O filtro "Período" do Ranking mostra o ROI **só daquele ano** como coluna; as demais métricas continuam sendo da etapa inteira (o painel não recalcula tudo por ano).
