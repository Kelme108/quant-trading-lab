# H-007: lookahead `has_bias=True` em BNB/USDT (etapa 0.3, 2026-11-03)

Hipótese não reaberta; decisão do ledger inalterada ("rejected at exploration").

## Reprodução
`lookahead-analysis` isolado em BNB/USDT, janela de exploração (1509937200-1721887200), custo base, estratégia H-007 arquivada copiada temporariamente (SHA conferido). CSV: `research/experiments/h007-la-bnb-0.3/raw/lookahead-h007-la-bnb-0.3.csv`.

`has_bias=True`, `total_signals=20`, **`biased_entry_signals=1`**, `biased_exit_signals=0`, **`biased_indicators` vazio**. Ou seja, nenhum indicador diverge; diverge uma única entrada.

## Qual sinal
O log do analisador aponta `timerange: 2019-05-15 03:00 - 2019-05-17 03:00, idx 5`. É o trade que abre em **2019-05-15 03:00** (e fecha por stop em 2019-05-17 03:00). O sinal nasce no candle de **02:00** (fecha a 25,10, rompendo a máxima de 480 candles).

## Causa: dado (lacuna de 11 h), não código
- A BNB não tem candles entre 2019-05-15 03:00 e 12:00 (o próximo é 13:00). Das 27 lacunas da série, é a única que fica logo após um sinal de entrada da H-007.
- O Freqtrade preenche lacunas com candles planos (preço = último fechamento, volume 0). A entrada em 03:00 ocorre nesse candle sintético, a 25,10.
- O analisador refaz o backtest com os dados truncados na data do sinal. Truncado em 02:00 (`data ends at 2019-05-15 02:00:00` no log), não existe candle 03:00 (o preenchimento só ocorre entre candles reais), então a entrada não aparece e a comparação marca "viés".
- Teste do código: invariância a prefixo com os 370 sinais brutos de entrada na BNB (indicadores recalculados só até cada candle): **0 divergências**. Os canais usam `shift(1)`; o código é causal.
- Controle: `lookahead-analysis` com início da janela em 2019-05-16 (exclui apenas esse sinal): **`has_bias=False`, 0 sinais enviesados** (`h007-la-bnb-0.3-after-gap`).

## O "salto de 23,53%"
É o aviso do Freqtrade `Price jump in BNB/USDT, 1h, spot between two candles of 23.53%`: abertura do 2º candle da série (2017-11-06 04:00) 23,53% abaixo do fechamento do 1º, no lançamento da BNB. Fica 2 anos antes do primeiro sinal, na área de warm-up. **Não tem relação com o viés.** (Já havia causado um falso "recursive instável" no parser, corrigido em `command-log.md`.)

## Consequências
- O viés é artefato de dado + método do analisador; não invalida a lógica da H-007 e não muda a decisão (rejeitada por desempenho).
- Efeito residual real: o backtest entra num candle sintético durante uma pausa de 11 h; a entrada a 25,10 é uma suposição otimista/irreal para esse único trade. Para famílias novas, `lab/dataquality.py` deve continuar sinalizando lacunas; estratégias que entram logo antes de lacunas devem ser lidas com essa ressalva.
