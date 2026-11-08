# Estudo: day-trader-skill e o que trouxemos para o lab

Fonte: [github.com/jakeschincariol/day-trader-skill](https://github.com/jakeschincariol/day-trader-skill), commit
`3d0f4ef` de 20/10/2026, licença MIT (Jake Schincariol). Lido em 08/11/2026. Nenhum código de lá roda aqui; o que
veio foi o método, reescrito para o nosso lab.

## 1. O que é o projeto

Um pacote de 11 "skills" do Claude para day trade de **ações americanas**, com um humano decidindo cada ordem.
Cada skill é um script Python simples que lê dados gratuitos (Yahoo Finance, Nasdaq Trader, SEC) e escreve um
arquivo JSON numa pasta `trader/`; a próxima skill lê o que a anterior escreveu:

```
scanner -> news -> entry -> exit -> timemachine -> budget -> risk -> broker   (uma operação)
alerts: stop, alvo, zerar no fechamento                                       (com a posição aberta)
```

| Skill | O que faz |
|---|---|
| scanner | varre milhares de gráficos atrás de setups: rompimento da faixa de abertura (ORB), bandeira, sobrevenda |
| news | manchetes e comunicados (8-K) das ações acompanhadas |
| entry | espera, candle a candle, o primeiro candle de 5 min que **fecha** acima da faixa |
| exit | define stop (meio da faixa, mínima da faixa, %, ATR) e alvo (1R, 2R) **antes** de entrar; zera às 15:55 |
| timemachine | 10.000 replays do resto do pregão + o histórico real da mesma regra; dá um veredito honesto |
| budget | tamanho da posição pela perda máxima por trade |
| risk | barra ordens que estouram limites: perda por trade, perda do dia, trades por dia, janela de horário |
| broker | envia a ordem (Alpaca, conta papel por padrão), só com o seu "sim" |
| alerts, analyst, pelosi | alertas de preço, balanço de empresas, operações de deputados americanos |

O exemplo do próprio autor (TSLA, 19/10/2026) termina com a Time Machine dizendo: **"perto de cara ou coroa"**. É o
ponto mais valioso do projeto: medir antes de arriscar, e dizer a verdade quando não há vantagem.

## 2. O que dá e o que não dá para usar aqui

Nosso lab é outro mundo: **cripto spot na Binance**, robôs automáticos no Freqtrade, mercado 24 horas, pesquisa feita
por agentes com gates estatísticos. Então:

- **Não serve direto:** scanner de ações, notícias da SEC, Pelosi, o broker Alpaca (só ações; o risk deles bloqueia
  cripto), o calendário da NYSE.
- **Serve, adaptado:** a regra ORB com stop no meio da faixa e alvo em R; a Time Machine; os limites de risco do dia.

## 3. O que foi implementado

### 3.1 Time Machine para cripto (`lab/timemachine.py`)

Mesmo método, adaptado: candles de 15 min da Binance (os nossos), sessões em UTC, custo do lab descontado.

```
python -m lab.timemachine BTC/USDT --date 2023-03-13 --entry-time 14:15 --entry 22918.8 \
    --stop 22380.3 --target 23995.9 --session-start 13:30 --session-hours 6.5
```

1. **Replays:** reconstrói o resto da sessão 10.000 vezes sorteando candles do mesmo horário dos últimos 60 dias.
   Stop primeiro, depois alvo; um candle que toca os dois conta como stop (conservador). Semente fixa (19): o mesmo
   plano dá sempre o mesmo número.
2. **Histórico:** roda a mesma regra de faixa de abertura em cada um desses 60 dias reais.
3. **R líquido:** além do R da regra, mostra o R depois do custo (0,30% ida e volta no cenário base).
4. **Veredito** com os mesmos limiares do original: cara ou coroa, tende ao alvo/stop, fortemente.

Ela é ferramenta de pesquisa e de acompanhamento do dry-run, **não é gate**. Um plano com data dentro da validação ou
depois sai marcado como "monitoramento, não avaliação".

**Primeira lição dela:** num ORB de 15 min em cripto, a faixa de abertura costuma ser estreita, o stop no meio da faixa
fica a 0,2-0,3% da entrada, e os 0,30% de custo viram **1 a 1,5R por operação**. Por isso a H-034 perdeu. Toda regra
de "bracket" agora precisa de uma distância mínima de stop de ~1% do preço.

### 3.2 A regra ORB do projeto como hipótese

- **H-069** já era o ORB da abertura de Nova York com saída no fechamento. Ela tinha sido descartada **só** porque a
  calibração pedia uma posição abaixo da ordem mínima na carteira de 100 USDT; nenhum backtest de exploração tinha
  rodado.
- Novo comando `python -m lab.pipeline recalibrate H-...`: traz do arquivo o código **byte a byte idêntico** (hash
  SHA-256 conferido), roda calibração e exploração de novo com a carteira de 1000 USDT, sem reescrever nada e sem
  chamar agente. Só aceita hipóteses descartadas por esse motivo e sem decisão de gate (não é segunda tentativa).
  H-069 e as outras descartadas pelo mesmo motivo voltam assim.
- Uma ideia nova, terceira e última variante da família `SessionOpeningRangeBreakout`: faixa dos primeiros 30 min
  após 13:30 UTC, só em dias com faixa >= 2%, entrada no primeiro fechamento acima da faixa, stop no meio, alvo 2R,
  zera às 20:00 UTC, um trade por dia.

### 3.3 Limites de risco do dia

Os agentes passaram a conhecer os blocos de montagem de day trade do projeto: bracket (stop e alvo definidos antes),
limite de entradas por dia e parada do dia depois de perdas. O developer sabe implementá-los no Freqtrade
(`protections` como `StoplossGuard`/`MaxDrawdown`, ou contagem em `confirm_trade_entry`), sempre que a proposta pedir.

## 4. O que o projeto ensina, em uma frase

Antes de arriscar: defina a saída antes da entrada, meça a chance real com os dados do próprio ativo, desconte o
custo, e aceite "cara ou coroa" como resposta.
