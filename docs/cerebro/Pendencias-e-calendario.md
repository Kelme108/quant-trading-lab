---
tipo: pendencias
atualizado: 2026-11-19
tags: [cerebro, pendencias, calendario]
---

# Pendências e calendário

## Datas que vencem

| Data | O que | Quem |
|---|---|---|
| **antes de 2026-12-01** | Trocar `WDOZ26` por `WDOF27` nas configs dos robôs de dólar (P-026 em WDO) | Claude, com aviso ao dono |
| **antes de 2026-12-16** | Trocar `WINZ26` por `WING27` em **todos** os robôs WIN (24 hoje) | Claude |
| 2026-12-16 | Fim da janela do programa de agentes B3 (`b3/config/b3_program.json`) | decisão do dono |
| 2026-12-31 | Fim da exploração do programa de ticks; leitura de decisão só depois | [[B3-WIN-WDO]] |
| quando o B3 publicar | **Calendário de feriados de 2027** só a partir do **Ofício Circular oficial**, nunca de memória | Claude |

## Esperando o dono

- **Abrir o terminal da Clear e entrar na conta demo**, e avisar: os 24 robôs estão parados desde o reinício do PC de 2026-11-20 08:46 ([[Estado-atual]]).
- Rodar `ops/windows/install-demo-p032-task.ps1`: cria as tarefas das 08:40 de P-032 e dos 11 robôs da esteira. Sem isso, um reinício do PC deixa esses robôs desligados.
- **Não reiniciar o PC** com os robôs ligados.
- **GitHub**: conferir se o repositório é **privado** antes do primeiro push (ele traz toda a pesquisa, nomes de servidores e caminhos do terminal) e escolher uma **licença** (hoje nenhuma: todos os direitos reservados).
- Decidir o que fazer com MES/MNQ quando retomar: fonte de dados e corretora para uso ao vivo ([[2026-11-20-mes-mnq-adiado]]).
- Decidir sobre as **19 candidatas da última noite** (melhor: E-377) depois de ver o pregão de hoje.
- Cotação da **Nelogica** e a **linha de fluxo** (ticks de agressor): pendentes, sem prazo.
- Destino da pasta antiga `D:\Clear-MT5-Real` (pergunta aberta sobre apagar).
- Aprovar o merge da seção "ao vivo" do portal (branch `feat/portal-controls`) quando quiser.
- Destrancar o teste final: só o dono, e só para uma regra por vez.

## Para a próxima sessão do Claude

0. Saídas em reais: a rodada de 2026-11-20 terminou (relatório em `research/b3/exit_brl/`, resumo em [[2026-11-20-saidas-em-reais-35-90]]). Se o dono quiser levar alguma à demo: ensinar `b3/esteira_live.py` o tipo `["brl", valor]` (hoje só lê saídas em V), checar paridade com a pesquisa e só então ligar.
1. Depois de um pregão com os robôs ligados: comparar cada robô com a pesquisa (acerto, resultado por trade, motivos de saída) e registrar em [[Demo-diario]]. Ver [[Robos-demo]].
2. Revisar `ops/state/exit_menu/picks.jsonl`: aplicar a regra "candidata **e** p90 > 0", checar paridade e só então propor robô.
3. Mover relatórios novos de `ops/state/exit_menu/` para `research/b3/exit_menu/` e commitar (só com a esteira parada e a trava livre).
4. Commitar `live/core/engine.py` e `live/run.py` (hoje misturam MOVE_STOP e controles do portal) quando o dono aprovar.
5. Retomar a esteira só se o dono pedir (apagar `ops/state/STOP_ESTEIRA`).

## Dívidas conhecidas

- Falha preexistente em `tests/archive` (h019), sem relação com a linha B3.
- A E-166 passou no menu de saídas mas usa barras do dólar; o robô de índice não as recebe. Ficou de fora.
- `docs/funcionamento-geral.md` descreve a linha cripto de 2026-11-08 e está desatualizado. Ver [[Cripto-Freqtrade]].
