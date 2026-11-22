---
tipo: regras
atualizado: 2026-11-19
tags: [cerebro, seguranca, regras]
---

# Regras invioláveis

Valem para qualquer sessão do Claude, em qualquer máquina. Quem pode mudar: **só o dono, por escrito**.

## Dinheiro e contas

1. **Nenhum dinheiro real.** Robôs rodam em demo (Clear) ou dry-run. `allow_real` fica `false`. A seção "ao vivo" do [[Portal]] é interface; nenhum robô opera na conta real.
2. **Conta demo apenas.** Anexe ao terminal Clear demo **sem credenciais**: `b3/config/broker_mt5.json` + terminal já logado pelo dono. Nunca use servidor com `PRD` ou `REAL` para robô demo. Nunca use o `live/.env` antigo (conta de outra corretora).
3. **Não leia `live/.env.real`.** Só a linha `MT5_PATH` foi tocada até hoje.
4. **Credenciais**: nunca em repositório, log, commit, nota ou chat. O dono digita no `.env` ignorado pelo git.
5. **Sem ordens em sondas.** Consultas ao MT5 para diagnóstico são só de leitura.
6. **Fechar posição só a pedido do dono**, e pelo arquivo de comando do robô (`live/commands/<robô>.json`, lido por `live/core/control.py`). Fechar direto na corretora quebra a reconciliação (aconteceu com a P-017) e o robô entra em `safe_mode`.
7. As duas contas (real e demo) são **hedging** (`margin_mode == 2`). Ao checar, imprima o número bruto. Não volte a falar em netting. Ver [[2026-11-17-conta-hedging]].

## Pesquisa e evidência

8. **Validação lê-se uma vez por regra e mercado.** O **teste final está trancado**; só o dono destranca.
9. **Toda variante testada é uma tentativa** e entra na contagem do DSR. Mudou um número depois de ver o resultado: é hipótese nova com ID novo.
10. **Demo não é evidência.** Servir de observação, nunca de aprovação.
11. **Agentes escrevem texto e código, não decidem.** Aprovar ou rejeitar é código determinístico (`lab/gates.py`, `b3/config/gates_b3.json`). Agentes não afrouxam gates.
12. **Feriados da B3 de um ano só entram a partir do Ofício Circular oficial**, nunca de memória. O calendário de 2027 ainda não existe no repositório.
13. Janela de tempo de ticks do MT5: veja [[2026-11-16-relogio-tick-mt5]] antes de escrever código com ticks.

## Trabalho no repositório

14. **Não edite arquivo rastreado durante um ciclo da esteira** (`TradeInitial-EsteiraCycle`) ou do pipeline de proxies: o guard compara os caminhos alterados antes e depois e derruba o ciclo. Pause criando `ops/state/STOP_ESTEIRA` e espere a trava `%TEMP%\trade-initial-esteira-cycle.lock` sumir.
15. **Rode a suíte completa** (`pytest tests/b3 tests/live`) e confira o código de saída, sem `| tail`, antes de liberar um ciclo.
16. **Várias sessões trabalham aqui.** Liste processos `lab.pipeline|b3.esteira|live.run` antes de mexer. Use worktree. Pergunte ao dono antes de parar processo de outra sessão. Nunca rode a mesma fila duas vezes. Veja [[Operacao-Windows]].
17. **Commit só dos seus caminhos** (`lab/gitops.py` já faz isso). Nunca commite `.env`, bancos ou estado de execução.
18. **Dados pessoais do dono não entram** em nota, commit ou serviço externo.
19. Configurações do sistema (plano de energia, tarefas agendadas) são do dono: o Claude entrega o script `.ps1`, o dono roda.
20. Usar `ScheduleWakeup`/loops nunca deve gastar além do teto diário de agente (hoje **US$ 50** por dia de São Paulo, em `b3/config/esteira_b3.json`).
