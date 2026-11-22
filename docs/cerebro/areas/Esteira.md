---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, esteira, agentes]
---

# Esteira (conveyor)

Linha de montagem de famílias de regras simples para WIN/WDO. Aprovada pelo dono em 2026-11-17 ([[2026-11-17-esteira-aprovada]]). Ideia: o backtest é um **filtro**, a demo é o teste; gerar muitas regras simples rápido.

## Fluxo

1. **Agente `esteira-research`** escreve um **lote** de 5–10 famílias num arquivo `b3/families/bNNN_agent.py` (`FAMILIES = [Family(...)]`, até 3 parâmetros, grade pequena).
2. **Checagens** antes de qualquer leitura: look-ahead e janela de 21 sessões (garante que a regra ao vivo reconstrói o mesmo sinal).
3. O lote é **commitado antes de ler resultado** (pré-registro). Cada ID de família é filtrado **uma vez**; ideia mudada = ID novo.
4. **Filtro** (`b3/esteira.py screen`) só na exploração, com custo medido: trades/ano mínimos, líquido médio > 0, ≥5 de 8 fatias de tempo positivas, plateau (≥2/3 dos vizinhos positivos), melhor por família, sobreposição ≤ 0,5 com as já selecionadas. Limiares exatos em `b3/config/esteira_b3.json`. DSR/PBO só são relatados.
5. **Menu de saídas** roda sobre as famílias do lote ([[Menu-de-saidas]]).
6. Os candidatos vão para a **demo** (manual, revisão do Claude): [[Robos-demo]].

## Ciclo horário

- Tarefa Windows `TradeInitial-EsteiraCycle`, a cada hora: `ops/windows/esteira-cycle.cmd` → `python -m b3.esteira_cycle cycle --max 200 --minutes 50`. Lotes seguidos; não abre lote novo após 50 min.
- **Trava**: `%TEMP%\trade-initial-esteira-cycle.lock`. **Pausa**: `ops/state/STOP_ESTEIRA`. Auto-pausa após 2 erros seguidos.
- **Limite de uso do Claude** ("5-hour limit") **pula a hora** sem contar como erro (corrigido em 2026-11-18, quando a esteira ficou parada a tarde toda).
- **Teto de agente**: US$ 50 por dia de São Paulo (`max_agent_cost_usd_per_day`).
- **Guard**: o ciclo compara os caminhos alterados no git antes e depois do agente. Editar arquivo rastreado durante o ciclo o derruba. Ver [[Regras-inviolaveis]].

## Registros

| Arquivo | Conteúdo |
|---|---|
| `research/b3/esteira/families.jsonl` | Uma linha por família filtrada |
| `research/b3/esteira/ledger.jsonl` | Variantes lidas (contagem de tentativas) |
| `research/b3/esteira/cycle_log.jsonl` | Eventos do ciclo (`agent`, `registered`, `screen`, `batch_done`, `exit_menu`, `usage_limit`) |

## Estado

E-001..E-387 geradas; pausada em 2026-11-19. Ver [[Estado-atual]].

## Lições

- Lote 1 (E-001..E-008): nenhuma passou. Saída padrão em R$ (alvo/stop 30) é injusta com WDO (30 reais = 6 ticks): por isso as saídas por V.
- Um erro de sintaxe num `fh.write(...)` quebrou o passo do menu de saídas em dois lotes; teste `tests/b3/test_exit_menu.py` agora cobre a importação.
