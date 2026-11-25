---
tipo: resultados
atualizado: 2026-11-25
tags: [cerebro, demo, diario]
---

# Demo: resumo por dia

Um bloco por pregão, do mais novo para o mais antigo. Fonte: os diários dos robôs (`live/journal.<robô>.sqlite`, tabela `events`, `kind='fill'`; a saída tem `pnl`). **O diário não desconta custo.** Para comparar com a pesquisa, desconte o custo medido do WIN: **R$ 1,30 por trade** (R$ 0,50 de taxas + 0,8 tick de slippage; ver [[2026-11-20-saidas-em-reais-35-90]]). A demo é observação, não evidência ([[Regras-inviolaveis]]).

Custo do WDO: **R$ 6,00 por trade** (2 × R$ 1,00 de taxas + 2 × 0,4 tick × R$ 5,00; `b3/config/pattern_search_b3.json`, `wdo_extension.costs.measured`). Histórico completo exportado em `live/export-2026-11-25/` (resumo por dia e robô, fills individuais).

## 2026-11-24 (terça)

177 trades fechados, 106 positivos (60%), **bruto −R$ 2.493**, líquido estimado **≈ −R$ 3.174** (R$ 1,30 × 81 no WIN + R$ 6,00 × 96 no WDO). WIN: 81 trades, bruto −R$ 588; WDO: 96 trades, bruto −R$ 1.905. 41 dos 63 robôs com diário no dia operaram. **O diário para às 16:07** (último evento de todos os robôs; o pregão fecha às 18:25). A E-272-B2 WIN abriu uma posição às 16:07:09 e o diário não tem a saída: a posição pode ter ficado aberta. Os seis robôs do lote B1 (E-164, E-166, E-656) não têm nenhum evento em 24/11.

| Robô | Trades | Acertos | Bruto (R$) |
|---|---|---|---|
| P-030 WIN | 3 | 3 | +157 |
| E-193 WDO | 5 | 4 | +140 |
| E-331-B2 WIN | 10 | 8 | +93 |
| E-499-B5 WDO | 2 | 2 | +85 |
| P-025 WIN | 1 | 1 | +84 |
| E-587-B5 WIN | 6 | 5 | +78 |
| E-385-B1 WIN | 10 | 8 | +72 |
| E-499-B5 WIN | 2 | 2 | +71 |
| E-445-B5 WDO | 1 | 1 | +50 |
| P-026 WIN | 2 | 2 | +44 |
| E-225-B2 WIN | 3 | 2 | +36 |
| P-028 WIN | 1 | 1 | +35 |
| E-395-S2 WIN | 3 | 2 | +28 |
| E-193 WIN | 2 | 1 | −8 |
| E-331-B2 WDO | 10 | 8 | −10 |
| E-436-B2 WIN | 2 | 1 | −11 |
| E-395-B2 WDO | 3 | 2 | −20 |
| E-395-B2 WIN | 3 | 2 | −24 |
| P-023 WIN | 3 | 1 | −28 |
| E-178-B2 WDO | 4 | 3 | −40 |
| E-436-B2 WDO | 2 | 1 | −50 |
| E-272-B2 WDO | 7 | 5 | −60 |
| E-385-B1 WDO | 10 | 7 | −65 |
| E-453-B5 WDO | 10 | 7 | −65 |
| E-335-B2 WIN | 5 | 3 | −83 |
| E-118-B3 WIN | 1 | 0 | −96 |
| E-490-B5 WDO | 1 | 0 | −100 |
| E-490-B5 WIN | 1 | 0 | −108 |
| E-587-B5 WDO | 7 | 4 | −110 |
| E-178-B2 WIN | 4 | 2 | −114 |
| E-118 WIN | 1 | 0 | −149 |
| P-020 WIN | 3 | 1 | −150 |
| E-445-B5 WIN | 3 | 1 | −153 |
| E-272-B2 WIN | 7 | 4 | −167 |
| P-017 WIN | 5 | 0 | −195 |
| E-335-B2 WDO | 5 | 2 | −205 |
| E-118-B3 WDO | 4 | 1 | −235 |
| E-410-B1 WDO | 10 | 4 | −250 |
| E-350-B1 WDO | 10 | 4 | −305 |
| E-118 WDO | 3 | 1 | −310 |
| E-395-S2 WDO | 2 | 0 | −355 |

