# Revisão completa das estratégias: day trade, boas e com muitos trades (12/11/2026)

Pedido do dono: "revisão completa sobre as estratégias, queremos day trade apenas, estratégias boas e que façam bastante trades".
Dados: as listas reais de trades da exploração de cada hipótese (custo base, 0,30% ida e volta). Validação e holdout não foram lidos.
Tabela completa: [research/knowledge/scoreboard.md](../knowledge/scoreboard.md), gerada por `python -m lab.knowledge`.

## Conclusão

**Nenhuma das 80 hipóteses com trades é ao mesmo tempo day trade, frequente e lucrativa depois do custo.**

| Filtro | Hipóteses |
|---|--:|
| Com lista de trades de exploração | 80 |
| Day trade (95% das posições fechadas em até 24 h) | 56 |
| Day trade e frequente (100 ou mais trades por ano por par) | 17 |
| Day trade, frequente e com lucro líquido médio por trade | **0** |

O motivo é um só. As regras frequentes têm movimento bruto médio de no máximo 0,29% por trade (mediana 0,01%), e a ida e volta custa 0,30%. O gatilho delas dispara em barras comuns, onde o preço quase não anda. Os estudos publicados dizem o mesmo: regras intraday técnicas em geral não sobrevivem ao custo (resumo em [research/knowledge/evidence.md](../knowledge/evidence.md)).

## As mais próximas do objetivo

Day trade, com 20 ou mais trades por ano por par, ordenadas pelo líquido por trade:

| Hipótese | Trades/ano/par | Bruto/trade | Líquido/trade | Pares com lucro | 2022-24 |
|---|--:|--:|--:|--:|--:|
| H-104 (Williams + volume) | 28 | 0,69% | 0,38% | 8/9 | perdeu |
| H-101 (Ichimoku + volume) | 21 | 0,63% | 0,33% | 7/9 | ganhou pouco |
| H-043 (Williams) | 38 | 0,54% | 0,24% | 7/9 | perdeu |
| H-100 (RSI + volume) | 50 | 0,44% | 0,14% | 6/9 | perdeu |

As quatro têm o mesmo perfil: gatilho raro em barra de muito volume, com ganho real por trade, mas pouca frequência e perda nos anos de baixa (2022-2024). Todas foram reprovadas na exploração ou na validação.

## Os bots do dry-run

- **Defeito: descartado.** Rodei o backtest de cada bot nos mesmos dias em que ele ficou no ar, com candles novos e a mesma configuração. O backtest também deu 0 trades. A única exceção foi 1 trade da H-009, antes de o bot ser ligado. As estratégias são lentas; os bots funcionam.
- **Regra nova de 2 dias aplicada.** H-001, H-009, H-016, H-043 e H-047 saíram do dry-run: bots parados, congelamentos em `research/forward/retired/`. A retirada agora é automática a cada ciclo.
- **Ficam H-100 a H-104.** Pelo ritmo de exploração, cada um deve fazer de 0,3 a 1,2 trade por dia somando seus pares. Vão ser julgados pela mesma regra.

## O que foi feito para os agentes (retroalimentação)

1. **Placar de day trade no contexto de todo agente** (`lab/knowledge.py`). É reconstruído a cada etapa a partir dos trades reais e mostra três coisas:
   - a troca entre frequência e movimento por trade;
   - as regras mais próximas do objetivo;
   - os mecanismos que viraram ruído (FVG, order block, SMT, Judas sweep, pivô, periodicidade de horário), para não serem repetidos.
2. **Evidência externa com fontes** (`research/knowledge/evidence.md`):
   - momentum intraday dentro da sessão (Financial Review 2022);
   - padrões de volatilidade por hora;
   - comportamento depois de saltos;
   - por que regras intraday técnicas falham no custo.
3. **Fila de fontes reordenada** (`research/sources-queue.md`, seção 0). Primeiro os estudos publicados, depois os repositórios de bots. As fontes ICT/SMC estão esgotadas.
4. **Direção do dono de 12/11** (`research/guidance.md`):
   - pelo menos cerca de 1 trade por dia somando os pares do bot;
   - movimento bruto acima de 0,6% por trade;
   - frequência vinda de muitos pares e gatilhos raros, não de gatilho frouxo;
   - toda proposta declara trades por ano e movimento esperado.

## Decisões que são do dono

O laboratório opera hoje em spot, só compra, com 0,30% de custo por ida e volta. Nessas condições a combinação "day trade + muitos trades + lucro" ainda não apareceu. Três mudanças estruturais aumentariam muito a chance, e cada uma muda o protocolo:

1. **Mais pares no universo.** Exemplo: 25 a 30 pares líquidos em vez de 9.
   - A frequência por bot vem da soma dos pares. H-104 tem 28 trades por ano por par: com 30 pares dá cerca de 2,3 trades por dia, e a chance de passar 2 dias sem trade cai para perto de 1%.
   - É a alavanca mais barata, porque o bot multi-par já existe.
   - Exige baixar dados, cortar novas divisões de exploração e validação e ajustar a regra de amplitude ("6 de 9 pares").
2. **Futuros perpétuos em dry-run.**
   - Na tabela pública da Binance, a taxa de futuros é bem menor que a de spot (a confirmar).
   - Futuros permitem vender a descoberto, o que resolve a perda de 2022-2024.
   - Muda o risco: alavancagem e liquidação, mesmo em dry-run. O Freqtrade suporta futuros em dry-run.
3. **Execução só com ordem limitada (maker).** Corta a derrapagem e parte da taxa no spot, mas algumas ordens não são executadas.

Sem nenhuma dessas mudanças, o loop continua procurando com o placar e a evidência novos, mas a expectativa honesta é baixa.
