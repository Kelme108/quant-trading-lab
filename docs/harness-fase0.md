# Fase 0: harness de validação (plano das 5 estratégias)

Nenhuma estratégia nova foi implementada. Esta fase entrega dados, informative diário, custos, estatística e baselines. Parada aguardando aprovação para a Fase 1.

## 1. Dados e informative diário

- Candles 1d de BTC/ETH/BNB baixados (último candle fechado: 2026-11-02; o dia incompleto não vem). `lab/dataquality.py` confere: alinhamento 00:00 UTC, sem duplicatas, ordem, candles fechados no momento do uso, e **igualdade do 1d com a agregação do 1h** (abertura = primeira, máxima, mínima, fechamento = última). Resultado: **0 divergências em ~3.300 dias por par**.
- **Warm-up (teste empírico, não suposição):** o Freqtrade carrega `startup_candle_count` candles de **cada** timeframe usado. Com `startup_candle_count = 10` a SMA(200) diária fica NaN (0 trades); com 200 ou 4800 há sinal desde o primeiro dia. Logo **SMA(200) em 1d funciona com `startup_candle_count = 200`**; o limite de 4500 candles de 1h não se aplica a informative diário e **não foi preciso reduzir para SMA(150)**. A baseline usa 210 (margem).
- **Alinhamento causal (`research/tools/check_informative.py`, roda no container com o `merge_informative_pair` real, dados reais 2022+):** (1) o valor diário visível na linha 1h de data t é o candle do dia `floor(t+1h) - 1 dia`: o Freqtrade o expõe na linha das 23:00, cujo fechamento (00:00 UTC) é o fechamento do dia, e a ordem só executa na abertura seguinte; 0 divergências em 42.329 linhas. (2) Corromper todos os candles diários a partir de 2023-06-01 não altera nenhuma linha anterior (0 de 12.383).

## 2. Custos (validação)

Contagem por lado = fee + slippage + spread/2, aplicada **uma vez na entrada e uma na saída** pelo `--fee`. Conferido em trades reais exportados (H-012, quatro cenários): `profit_ratio = bruto*(1-f)/(1+f) - 1` com erro máximo de 2,7e-10. Portanto fee, spread e slippage **não são contados em dobro**.

| Cenário | fee | slip/lado | spread total | efetivo/lado | round trip | x base |
|---|--:|--:|--:|--:|--:|--:|
| optimistic | 0,10% | 0 | 0 | 0,100% | 0,200% | 0,57 |
| base | 0,10% | 0,05% | 0,05% | 0,175% | 0,349% | 1,00 |
| conservative | 0,10% | 0,10% | 0,10% | 0,250% | 0,499% | **1,43** |
| stress | 0,10% | 0,25% | 0,25% | 0,475% | 0,946% | 2,71 |
| **base_2x** (novo) | 0,20% | 0,10% | 0,10% | **0,350%** | **0,698%** | **2,00** |

O "conservative" do protocolo **não** é o dobro do base; por isso foi criado `base_2x` (todos os componentes dobrados), usado nos relatórios comparativos. Os 4 cenários dos gates ficam inalterados (`base_2x` não é obrigatório nos gates). Testes: `tests/test_lab_costs_2x.py`.

## 3. Estatística (`lab/stats.py`, sem scipy)

Sharpe, PSR, **Deflated Sharpe** (SR0 pelo máximo esperado de N tentativas), **PBO por CSCV** e IC por block bootstrap (marca `low_sample` abaixo de 100 observações). Testes: SR0(N=2) ≈ E[max de 2 normais]; SR0(N=100) ≈ 2,5; DSR(N=1) = PSR e cai quando N cresce; PBO ≈ 0,5 em ruído puro e < 0,1 com um edge real persistente; ICs reprodutíveis por semente. `n_trials` vem do registro de hipóteses (cada configuração do grid conta).

## 4. Retornos, ciclos, holdout, walk-forward

