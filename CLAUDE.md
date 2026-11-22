# CLAUDE.md — leia isto primeiro

Este repositório é um laboratório de trading quantitativo (Quant Trading Lab). A linha principal hoje é **mini índice (WIN) e mini dólar (WDO) da B3**, com dados e robôs na **conta demo** da Clear (MetaTrader 5).

**O mapa completo está no cofre de notas `docs/cerebro/`** (Markdown, abre no Obsidian). Comece por:

1. [docs/cerebro/00-LEIA-PRIMEIRO.md](docs/cerebro/00-LEIA-PRIMEIRO.md): o que é o projeto e em que ordem ler.
2. [docs/cerebro/Regras-inviolaveis.md](docs/cerebro/Regras-inviolaveis.md): o que você nunca faz.
3. [docs/cerebro/Estado-atual.md](docs/cerebro/Estado-atual.md): onde o trabalho está parado hoje.
4. [docs/cerebro/Como-rodar-em-outro-ambiente.md](docs/cerebro/Como-rodar-em-outro-ambiente.md): montar o ambiente a partir de um clone.

## Regras que valem sempre (resumo)

- **Nunca dinheiro real.** Todos os robôs são demo ou dry-run. Operar na conta real é decisão exclusiva do dono, por escrito.
- **Nunca escreva senha, chave ou número de conta** em arquivo, log, commit ou nota. Credenciais ficam em `.env` ignorado pelo git, digitadas pelo dono.
- **Validação só se lê uma vez; o teste final está trancado** e só o dono destranca. Toda variante testada conta como tentativa (penalidade por múltiplos testes).
- **Demo não é evidência.** Robô rodando na demo serve para observar, nunca para aprovar uma regra.
- **Agentes de IA escrevem texto e código; quem decide são os portões em código** (`lab/gates.py`, `b3/config/gates_b3.json`).
- **Não edite arquivos rastreados enquanto um ciclo da esteira ou do pipeline roda**: o guard acusa mudança de caminhos e derruba o ciclo. Pause com `ops/state/STOP_ESTEIRA` (ou `STOP_PROXY_CYCLES`) e espere a trava sair.
- **Mais de uma sessão do Claude pode trabalhar aqui ao mesmo tempo.** Confira processos, use um worktree e faça commit só dos seus caminhos.
- **Ordem manual em robô passa pelo arquivo de comando** (`live/commands/<robô>.json`), nunca direto na corretora.
- Pergunte antes de: gastar com agentes além do teto diário, apagar dados, mudar gates/splits, parar processo de outra sessão, fazer `git push`.

## Comandos úteis

```bash
python -m pytest tests/b3 tests/live          # testes da linha B3 e do motor ao vivo (rode da raiz)
python -m b3.esteira status                    # esteira de famílias
python -m b3.esteira_cycle status              # ciclo horário (gasto do dia, pausa)
python -m b3.exit_menu run --family E-001      # menu de saídas S1..S4 numa família
python -m lab.dashboard serve --open           # portal em 127.0.0.1:8765 (somente leitura)
```

Os dados de mercado, os bancos (`research/lab.sqlite`, `live/journal*.sqlite`) e o estado de execução **não vão para o git**. Veja o cofre para saber como reconstruí-los.
