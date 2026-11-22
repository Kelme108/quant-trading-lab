---
tipo: mapa
atualizado: 2026-11-22
tags: [cerebro, mapa]
---

# Mapa do repositório

Convenção: **versionado** = vai no git; **local** = ignorado, precisa ser reconstruído (ver [[Como-rodar-em-outro-ambiente]]).

| Pasta / arquivo | O que é | Nota |
|---|---|---|
| `CLAUDE.md` | Instruções que o Claude lê ao abrir o repositório | [[00-LEIA-PRIMEIRO]] |
| `bootstrap.py`, `requirements*.txt` | Preparo do ambiente (venv, dependências, pastas locais, diagnóstico) | [[Onboarding-equipe]] |
| `CONTRIBUTING.md`, `.github/` | Regras de colaboração, modelo de PR e CI | [[Onboarding-equipe]] |
| `docs/cerebro/` | **Este cofre** (Obsidian) | |
| `docs/` | Planos, protocolos e manuais longos (alguns datados) | ver abaixo |
| `b3/` | **Linha B3**: dados, calendário, custos, mercados, esteira, menu de saídas, buscas, regras | [[B3-WIN-WDO]] |
| `b3/families/` | Famílias de regras da esteira (`b002_agent.py`...) | [[Esteira]] |
| `b3/proxy_rules/` | Regras P-NNN escritas por agentes (P-032 inclusive) | [[Lab-de-pesquisa]] |
| `b3/config/` | Configurações **pré-registradas** (splits, gates, programa, esteira, menu de saídas) | [[Regras-inviolaveis]] |
| `b3/data/` | Coleta MT5 (histórico, gravador de ticks) | [[Dados]] |
| `b3/esteira.py`, `esteira_cycle.py`, `esteira_live.py` | Filtro da esteira, ciclo horário, regra da esteira no motor ao vivo | [[Esteira]] |
| `b3/exit_menu.py`, `p026_lab.py`, `exit_study.py` | Saídas S1–S4, laboratório da P-026, estudo de saídas | [[Menu-de-saidas]] |
| `live/` | **Motor de execução** MT5 (risco, journal, kill switch, comandos) | [[Engine-live]] |
| `live/config/` | Um JSON por robô (`demo-b3-*.json`) e exemplos | [[Robos-demo]] |
| `live/strategies/b3_rule.py` | Liga uma regra de pesquisa ao motor | [[Engine-live]] |
| `lab/` | Laboratório: orquestrador, gates, registro, portal, agentes | [[Lab-de-pesquisa]] |
| `lab/dashboard.py` + `lab/dashboard_assets/` | Portal local (HTML/JS) | [[Portal]] |
| `lab/esteira_portal.py`, `lab/dashboard_assets/esteira.js` | Seção **Esteira** do portal (só leitura dos arquivos da esteira) | [[Portal]] |
| `research/` | Ledgers, manifestos, propostas, relatórios, resultados | |
| `research/b3/` | Resultados da linha B3 (esteira, exit_menu, buscas, trades) | [[Resultados-B3]] |
| `research/proxies/` | Linha de proxies (encerrada) | [[2026-11-14-proxies-indices]] |
| `research/experiments/`, `manifests/` | Linha cripto: um item por hipótese | [[Cripto-Freqtrade]] |
| `user_data/strategies/` | Estratégias Freqtrade (cripto) | [[Cripto-Freqtrade]] |
| `user_data/data/` | **Local**: dados de mercado (cripto e B3) | [[Dados]] |
| `tests/` | `tests/b3`, `tests/live` e a suíte antiga (`tests/archive`) | [[Como-rodar-em-outro-ambiente]] |
| `ops/windows/` | Launchers `.cmd` e instaladores `.ps1` de tarefas | [[Operacao-Windows]] |
| `ops/linux/`, `ops/vps/` | Migração para Linux e bootstrap de VPS | [[Operacao-Windows]] |
| `ops/state/` | **Local**: pausas, logs de ciclo, saída do menu de saídas | |
| `.claude/agents/`, `.claude/skills/` | Agentes da pesquisa e skills `trader-*` | [[Agentes-e-skills]] |
| `forward/`, `docker-compose*.yml`, `testnet/` | Dry-run Freqtrade e testnet (cripto) | [[Cripto-Freqtrade]] |
| `reports/`, `research_notes/` | Relatórios de pesquisa na web (ex.: panorama de trading quantitativo e IA, 2026-11-21) e as notas de apoio | [[Lab-de-pesquisa]] |
| `bot.py` | Script antigo, fora do laboratório | |

## Documentos longos em `docs/`

| Arquivo | Assunto | Situação |
|---|---|---|
| [plano-b3-win-wdo.md](../plano-b3-win-wdo.md) | Plano da linha B3 | vigente |
| [plano-b3-reuso.md](../plano-b3-reuso.md) | Reuso do motor para B3 (aprovado 2026-11-16) | vigente |
| [plano-busca-padroes-b3.md](../plano-busca-padroes-b3.md) | Busca de padrões A/B/C | histórico |
| [plano-fluxo-ticks-b3.md](../plano-fluxo-ticks-b3.md) | Programa de ticks | vigente |
| [plano-gestao-saida-b3.md](../plano-gestao-saida-b3.md) | Estudo de saídas | histórico |
| [plano-portal-proxies.md](../plano-portal-proxies.md) | Portal de índices | histórico |
| `runbook-ao-vivo.md` | Operação da seção "ao vivo" | rascunho, **ainda sem commit** (frente de controles ao vivo; ver [[Publicar-no-GitHub]]) |
| [funcionamento-geral.md](../funcionamento-geral.md) | Manual geral da linha **cripto**, de 2026-11-08 | **envelhecido** |
| [protocolo-validacao-v3.md](../protocolo-validacao-v3.md) | Protocolo de validação | vigente |
| [migracao-linux.md](../migracao-linux.md) | Mover o laboratório para Linux | só linha cripto |
| [checklist-operacao-real.md](../checklist-operacao-real.md) | Pré-requisitos de qualquer operação real | vigente |

## Onde ficam os "sinais vitais"

- Esteira: `research/b3/esteira/` (ledger, famílias, log de ciclos).
- Menu de saídas: `research/b3/exit_menu/` (relatórios) e `ops/state/exit_menu/` (trabalho local).
- Robôs: `live/logs/`, `live/journal.<robô>.sqlite`, `live/state/`. Todos locais.
- Pausas: `ops/state/STOP_ESTEIRA`, `ops/state/STOP_PROXY_CYCLES`, `live/STOP`.