- `lab/returns.py`: reconstrói a curva de equity horária (mark-to-market, custos e exposição fixa) a partir dos trades exportados. Teste: o final bate com o produto `1 + w*profit_ratio` dos trades a 1e-12. Contra o Freqtrade, o retorno total difere ~0,14% (BTC 6,3857 vs 6,3947) porque o Freqtrade arredonda o stake (99,95 de 100) e deixa saldo residual; o produto dos `profit_ratio` exportados é idêntico à curva reconstruída.
- `lab/cycles.py` + `lab/config/holdout.json`: ciclos 2018, 2019, 2020-21, 2022, 2023+ (todos terminam antes do corte); rótulos IS (exploração), OOS (validação) e **últimos 12 meses (semi-contaminados: 2025-10-21..2026-10-20)**; **holdout prospectivo = dados a partir de 2026-10-21**, nunca usado para otimização. Avaliação: não antes de **2027-04-21**, preferencialmente 2027-10-21, e somente com **>= 30 trades fechados** (senão relatado como inconclusivo com IC); uma avaliação por estratégia congelada; `final_test_unlocked` continua `false` e só o usuário altera. `assert_before_holdout` impede janelas históricas de tocá-lo.
- `lab/walkforward.py`: walk-forward ancorado (escolhe a melhor configuração do grid pelo Sharpe de treino e avalia no ano seguinte); teste garante que a seleção usa só o treino.
- `lab/causality.py`: testes genéricos anti-lookahead (invariância a prefixo e corrupção do futuro). Detectam `shift(-1)`, normalização da série inteira e máximo global.

## 5. Baselines por ciclo (BTC/USDT, `research/baselines/sma200-cycles.json`)

Baseline `Sma200Baseline` (fechamento diário > SMA(200) diária, execução 1h, sem stop; congelada por SHA em `test_protected_files.py`). `lookahead-analysis`: sem viés. `recursive-analysis`: estável. 33 trades na história.

| Janela | Trades | SMA200 retorno | maxDD | Sharpe | B&H retorno | maxDD | Sharpe |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2018 | 2 | -35% | 37% | -2,42 | -73% | 81% | -1,14 |
| 2019 | 2 | 57% | 45% | 1,09 | 94% | 53% | 1,31 |
| 2020-21 | 12 | 113% | 65% | 0,93 | 543% | 60% | 1,59 |
| 2022 | 0 | 0% | 0% | 0,00 | -65% | 67% | -1,31 |
| 2023+ | 17 | 241% | 35% | 1,05 | 401% | 54% | 1,15 |
| IS (exploração) | 19 | 477% | 66% | 0,79 | 1250% | 84% | 0,89 |
| OOS (validação) | 14 | 28% | 35% | 0,50 | 42% | 54% | 0,56 |
| últimos 12m (semi-contaminado) | 3 | 10% | 11% | 0,64 | -25% | 50% | -0,43 |
| história completa | 33 | 639% | 66% | 0,73 | 1824% | 84% | 0,82 |

(custos base; com `base_2x`: 558% na história completa, Sharpe 0,70.) ETH e BNB estão no JSON.

**Leitura:** a regra de tendência simples corta o drawdown (2022 inteiro em caixa, 2018 perde menos) mas **não bate o buy-and-hold em Sharpe na história completa nem em quase nenhum ciclo** (só nos últimos 12 meses e em 2018/2022, anos de queda). Essa é a barra: uma estratégia nova que não supere o B&H e esta SMA(200) ajustada ao risco no OOS é descartada. Cada ciclo tem poucos trades (0 a 17); ICs são largos.

## Limitações conhecidas

1. Baselines e ciclos usam a série de preços inteira, inclusive a janela de validação e os últimos 12 meses (a série de preços é a mesma já vista por experimentos anteriores); por isso essas janelas estão rotuladas e o único dado realmente virgem é o holdout prospectivo.
2. As janelas por ciclo cortam posições abertas na fronteira (mark-to-market), o que é consistente entre estratégia e B&H, mas não idêntico a rodar um backtest separado por janela.
3. DSR/PBO assumem que o `n_trials` informado é o número real de configurações tentadas, e retornos diários aproximadamente independentes.
4. O stake do Freqtrade é arredondado; a curva reconstruída usa o `profit_ratio` exportado (diferença ~0,14% no total).

## Arquivos

Novos: `lab/dataquality.py`, `lab/stats.py`, `lab/returns.py`, `lab/cycles.py`, `lab/walkforward.py`, `lab/causality.py`, `lab/config/holdout.json`, `user_data/strategies/Sma200Baseline.py`, `research/tools/{check_informative,baseline_cycles,baseline_table}.py`, `research/baselines/sma200-cycles.json`, testes `test_lab_{stats,returns,cycles_holdout,causality_dataquality,costs_2x}.py` e `test_sma200_baseline.py`. Alterados: `lab/costs.py` (cenário `base_2x`, `cost_table`), `tests/test_protected_files.py` (hash da baseline), `tests/test_lab_dashboard.py` (dashboard lista `base_2x`). Dados 1d baixados em `user_data/data/binance/`.
