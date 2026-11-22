---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, robos, demo]
---

# Robôs na demo

Todos rodam no terminal **Clear demo** (conta hedging), 1 contrato, via `ops/windows/demo-b3.cmd <nome>` (`live.run` com `live/config/<nome>.json`). **Demonstração, não evidência.** Motor: [[Engine-live]]. Como foram escolhidos os da esteira: [[Menu-de-saidas]].

Estado em 2026-11-19: **24 rodando** (todos abaixo, menos `demo-b3-p004-wdo`, desligado). Sessão: entradas 15 min após a abertura até 30 min antes do fechamento, zeragem 10 min antes do fim. Limite de entradas por dia: 10 (P-004: 2, P-032: 4). Perda diária máxima do robô: R$ 300.

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

Taxa de acerto e resultado por trade são da **pesquisa** (exploração, custo medido), para comparar com a demo. Parâmetros da variante em `live/config/<robô>.json` (`strategy.esteira`).

| Robô | TF | Magic | Saída | Parâmetros | Acerto pesquisa | Por trade pesquisa | Família |
|---|---|---|---|---|---|---|---|
| `demo-b3-e040-win` | 1m | 262040 | S2 | `{"k": 4}` | 66.8% | +R$ 1.91 | E-040: Clock-hour open defence |
| `demo-b3-e062-win` | 5m | 262062 | S2 | `{"run": 3, "k": 0.8}` | 67.9% | +R$ 2.55 | E-062: Rising-volume run follow |
| `demo-b3-e102-win` | 5m | 262102 | S3 | `{"n": 14, "th": 45}` | 42.4% | +R$ 2.44 | E-102: Choppiness-index trend onset |
| `demo-b3-e118-win` | 5m | 262118 | S2 | `{"win_min": 10, "k": 1.0}` | 68.1% | +R$ 3.93 | E-118: Close-vs-midpoint divergence fade |
| `demo-b3-e156-win` | 1m | 262156 | S3 | `{"k": 1.25, "win_min": 60}` | 41.1% | +R$ 3.87 | E-156: Post-wide-day consolidation fade |
| `demo-b3-e160-win` | 5m | 262160 | S2 | `{"tail_min": 15, "q": 0.1}` | 65.2% | +R$ 2.30 | E-160: Hour-end painting fade |
| `demo-b3-e164-win` | 5m | 262164 | S3 | `{"win_min": 60, "k": 1.5}` | 42.2% | +R$ 3.33 | E-164: Macro-backed dip buy |
| `demo-b3-e193-win` | 5m | 262193 | S2 | `{"step": 0.33, "k": 0.0}` | 66.2% | +R$ 2.72 | E-193: Volume-clock milestone momentum |
| `demo-b3-e209-win` | 5m | 262209 | S3 | `{"k": 0.75, "win_min": 15}` | 42.9% | +R$ 3.53 | E-209: Post-narrow-session break follow |
| `demo-b3-e217-win` | 1m | 262217 | S2 | `{"q": 0.1, "pb": 2}` | 68.1% | +R$ 1.65 | E-217: Open-drive day pullback resumption |
| `demo-b3-e225-win` | 1m | 262225 | S2 | `{"n_sessions": 5, "k": 4}` | 65.7% | +R$ 1.89 | E-225: Multi-day channel edge micro-break fade |

## Como ler os resultados da demo

- Saídas **S2** acertam ~65–68% com ganhos pequenos e perdas maiores; **S3** acertam ~41–43% com ganho médio ~2× a perda. Sequências de 5–7 perdas em S3 são normais.
- Comparar sempre com a pesquisa: acerto, resultado por trade, motivos de saída (`target`, `stop`, `time`, `flatten`).
- Rolagem de contrato pendente: [[Pendencias-e-calendario]].
- Controle manual só pelo arquivo de comando: [[Regras-inviolaveis]].
