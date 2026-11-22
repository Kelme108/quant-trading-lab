---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, lab, pesquisa, gates]
---

# Laboratório de pesquisa (`lab/`)

Núcleo determinístico em Python. Nasceu para a linha cripto e foi reaproveitado pela B3. **Agentes escrevem texto e código; o laboratório decide.** Filosofia completa no [README](../../../README.md#filosofia).

## Princípios (valem para qualquer linha)

1. Hipótese registrada **antes** de rodar (regra ex-ante, dados visíveis, número de testes anteriores).
2. Divisão cronológica: exploração, validação (lida uma vez), teste final (trancado).
3. Penalidade por múltiplos testes: a barra de lucro sobe com cada variante da família.
4. Custos conservadores em cenários (otimista, base, conservador, estresse).
5. Resultado negativo é resultado: hipóteses rejeitadas ficam no registro.

## Peças

| Arquivo | Papel |
|---|---|
| `lab/orchestrator.py`, `pipeline.py` | Ciclo: propor → implementar → testar → decidir → revisar |
| `lab/gates.py`, `config/gates.json` | Portões (cripto). B3 usa `b3/config/gates_b3.json` |
| `lab/guard.py` | Hash antes/depois de cada passo de agente; restaura arquivos protegidos |
| `lab/strategy_check.py` | Análise estática do código gerado (só numpy/pandas, sem E/S de arquivo) |
| `lab/runner.py` | Roda backtests; tem a linha `b3` que grava em `research/b3/` |
| `lab/registry.py` | Registro SQLite (`research/lab.sqlite`, local) com a contagem de tentativas |
| `lab/gitops.py` | Commita **só** os caminhos informados |
| `lab/stats.py`, `analytics.py` | DSR, PBO, estatísticas |
| `lab/autopilot.py`, `dryrun.py`, `forward.py` | Política de dry-run de cripto |
| `lab/dashboard.py` | Portal ([[Portal]]) |

## Registros

- `research/hypothesis-ledger.md`: hipóteses H-NNN (cripto), gerado do banco.
- `research/registry-dump.sql`: cópia em SQL do banco, versionada.
- `research/command-log.md`: comandos e invalidações.
- `research/b3/ledger.jsonl`, `research/proxies/ledger.jsonl`: linhas B3 e proxies.
- **Faça backup do banco**: perder o contador apaga a penalidade por múltiplos testes.

## Sessões em paralelo

Mais de uma sessão do Claude pode mexer aqui. Ver [[Operacao-Windows]] e [[Regras-inviolaveis]].
