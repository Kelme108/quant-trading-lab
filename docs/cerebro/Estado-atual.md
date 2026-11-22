---
tipo: estado
atualizado: 2026-11-22
tags: [cerebro, estado]
---

# Estado atual (2026-11-22)

> Foto de um momento. Antes de agir, confira nos arquivos (`python -m b3.esteira_cycle status`, `ops/state/`, ledgers, diários dos robôs) ou na seção **Esteira** do portal.

## Em uma frase

A **esteira roda em backtest** (exploração, teto de US$ 15 por noite, agente no Sonnet); **os 25 robôs da demo estão parados** (mercado fechado); o portão das regras P foi trocado por custo medido + barra estatística; nenhuma regra tem evidência para dinheiro real.

## Atualização 2026-11-22

- **Portal:** nova seção **Esteira** (ciclos, gasto da noite, triagem, melhores saídas, portão). Ver [[Portal]].
- **Robôs da demo na exploração:** tabela refeita para os 25 robôs em [[Robos-demo]]. Nenhum dos 11 da esteira chega perto do t mínimo (maior 2,39 contra ~4,6). Entre as regras P só a P-004 em WIN passa (t 5,96), e a validação dela já foi lida.
- **Noite 21→22:** 29 chamadas de agente, 283 famílias (até a E-727), US$ 12,07 de US$ 15. A esteira parou às 01:52 porque o ciclo reserva US$ 3 por chamada e cada lote custa US$ 0,2 a 0,3 no Sonnet; sobraram ~US$ 2,90. Proposta aberta: baixar a reserva para ~US$ 1 ([[Pendencias-e-calendario]]).
- **Candidatas por t:** E-410 com B1 (t 4,48), E-303 com S2 (3,38), E-286 com B5 (3,29). Nenhuma passa; **validação continua sem leitura** e só se lê com o aval do dono.
- **Preparo para o Git:** [[Publicar-no-GitHub]].

## Atualização 2026-11-21

- **Esteira retomada** em backtest (exploração), também com o mercado fechado; cada lote roda o menu por V e o menu em reais. Teto passou de US$ 50 por dia para **US$ 15 por noite** (a noite começa às 21h).
- **Auditoria backtest × demo:** o simulador reproduz a demo; o "nenhuma passa" vem do portão das regras P; o bom resultado da demo veio de fechamentos manuais. Ver [[2026-11-21-auditoria-backtest-demo]].
- **Portão trocado** (aprovado pelo dono): custo base = custo medido (p90 como conservador) e t mínimo no lugar da barra linear.

## Robôs na demo

- **0 de 25 rodando** (14 regras P e 11 da esteira). Causa em 2026-11-20: o terminal da Clear perdeu a autorização às 06:05 e o PC reiniciou às 08:46, matando os processos. Em 2026-11-21 o dono decidiu deixá-los parados com o mercado fechado.
- Para religar: o dono abre o terminal Clear e entra na conta **demo**; depois sobem os robôs com `ops\windows\demo-b3.cmd <nome>` ([[Robos-demo]]). Sem credenciais. **E-164 não deve ser religado** (falta a barra do dólar).
- Tarefas das 08:40 existem para os robôs antigos; **os 12 novos (P-032 e os 11 da esteira) ainda não têm** (o dono precisa rodar `ops/windows/install-demo-p032-task.ps1`). Ver [[Pendencias-e-calendario]].
- Último pregão com operação: 2026-11-19, 44 trades, bruto +R$ 237. Detalhe em [[Demo-diario]].

## Esteira e menu de saídas

- Famílias **E-001 a E-727** geradas e filtradas na exploração (10.596 versões triadas, ~104 mil leituras contando os menus). Ver [[Esteira]].
- **Rodando** (a pausa de 2026-11-19 foi encerrada em 2026-11-21). Pausar: criar `ops/state/STOP_ESTEIRA`.
- Teto de agente: **US$ 15 por noite** (dia de orçamento de São Paulo começa às 21h).
- [[Menu-de-saidas]] por V rodado em três levas: ~20 mil versões lidas, 314 candidatas. **19 candidatas da noite de 18→19 não foram ligadas** (melhor: E-377, saída S3); lista em `ops/state/exit_menu/picks.jsonl`.
- **Rodada concluída (2026-11-20):** saídas em reais B1–B5 (alvo R$ 35 / stop R$ 90 e vizinhos) sobre 76 famílias, só WIN: 6.160 versões, 887 candidatas, 29 famílias com lucro também no custo pessimista (melhor: E-286, +R$ 4,48 por trade). Relatório em `research/b3/exit_brl/`. **Nenhuma ligada na demo.** Detalhes: [[2026-11-20-saidas-em-reais-35-90]].

## Evidência

- P-004 foi a única regra que passou na exploração de WIN e **reprovou na validação**. Ver [[Resultados-B3]].
- A validação do restante está **intocada**. O teste final está **trancado**.
- Busca de padrões (A, B, C), estudo de saídas e P-026 lab: nenhum aprovado como edge.

## Adiado

- **MES e MNQ** (micro S&P 500 e micro Nasdaq-100) como nova seção: adiado pelo dono em 2026-11-20. Análise em [[2026-11-20-mes-mnq-adiado]].

## Código em andamento

- Branch `main`. `live/core/engine.py`, `live/run.py`, `lab/dashboard.py` (parte dos controles), `lab/demo_b3.py` e `live/core/control.py` têm mudanças não commitadas da frente **controles ao vivo / conta real** (branch `feat/portal-controls`), com as configs `live/config/live-b3-*.json`. Fica fora do que se publica até o dono decidir ([[Publicar-no-GitHub]]).
- Preparo para clone (`bootstrap.py`, `requirements*.txt`, `CONTRIBUTING.md`, `.github/`, este cofre) já está commitado. O que falta e as decisões do dono: [[Publicar-no-GitHub]] e [[Onboarding-equipe]].

## Linhas

| Linha | Estado |
|---|---|
| B3 WIN/WDO | Principal, ativa ([[B3-WIN-WDO]]) |
| Proxies (CFDs de índice) | Encerrada em 2026-11-16 |
| Cripto (Freqtrade) | Pausada ([[Cripto-Freqtrade]]) |
| Tick/fluxo de ordens | Gravador de ticks; programa de ticks aprovado, leitura só após 2026-12-31 |