Sem operações: E-156-B5 WDO, E-156-B5 WIN, E-225-B2 WDO, E-225 WDO, E-225 WIN, E-286-B5 WDO, E-286-B5 WIN, E-332-B5 WDO, E-332-B5 WIN, E-350-B1 WIN, E-362-B5 WDO, E-362-B5 WIN, E-410-B1 WIN, E-418-B5 WDO, E-418-B5 WIN, E-453-B5 WIN, P-004 WDO, P-004 WIN, P-014 WIN, P-024 WIN, P-026 WDO, P-029 WIN.

## 2026-11-23 (segunda)

283 trades fechados, 226 positivos (80%), **bruto +R$ 4.155**, líquido estimado **≈ +R$ 3.186** (R$ 1,30 × 155 no WIN + R$ 6,00 × 128 no WDO). WIN: 155 trades, bruto +R$ 2.225; WDO: 128 trades, bruto +R$ 1.930. 50 dos 69 robôs com diário no dia operaram. Os seis robôs do lote B1 E-164, E-166 e E-656 (WIN e WDO) não têm evento depois de 09:26 e não operaram.

| Robô | Trades | Acertos | Bruto (R$) |
|---|---|---|---|
| E-286-B5 WDO | 10 | 10 | +355 |
| E-350-B1 WDO | 10 | 10 | +335 |
| E-225 WDO | 7 | 6 | +270 |
| E-385-B1 WIN | 10 | 9 | +261 |
| E-331-B2 WIN | 7 | 7 | +226 |
| E-286-B5 WIN | 10 | 9 | +207 |
| P-020 WIN | 4 | 4 | +207 |
| E-156-B5 WDO | 10 | 8 | +195 |
| E-490-B5 WIN | 9 | 8 | +191 |
| E-193 WIN | 3 | 3 | +181 |
| E-350-B1 WIN | 10 | 9 | +177 |
| E-395-S2 WIN | 3 | 3 | +172 |
| E-445-B5 WIN | 5 | 5 | +165 |
| E-193 WDO | 6 | 5 | +160 |
| E-395-B2 WIN | 5 | 5 | +154 |
| E-587-B5 WDO | 5 | 5 | +140 |
| E-445-B5 WDO | 7 | 6 | +135 |
| E-118 WDO | 6 | 5 | +120 |
| E-178-B2 WIN | 4 | 4 | +111 |
| E-385-B1 WDO | 10 | 8 | +100 |
| E-395-S2 WDO | 1 | 1 | +100 |
| E-453-B5 WIN | 10 | 8 | +96 |
| E-587-B5 WIN | 7 | 6 | +86 |
| E-335-B2 WIN | 4 | 3 | +83 |
| E-225-B2 WIN | 10 | 8 | +80 |
| E-499-B5 WDO | 2 | 2 | +80 |
| E-499-B5 WIN | 2 | 2 | +75 |
| P-026 WIN | 1 | 1 | +66 |
| E-395-B2 WDO | 2 | 2 | +65 |
| E-331-B2 WDO | 2 | 2 | +60 |
| E-436-B2 WDO | 2 | 2 | +45 |
| E-362-B5 WIN | 5 | 4 | +44 |
| E-225 WIN | 9 | 5 | +39 |
| E-225-B2 WDO | 9 | 7 | +15 |
| E-272-B2 WDO | 10 | 7 | +15 |
| E-272-B2 WIN | 9 | 6 | +13 |
| E-118 WIN | 3 | 2 | +3 |
| E-118-B3 WIN | 3 | 2 | +2 |
| P-004 WDO | 1 | 0 | −15 |
| P-004 WIN | 1 | 0 | −19 |
| P-030 WIN | 4 | 2 | −34 |
| E-178-B2 WDO | 4 | 3 | −35 |
| E-362-B5 WDO | 2 | 1 | −40 |
| P-028 WIN | 3 | 1 | −49 |
| E-490-B5 WDO | 8 | 6 | −50 |
| E-118-B3 WDO | 6 | 4 | −55 |
| P-025 WIN | 3 | 2 | −59 |
| E-335-B2 WDO | 8 | 5 | −65 |
| P-023 WIN | 4 | 1 | −68 |
| P-017 WIN | 7 | 2 | −185 |

Sem operações: E-156-B5 WIN, E-164-B1 WDO, E-164-B1 WIN, E-166-B1 WDO, E-166-B1 WIN, E-332-B5 WDO, E-332-B5 WIN, E-410-B1 WDO, E-410-B1 WIN, E-418-B5 WDO, E-418-B5 WIN, E-436-B2 WIN, E-453-B5 WDO, E-656-B1 WDO, E-656-B1 WIN, P-014 WIN, P-024 WIN, P-026 WDO, P-029 WIN.

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
