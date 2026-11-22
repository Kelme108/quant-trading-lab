---
tipo: decisao
data: 2026-11-16
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# WIN/WDO pela conta demo da Clear: linha principal

**Data:** 2026-11-12 (decisão) e 2026-11-16 (aprovação)

O dono decidiu em 2026-11-12 trazer WIN/WDO ao laboratório e aprovou em 2026-11-16 o [plano de reuso](../../plano-b3-reuso.md) com todas as recomendações (D1–D6), depois de subir "Max bars in chart" do terminal Clear para Unlimited.

**Feito em 2026-11-16:** splits A aprovados; gates B3 = gates de proxies; escopo WIN/WDO ≥ 1 min; `b3/b3_data.py` (rolagem, back-adjust, calendário); `B3Market` (stop paga 1 tick extra); runner com linha B3 (ledger próprio em `research/b3/`); adaptador de cripto (126 estratégias portadas); portal com seções Cripto / B3 / Substitutos; agentes em WIN/WDO alternando 1m e 5m.

**Demonstração na demo:** a P-004 (reprovada na validação) roda só como demonstração, não evidência. Depois entraram os demais robôs ([[Robos-demo]]).

**Como aplicar:** nunca ler a validação duas vezes nem o teste final (o dono destranca). Leituras novas passam por `b3/proxy_research.py` para contar como tentativas. Evidência de dry-run só com regra aprovada na validação. Ver [[B3-WIN-WDO]].
