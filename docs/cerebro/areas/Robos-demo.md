---
tipo: area
atualizado: 2026-11-22
tags: [cerebro, robos, demo]
---

# Robôs na demo

Todos rodam no terminal **Clear demo** (conta hedging), 1 contrato, via `ops/windows/demo-b3.cmd <nome>` (`live.run` com `live/config/<nome>.json`). **Demonstração, não evidência.** Motor: [[Engine-live]]. Como foram escolhidos os da esteira: [[Menu-de-saidas]].

Estado em 2026-11-22: **25 robôs configurados (14 regras P e 11 da esteira), 0 rodando**. Ficaram parados de propósito no fim de semana (mercado fechado) e desde o reinício do PC de 2026-11-20; religar é com o terminal da Clear aberto na conta demo ([[Pendencias-e-calendario]]). Sessão: entradas 15 min após a abertura até 30 min antes do fechamento, zeragem 10 min antes do fim. Limite de entradas por dia: 10 (P-004: 2, P-032: 4). Perda diária máxima do robô: R$ 300.

**E-164 não deve ser religado como está:** a família usa o fechamento do dólar (`other_close`) e o robô ao vivo só recebe barras do índice, então erra em toda barra. Antes: dar barras de WDO ao robô, ou tirá-lo da demo.

## Regras de agente (P-NNN)

| Robô | Mercado | TF | Magic | Regra |
|---|---|---|---|---|
| `demo-b3-p004-wdo` | WDOZ26 | 5m | 261605 | **P-004**: momentum do resto do dia (última meia hora), 5m; única que passou a exploração de WIN e reprovou na validação |
| `demo-b3-p004-win` | WINZ26 | 5m | 261604 | **P-004**: momentum do resto do dia (última meia hora), 5m; única que passou a exploração de WIN e reprovou na validação |
| `demo-b3-p014-win` | WINZ26 | 5m | 261714 | **P-014**: fade de barra de 5 min com volume e movimento anormais para o horário |
| `demo-b3-p017-win` | WINZ26 | 1m | 261717 | **P-017**: fade de rompimento de 60 min que volta para dentro em até 5 barras (stop sweep) |
| `demo-b3-p020-win` | WINZ26 | 5m | 261720 | **P-020**: fade de movimento grande de 15 min com volume normal ou baixo |
| `demo-b3-p023-win` | WINZ26 | 1m | 261723 | **P-023**: seguir movimento de 30 min feito de muitos minutos pequenos do mesmo sinal |
| `demo-b3-p024-win` | WINZ26 | 5m | 261724 | **P-024**: fade de corrida de 30 min quando barra de 5 min tem volume alto e quase não move (absorção) |
| `demo-b3-p025-win` | WINZ26 | 1m | 261725 | **P-025**: fade do impulso de 20 min em torno da abertura, da abertura de NY e do fechamento |
| `demo-b3-p026-wdo` | WDOZ26 | 5m | 261826 | **P-026**: rompimento de caixa de compressão (seguir fechamento de 5 min fora da faixa de 60 min); rejeitada na exploração |
| `demo-b3-p026-win` | WINZ26 | 5m | 261726 | **P-026**: rompimento de caixa de compressão (seguir fechamento de 5 min fora da faixa de 60 min); rejeitada na exploração |
| `demo-b3-p028-win` | WINZ26 | 5m | 261728 | **P-028**: seguir ou fazer fade de movimentos de 15 min conforme razão de variância do dia |
| `demo-b3-p029-win` | WINZ26 | 1m | 261729 | **P-029**: seguir saída de zona de alto volume do perfil do dia para zona fina |
| `demo-b3-p030-win` | WINZ26 | 5m | 261730 | **P-030**: pullback contra a tendência de 5 sessões (comprar quedas de 30 min em alta) |
| `demo-b3-p032-win` | WINZ26 | 1m | 261832 | **P-032**: fade de fechamento fora da caixa comprimida de 2h, 1m, breakeven+trailing (estudo P-026) |

## Famílias da esteira com saída do menu (E-NNN)

Números da **pesquisa** (exploração 2021-11 a 2024-06, 1 contrato, custo medido R$ 1,30 por ida e volta; p90 = custo pessimista R$ 3,00), refeitos em 2026-11-22 com a variante e a saída de cada robô, para comparar com a demo. "Aleatória" é o controle (mesma saída, entradas aleatórias); **t** é a estatística da média por trade, que precisa passar de ~4,6 com as ~35 mil versões lidas, e **nenhum chega perto** (maior: 2,39). Parâmetros da variante em `live/config/<robô>.json` (`strategy.esteira`).

