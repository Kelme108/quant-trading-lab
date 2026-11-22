---
tipo: decisao
data: 2026-11-06
atualizado: 2026-11-19
tags: [cerebro, decisao]
---

# Foco em day trade com muitos trades por dia

**Data:** 2026-11-06 (reforçado em 11-08, 11-09, 11-12 e 11-16)

O dono quer **day trade** com **muitos trades por dia** (ideal 1–4 por par por dia, 400–1500 por ano), para formar evidência de dry-run e ao vivo em dias, não em meses. Regras lentas com poucos trades por ano (a H-004) não servem, por melhor que seja o backtest. Aceita gasto alto de agente.

- **Regra de inatividade (D1, 2026-11-13)**: substituiu a regra de 2 dias por "esperado × observado". Um robô é aposentado quando seus trades fechados após T dias ficam abaixo do 1º percentil da própria exploração em janelas de T dias, ou quando fica parado mais que o maior intervalo da exploração. Motivo: trades vêm em rajadas; a regra de 2 dias aposentava ~92% até dos melhores antes do dia 14. Código: `lab/activity.py`.
- **B3 (2026-11-16)**: piso de **500 trades/ano por mercado** nas propostas novas (`b3/config/b3_program.json`).
- **Fontes**: evidência primeiro, depois repositórios de robôs; os conceitos ICT/SMC foram todos ruído.
- **Ressalva a repetir**: na exploração de WIN as regras frequentes perderam por trade; só a P-004 (246/ano) passou a exploração.

**Como aplicar:** guiar agentes para 1m/5m com saída forçada no fim do dia e movimento bruto bem acima do custo. Nunca propor regra lenta.

Relacionadas: [[2026-11-13-decisoes-estruturais]], [[2026-11-16-timeframes-1-5-15]].
