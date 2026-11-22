---
tipo: glossario
atualizado: 2026-11-19
tags: [cerebro, glossario]
---

# Glossário

| Termo | Significado |
|---|---|
| **WIN / WDO** | Mini índice Bovespa e mini dólar da B3. Contrato de vencimento corrente (`WINZ26`, `WDOZ26`); `WIN$N`/`WDO$N` é a série contínua para pesquisa |
| **Roll** | Troca do contrato vencendo pelo seguinte. Pendente: [[Pendencias-e-calendario]] |
| **Exploração / validação / teste final** | Três fatias cronológicas dos dados. Procura-se na exploração; a validação é lida **uma vez**; o teste final está **trancado** ([[Regras-inviolaveis]]) |
| **Splits A** | Divisão aprovada da B3: exploração 2021-11-16..2024-07-01, validação ..2025-10-01, teste final depois |
| **Tentativa (trial)** | Toda variante lida. Entra na contagem do DSR; mais tentativas, barra mais alta |
| **DSR / PBO** | Deflated Sharpe Ratio (corrige múltiplos testes) e Probabilidade de Overfitting do Backtest. Relatórios; são a barra para dinheiro real |
| **Gate (portão)** | Critério fixo em código que aprova ou reprova. Agentes não alteram |
| **Guard** | Verificação por hash antes/depois de um passo de agente; mudança fora do permitido derruba o ciclo |
| **Esteira** | Linha de montagem de **famílias** de regras simples ([[Esteira]]) |
| **Família (E-NNN)** | Uma ideia de regra com grade pequena de parâmetros (até 3 parâmetros) |
| **Variante** | Uma combinação de parâmetros de uma família num timeframe |
| **Plateau** | Vizinhos de uma variante também lucrativos; evita pico isolado |
| **V** | Volatilidade: média do retorno absoluto de 30 min no mesmo minuto do dia, nas últimas 20 sessões |
| **S1..S4** | Saídas em unidades de V: S1 stop 1V/alvo 1V; S2 1,5V/0,75V; S3 1V/2V; S4 stop 1V com breakeven/trailing ([[Menu-de-saidas]]) |
| **P-NNN** | Regra proposta por agente (`b3/proxy_rules/`), com ledger próprio |
| **Candidata** | Passou nos filtros da exploração. Não é aprovada |
| **p90** | Cenário de custo pessimista (percentil 90 do custo medido). Regra de implantação: candidata **e** lucro > 0 no p90 |
| **Controle aleatório** | Mesmos horários e lados sorteados; a regra precisa bater esse acaso |
| **Taxa de acerto** | Parcela de trades com resultado líquido > 0. Depende mais da saída do que da regra |
| **Demo ≠ evidência** | Robô na demo só observa; não aprova regra |
| **Hedging / netting** | Modos de conta MT5. As contas do dono são **hedging** (`margin_mode == 2`) |
| **Magic** | Número que identifica as ordens de cada robô (261xxx, 262xxx) |
| **MOVE_STOP** | Ação do motor que aperta o stop (só aperta, nunca afrouxa) via `TRADE_ACTION_SLTP` |
| **Journal** | Diário SQLite de cada robô (`live/journal.<robô>.sqlite`) |
| **Kill switch** | `live/STOP`: robô zera e para de enviar ordens |
| **Freeze** | Congelamento de hash de uma estratégia de cripto antes do dry-run |
| **Holdout prospectivo** | Dados futuros reais, depois do congelamento (linha cripto) |
| **Lane** | Linha de trabalho: cripto, proxies, B3 |
