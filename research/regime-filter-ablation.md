# Etapa 1.4: ablação do `vol_regime` (2026-11-03)

Janela: apenas exploração (IS) de cada par; validação e holdout não lidos. Custos `base` e `base_2x` (o critério usa `base_2x`). Dados brutos: `research/baselines/regime-ablation.json`; código: `research/tools/{ablation_regime,regime_strategies}.py`.

## Desenho (fixado antes de rodar)
- Família **sma200**: fechamento diário > SMA(200) (`trend_regime`, sempre ligado), execução 1h, sem stop. Com/sem `vol_regime` (30d, razão 1,5).
- Família **donchian**: Donchian 20/10 em candles de **4h**, stop 10%, sem `trend_regime`. Com/sem `vol_regime`.
- Regime ligado = pode entrar; ao desligar, a posição fecha.
- Critério: por par, no IS inteiro a `base_2x`, Sharpe(com) > Sharpe(sem) **e** maxDD(com) < maxDD(sem), e Sharpe(com) < Sharpe(sem) em no máximo 2 dos 5 ciclos. A família mostra benefício com ≥ 2 de 3 pares. O `vol_regime` fica **ligado por padrão só se as duas famílias** mostrarem benefício.
- Justiça: o filtro precisa de ~395 dias diários, então todas as janelas começam no primeiro dia em que ele existe (BTC/ETH 2018-09-16, BNB 2018-12-06), as duas pontas sempre na mesma janela; ciclos limitados ao fim do IS; janelas < 90 dias não pontuam (BNB não pontua 2018).
- Desvio do prompt: não usei `baseline_cycles.py` diretamente porque ele roda a história inteira (inclui validação). A ablação reaproveita suas funções, restrita ao IS. A ponta "sem filtro" da sma200 reproduz a baseline (19 trades em BTC IS, igual ao registro).

## Resultado (IS, `base_2x`, a partir do início do filtro)
| Par | Família | Sharpe sem → com | maxDD sem → com | Retorno sem → com | Trades sem → com | Ciclos pior (de) | Benefício |
|---|---|--:|--:|--:|--:|--:|:-:|
| BTC | sma200 | 1,00 → 0,91 | 67% → 67% | 735% → 459% | 19 → 21 | 1 (5) | não |
| ETH | sma200 | 1,03 → 1,15 | 76% → 54% | 1330% → 1691% | 18 → 18 | 1 (5) | **sim** |
| BNB | sma200 | 1,16 → 0,98 | 78% → 66% | 3193% → 730% | 31 → 32 | 2 (4) | não |
| BTC | donchian 4h | 0,67 → 0,80 | 64% → 60% | 213% → 294% | 190 → 145 | 0 (5) | **sim** |
| ETH | donchian 4h | 0,49 → 0,67 | 79% → 73% | 106% → 246% | 206 → 163 | 1 (5) | **sim** |
| BNB | donchian 4h | 1,00 → 0,87 | 58% → 52% | 1279% → 425% | 194 → 145 | 3 (4) | não |

- sma200: 1 de 3 pares → **sem benefício**. donchian: 2 de 3 → benefício na família.
- **Veredito: `vol_regime` desligado por padrão** (`VOL_REGIME_ON_BY_DEFAULT = False` em `regime_filter.py`). Continua disponível com `use_vol=True`.

## Leitura
O filtro reduz drawdown na maioria dos casos, mas custa retorno e piora o Sharpe na BNB (e no BTC da sma200). A melhora na Donchian 4h vem junto de menos trades; é um resultado de 3 pares, 1 janela, sem intervalo de confiança, e foi lido uma vez. Não é evidência de que o filtro seja útil em geral. Cada par/família/arm/custo conta como teste, mas a ablação não é uma hipótese do ledger.

## Limitações
- Os 395 dias de aquecimento excluem 2017-2018 de todas as comparações (o ciclo 2018 é só o fim de 2018 para BTC/ETH e não pontua para BNB).
- Sharpe a partir de retornos diários da curva rebuilt (marcação 1h), sem Monte Carlo.
