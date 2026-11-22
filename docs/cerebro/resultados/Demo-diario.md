---
tipo: resultados
atualizado: 2026-11-20
tags: [cerebro, demo, diario]
---

# Demo: resumo por dia

Um bloco por pregão, do mais novo para o mais antigo. Fonte: os diários dos robôs (`live/journal.<robô>.sqlite`, tabela `events`, `kind='fill'`; a saída tem `pnl`). **O diário não desconta custo.** Para comparar com a pesquisa, desconte o custo medido do WIN: **R$ 1,30 por trade** (R$ 0,50 de taxas + 0,8 tick de slippage; ver [[2026-11-20-saidas-em-reais-35-90]]). A demo é observação, não evidência ([[Regras-inviolaveis]]).

## 2026-11-20 (sexta)

**Nenhum robô operou.** O terminal da Clear perdeu a autorização às 06:05 e o PC reiniciou às 08:46, encerrando os processos. Os 12 robôs novos (P-032 e os 11 da esteira) não têm tarefa agendada. Ver [[Estado-atual]].

## 2026-11-19 (quinta)

44 trades fechados, 25 positivos (57%), **bruto +R$ 237**, líquido estimado **≈ +R$ 180** (R$ 1,30 × 44). Nenhuma posição aberta no fim do dia. 12 dos 24 robôs não operaram.

| Robô | Trades | Acertos | Bruto (R$) |
|---|---|---|---|
| P-030 | 4 | 4 | +255 |
| P-020 | 6 | 4 | +168 |
| P-032 | 1 | 1 | +112 |
| E-160 | 2 | 2 | +101 |
| E-040 | 2 | 2 | +80 |
| P-026 WIN | 4 | 2 | −6 |
| P-004 WIN | 1 | 0 | −4 |
| E-102 | 2 | 1 | −65 |
| P-017 | 6 | 2 | −68 |
| P-028 | 4 | 2 | −92 |
| P-023 | 2 | 0 | −88 |
| E-225 | 10 | 5 | −156 |

Sem operações: P-014, P-024, P-025, P-029, P-026 WDO, E-062, E-118, E-156, E-164, E-193, E-209, E-217.

Leitura: dos 11 robôs da esteira, 4 operaram (16 trades). A única amostra relevante é a E-225: 10 trades, 50% de acerto contra 65,7% na pesquisa. Um dia não diz nada sobre isso. Esperado pela pesquisa por robô: [[Robos-demo]].

## Como atualizar este arquivo

```bash
# por robô: trades fechados de um dia (ts em UTC; o pregão de 19/11 vai de ~12:00 a ~21:30 UTC)
python - <<'EOF'
import sqlite3, json
c = sqlite3.connect("file:live/journal.demo-b3-p032-win.sqlite?mode=ro", uri=True)
for ts, pl in c.execute("select ts, payload from events where kind='fill' and ts like '2026-11-19%'"):
    p = json.loads(pl)
    if p.get("pnl") is not None:
        print(ts, p["pnl"], p["reason"])
EOF
```
