---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, saidas, stop, alvo]
---

# Menu de saídas (S1–S4)

Mesmas **entradas** das famílias da [[Esteira]], com quatro saídas em unidades de **V** (volatilidade do horário). Decisão: [[2026-11-18-p026-menu-de-saidas]]. Config pré-registrada: `b3/config/exit_menu.json`. Código: `b3/exit_menu.py`, `b3/p026_lab.py`.

## As saídas

**V** = média do retorno absoluto de 30 minutos no mesmo minuto do dia, nas 20 sessões anteriores. Distâncias arredondadas para cima ao tick.

| Saída | Stop | Alvo | Outros | Hold máx. |
|---|---|---|---|---|
| S1 | 1V | 1V | | 60 min |
| S2 | 1,5V | 0,75V | | 60 min |
| S3 | 1V | 2V | | 60 min |
| S4 | 1V | nenhum | breakeven e trailing de 1V | 60 min |

## Seleção (exploração, custo medido)

≥ 250 trades/ano · líquido médio > 0 · ≥ 5 de 8 fatias positivas · plateau ≥ 2/3 entre vizinhos de parâmetro **e de saída** · bate o **controle aleatório** (3 sementes, só calculado para quem passou o resto).

**Regra de implantação na demo** (do Claude, não do dono): candidata **e** líquido médio > 0 no cenário p90.

## Como rodar

```bash
python -m b3.exit_menu run [--family E-001 ...] [--market WIN]
```

Trabalha em `ops/state/exit_menu/` (ignorado pelo git, para não acionar o guard). Relatórios vão depois para `research/b3/exit_menu/`. Depois de cada lote, o ciclo da esteira chama o menu sozinho.

## Execução ao vivo

- `b3/esteira_live.py` monta a regra da família + saída para o motor. Stop e alvo vão **para o servidor** junto com a entrada (`Signal.take_profit` → `OrderRequest.take_profit` → MT5 `tp`).
- S4 usa `MOVE_STOP` a cada fechamento de barra (só aperta). Recusa do broker ou preço já além do nível → saída a mercado.
- Paridade verificada: os sinais e V no ao vivo coincidem com a pesquisa. Ver [[Engine-live]].

## Resultados e o aviso de múltiplos testes

Três levas: 140 famílias (7.752 versões, 13 candidatas), 60 famílias (3.792, 14), 140 famílias na noite de 18→19 (8.672, 287). **Quase 20 mil versões lidas**: parte das candidatas é sorte. A demo é que separa. Ver [[Robos-demo]] e [[Resultados-B3]].

Taxa de acerto por saída (pesquisa): S2 65–68%, S1 53–54%, S3 39–44%, S4 ~39%. Lucro por trade não acompanha a taxa de acerto.