| Robô | TF | Magic | Saída | Parâmetros | Acerto | Por trade | p90 | Aleatória | Trades/ano | Fatias + | t | Família |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `demo-b3-e040-win` | 1m | 262040 | S2 | `{"k": 4}` | 66,8% | +R$ 1,91 | +R$ 0,59 | −R$ 0,80 | 576 | 5/8 | 1,76 | E-040: Clock-hour open defence |
| `demo-b3-e062-win` | 5m | 262062 | S2 | `{"run": 3, "k": 0.8}` | 67,9% | +R$ 2,55 | +R$ 1,24 | **+R$ 0,35** | 265 | 7/8 | 1,55 | E-062: Rising-volume run follow |
| `demo-b3-e102-win` | 5m | 262102 | S3 | `{"n": 14, "th": 45}` | 42,4% | +R$ 2,44 | +R$ 0,89 | −R$ 2,24 | 281 | 5/8 | 1,34 | E-102: Choppiness-index trend onset |
| `demo-b3-e118-win` | 5m | 262118 | S2 | `{"win_min": 10, "k": 1.0}` | 68,1% | +R$ 3,93 | +R$ 2,62 | −R$ 0,92 | 368 | 7/8 | 2,32 | E-118: Close-vs-midpoint divergence fade |
| `demo-b3-e156-win` | 1m | 262156 | S3 | `{"k": 1.25, "win_min": 60}` | 41,1% | +R$ 3,87 | +R$ 2,34 | −R$ 1,20 | 418 | 6/8 | 2,24 | E-156: Post-wide-day consolidation fade |
| `demo-b3-e160-win` | 5m | 262160 | S2 | `{"tail_min": 15, "q": 0.1}` | 65,2% | +R$ 2,30 | +R$ 0,97 | −R$ 1,40 | 356 | 5/8 | 1,68 | E-160: Hour-end painting fade |
| `demo-b3-e164-win` | 5m | 262164 | S3 | `{"win_min": 60, "k": 1.5}` | 42,2% | +R$ 3,33 | +R$ 1,77 | −R$ 1,22 | 250 | 7/8 | 1,37 | E-164: Macro-backed dip buy (**não religar**) |
| `demo-b3-e193-win` | 5m | 262193 | S2 | `{"step": 0.33, "k": 0.0}` | 66,2% | +R$ 2,72 | +R$ 1,40 | −R$ 0,77 | 588 | 6/8 | 2,25 | E-193: Volume-clock milestone momentum |
| `demo-b3-e209-win` | 5m | 262209 | S3 | `{"k": 0.75, "win_min": 15}` | 42,9% | +R$ 3,53 | +R$ 1,97 | −R$ 1,31 | 547 | 7/8 | 2,39 | E-209: Post-narrow-session break follow |
| `demo-b3-e217-win` | 1m | 262217 | S2 | `{"q": 0.1, "pb": 2}` | 68,1% | +R$ 1,65 | +R$ 0,34 | −R$ 0,22 | 263 | 6/8 | 0,98 | E-217: Open-drive day pullback resumption |
| `demo-b3-e225-win` | 1m | 262225 | S2 | `{"n_sessions": 5, "k": 4}` | 65,7% | +R$ 1,89 | +R$ 0,57 | −R$ 1,61 | 930 | 7/8 | 2,10 | E-225: Multi-day channel edge micro-break fade |

## Regras P: números da exploração (2026-11-22)

Mesma conta, na saída própria de cada regra, com R$ por contrato convertido do retorno em % (aproximado). Só a **P-004 em WIN** passa a barra nova (t 5,96, positiva em 8 de 8 fatias), e a validação dela **já foi lida** em 2026-11-16, então não pode ser relida. P-004 em WDO perde. As demais ficam perto de zero ou negativas:

| Regra | Mercado | Acerto | Por trade | p90 | Trades/ano | Fatias + | t |
|---|---|---|---|---|---|---|---|
| P-004 | WIN | 60,5% | +R$ 7,62 | +R$ 6,12 | 246 | 8/8 | 5,96 |
| P-014 | WIN | 53,3% | +R$ 1,40 | −R$ 0,29 | 225 | 6/8 | 0,64 |
| P-032 | WIN | 36,3% | +R$ 3,32 | +R$ 1,37 | 256 | 6/8 | 0,77 |
| P-029 | WIN | 28,2% | +R$ 3,65 | +R$ 2,05 | 15 | 4/8 | 0,48 |
| P-030 | WIN | 49,5% | +R$ 0,04 | −R$ 1,74 | 707 | 5/8 | −0,02 |
| P-017 | WIN | 43,5% | −R$ 0,07 | −R$ 1,72 | 1.020 | 5/8 | −0,02 |
| P-020, P-023, P-024, P-025, P-026, P-028 | WIN | 31–55% | −R$ 0,90 a −R$ 5,10 | negativo | 514–931 | 1–4/8 | −0,87 a −3,35 |
| P-004, P-026 | WDO | 41–43% | −R$ 4,51 e −R$ 5,04 | negativo | 245 e 475 | 2–4/8 | −1,55 e −2,39 |

## Como ler os resultados da demo

- Saídas **S2** acertam ~65–68% com ganhos pequenos e perdas maiores; **S3** acertam ~41–43% com ganho médio ~2× a perda. Sequências de 5–7 perdas em S3 são normais.
- Comparar sempre com a pesquisa: acerto, resultado por trade, motivos de saída (`target`, `stop`, `time`, `flatten`).
- Rolagem de contrato pendente: [[Pendencias-e-calendario]].
- Controle manual só pelo arquivo de comando: [[Regras-inviolaveis]].
