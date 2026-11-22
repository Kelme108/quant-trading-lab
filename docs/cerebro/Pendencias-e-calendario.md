---
tipo: pendencias
atualizado: 2026-11-22
tags: [cerebro, pendencias, calendario]
---

# Pendências e calendário

## Datas que vencem

| Data | O que | Quem |
|---|---|---|
| **antes de 2026-12-01** | Trocar `WDOZ26` por `WDOF27` nas configs dos robôs de dólar (P-026 em WDO) | Claude, com aviso ao dono |
| **antes de 2026-12-16** | Trocar `WINZ26` por `WING27` em **todos** os robôs WIN (23 configurados hoje) | Claude |
| 2026-12-16 | Fim da janela do programa de agentes B3 (`b3/config/b3_program.json`) | decisão do dono |
| 2026-12-31 | Fim da exploração do programa de ticks; leitura de decisão só depois | [[B3-WIN-WDO]] |
| quando o B3 publicar | **Calendário de feriados de 2027** só a partir do **Ofício Circular oficial**, nunca de memória | Claude |

## Esperando o dono

- **Abrir o terminal da Clear e entrar na conta demo** quando quiser os robôs de volta: os 25 estão parados (reinício do PC de 2026-11-20 e fim de semana sem pregão). **Não religar o E-164** ([[Robos-demo]]; [[Estado-atual]]).
- Rodar `ops/windows/install-demo-p032-task.ps1`: cria as tarefas das 08:40 de P-032 e dos 11 robôs da esteira. Sem isso, um reinício do PC deixa esses robôs desligados.
- **Não reiniciar o PC** com os robôs ligados.
- **GitHub**: seis decisões antes do primeiro push (visibilidade, licença, configs da conta real, frente de controles ao vivo, lote B-010 abandonado, nome nas aprovações). Lista e recomendações em [[Publicar-no-GitHub]].
- **Validação das três candidatas por t** (E-410 com B1, E-303 com S2, E-286 com B5): leitura única, só com o aval do dono. Para a **P-004**, cuja validação já foi lida, decidir se vale refazer só a conta de custo sobre os trades daquela leitura (zona cinzenta da regra "ler uma vez").
- **Teto da esteira**: o ciclo reserva US$ 3 por chamada, mas cada lote custa US$ 0,2 a 0,3 no Sonnet; a noite de 21→22 parou em US$ 12,07 de US$ 15. Baixar a reserva para ~US$ 1 é uma linha em `b3/esteira_cycle.py`.
- Decidir o que fazer com MES/MNQ quando retomar: fonte de dados e corretora para uso ao vivo ([[2026-11-20-mes-mnq-adiado]]).
- Decidir sobre as **19 candidatas da última noite** (melhor: E-377) depois de ver o pregão de hoje.
- Cotação da **Nelogica** e a **linha de fluxo** (ticks de agressor): pendentes, sem prazo.
- Destino da pasta antiga `D:\Clear-MT5-Real` (pergunta aberta sobre apagar).
- Aprovar o merge da seção "ao vivo" do portal (branch `feat/portal-controls`) quando quiser.
- Destrancar o teste final: só o dono, e só para uma regra por vez.

## Para a próxima sessão do Claude

0. Saídas em reais: a rodada de 2026-11-20 terminou (relatório em `research/b3/exit_brl/`, resumo em [[2026-11-20-saidas-em-reais-35-90]]). `b3/esteira_live.py` **já lê** o tipo `["brl", valor]` (teste `tests/b3/test_esteira_live_brl.py`). Antes de ligar robô novo na demo, alinhar duas diferenças com a pesquisa ([[2026-11-21-auditoria-backtest-demo]]): stop e alvo ao vivo saem do fechamento do sinal e na pesquisa saem da abertura do minuto seguinte; e o trailing da S4 ao vivo sobe a cada barra da estratégia, na pesquisa a cada minuto.
1. Depois de um pregão com os robôs ligados: comparar cada robô com a pesquisa (acerto, resultado por trade, motivos de saída) e registrar em [[Demo-diario]]. Ver [[Robos-demo]].
2. Revisar `ops/state/exit_menu/picks.jsonl`: aplicar a regra "candidata **e** p90 > 0", checar paridade e só então propor robô.
3. Mover relatórios novos de `ops/state/exit_menu/` para `research/b3/exit_menu/` e commitar (só com a esteira parada e a trava livre).
4. Commitar `live/core/engine.py` e `live/run.py` (hoje misturam MOVE_STOP e controles do portal) quando o dono aprovar.
5. Retomar a esteira só se o dono pedir (apagar `ops/state/STOP_ESTEIRA`).

## Dívidas conhecidas

- Falha preexistente em `tests/archive` (h019), sem relação com a linha B3.
- A E-166 passou no menu de saídas mas usa barras do dólar; o robô de índice não as recebe. Ficou de fora.
- `docs/funcionamento-geral.md` descreve a linha cripto de 2026-11-08 e está desatualizado. Ver [[Cripto-Freqtrade]].
