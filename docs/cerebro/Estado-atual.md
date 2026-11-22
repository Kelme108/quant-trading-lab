---
tipo: estado
atualizado: 2026-11-20
tags: [cerebro, estado]
---

# Estado atual (2026-11-20, tarde)

> Foto de um momento. Antes de agir, confira nos arquivos (`python -m b3.esteira_cycle status`, `ops/state/`, ledgers, diários dos robôs).

## Em uma frase

Pesquisa de famílias **pausada** (pedido do dono); **os 24 robôs da demo estão parados** desde o reinício do PC às 08:46; um teste de saídas em reais (alvo R$ 35, stop R$ 90) roda sobre as candidatas existentes; nenhuma regra tem evidência para dinheiro real.

## Atualização 2026-11-21

- **Esteira retomada** em backtest (exploração), também com o mercado fechado; cada lote roda o menu por V e o menu em reais. Teto US$ 50 por dia.
- **Auditoria backtest × demo:** o simulador reproduz a demo; o "nenhuma passa" vem do portão das regras P; o bom resultado da demo veio de fechamentos manuais. Ver [[2026-11-21-auditoria-backtest-demo]].

## Robôs na demo

- **0 de 24 rodando** em 2026-11-20. Causa: o terminal da Clear perdeu a autorização às 06:05 e o PC reiniciou às 08:46, matando os processos. O terminal está fechado.
- Para religar: o dono abre o terminal Clear e entra na conta **demo**; depois sobem os robôs com `ops\windows\demo-b3.cmd <nome>` ([[Robos-demo]]). Sem credenciais.
- Tarefas das 08:40 existem para os robôs antigos; **os 12 novos (P-032 e os 11 da esteira) ainda não têm** (o dono precisa rodar `ops/windows/install-demo-p032-task.ps1`). Ver [[Pendencias-e-calendario]].
- Último pregão com operação: 2026-11-19, 44 trades, bruto +R$ 237. Detalhe em [[Demo-diario]].

## Esteira e menu de saídas

- Famílias **E-001 a E-387** geradas e filtradas na exploração. Ver [[Esteira]].
- **Pausada** desde 2026-11-19 07:37 (`ops/state/STOP_ESTEIRA`). Para retomar: apagar o arquivo.
- Teto de agente: **US$ 50 por dia de São Paulo**.
- [[Menu-de-saidas]] por V rodado em três levas: ~20 mil versões lidas, 314 candidatas. **19 candidatas da noite de 18→19 não foram ligadas** (melhor: E-377, saída S3); lista em `ops/state/exit_menu/picks.jsonl`.
- **Rodada concluída (2026-11-20):** saídas em reais B1–B5 (alvo R$ 35 / stop R$ 90 e vizinhos) sobre 76 famílias, só WIN: 6.160 versões, 887 candidatas, 29 famílias com lucro também no custo pessimista (melhor: E-286, +R$ 4,48 por trade). Relatório em `research/b3/exit_brl/`. **Nenhuma ligada na demo.** Detalhes: [[2026-11-20-saidas-em-reais-35-90]].

## Evidência

- P-004 foi a única regra que passou na exploração de WIN e **reprovou na validação**. Ver [[Resultados-B3]].
- A validação do restante está **intocada**. O teste final está **trancado**.
- Busca de padrões (A, B, C), estudo de saídas e P-026 lab: nenhum aprovado como edge.

## Adiado

- **MES e MNQ** (micro S&P 500 e micro Nasdaq-100) como nova seção: adiado pelo dono em 2026-11-20. Análise em [[2026-11-20-mes-mnq-adiado]].

## Código em andamento

- Branch `main`. `live/core/engine.py` e `live/run.py` têm mudanças não commitadas que misturam o **MOVE_STOP** e a **seção ao vivo do portal** (branch `feat/portal-controls`).
- Muitos arquivos novos ainda não rastreados: configs `live/config/demo-b3-*.json`, `docs/plano-b3-win-wdo.md`, `docs/runbook-ao-vivo.md`, `live/core/control.py`, `ops/vps/`, e o preparo para clone (`bootstrap.py`, `requirements*.txt`, `CONTRIBUTING.md`, `.github/`, `docs/cerebro/`).
- Preparo para clone: ver [[Onboarding-equipe]].

## Linhas

| Linha | Estado |
|---|---|
| B3 WIN/WDO | Principal, ativa ([[B3-WIN-WDO]]) |
| Proxies (CFDs de índice) | Encerrada em 2026-11-16 |
| Cripto (Freqtrade) | Pausada ([[Cripto-Freqtrade]]) |
| Tick/fluxo de ordens | Gravador de ticks; programa de ticks aprovado, leitura só após 2026-12-31 |
