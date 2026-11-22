---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, operacao, windows, tarefas]
---

# Operação no Windows

O ambiente de produção do dono é um Windows 11 com o terminal Clear aberto. Tudo que "roda sozinho" são **tarefas agendadas** do Windows. **O Claude não cria nem altera tarefas agendadas nem configurações de energia**: ele entrega o script `.ps1` e o dono roda.

## Tarefas

| Tarefa | O que faz | Origem |
|---|---|---|
| `TradeInitial-DemoB3-<ROBÔ>` | Liga o robô às 08:40 em dias úteis (ignora segunda partida) | `ops/windows/demo-b3.cmd`, instaladores `install-demo-p030-task.ps1`, `install-demo-p032-task.ps1` |
| `TradeInitial-EsteiraCycle` | Ciclo da esteira, de hora em hora | `ops/windows/esteira-cycle.cmd`, `install-esteira-task.ps1` |
| `TradeInitial-ProxyCycle` | Ciclo do pipeline de regras de agente (confirme com `Get-ScheduledTask`; pode estar desativada) | `ops/windows/proxy-cycle.cmd` |
| `TradeInitial-TickRecorder` | Grava ticks, dias úteis 19:05 | `ops/windows/tick-recorder.cmd` |

Os `.cmd` descobrem a raiz do repositório e o Python sozinhos (`ops/windows/_env.cmd`: `.venv` da raiz → `C:\Python314` → `python` do PATH).

## Parar e pausar

| Alvo | Como |
|---|---|
| Um robô (zera e para) | Criar `live/STOP` (kill switch global dos robôs) ou usar o arquivo de comando |
| Esteira | Criar `ops/state/STOP_ESTEIRA` e esperar a trava `%TEMP%\trade-initial-esteira-cycle.lock` sair |
| Pipeline de agentes B3 | Criar `ops/state/STOP_PROXY_CYCLES` |
| Loop cripto | `STOP_CYCLES` |

## Sessões do Claude em paralelo

Várias sessões trabalham no mesmo diretório. Em 2026-11-13 uma delas deixou uma cadeia de shell que religa a próxima etapa quando uma é morta.

- Antes de editar: liste processos que casem `lab.pipeline|research-loop|b3.esteira|live.run` (filtre por nome para não casar o seu comando).
- Use um **worktree** enquanto um ciclo roda.
- Peça ao dono antes de parar o processo de outra sessão; mate a cadeia inteira (inclusive o shell pai) e refaça a mesma fila você mesmo.
- Nunca rode duas vezes a mesma fila: seria um segundo sorteio no registro.

## Máquina ligada

- O PC dorme em 20 min na tomada (plano do dono). Uma tarefa `TradeInitial-KeepAwake` existiu temporariamente. **Não reinicie o PC com robôs ligados.**
- Para o laboratório fora do PC: [../../migracao-linux.md](../../migracao-linux.md) e `ops/vps/bootstrap-ubuntu.sh` (não validados para a linha B3).

## Terminal MT5

Um terminal segura uma conta por vez. Logar o terminal demo em outra conta derruba os robôs (guarda do motor). Terminal demo: `C:\Program Files\Clear Investimentos MT5 Terminal`. Detalhes de conta: [[2026-11-17-conta-hedging]].
