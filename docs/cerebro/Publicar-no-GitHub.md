---
tipo: guia
atualizado: 2026-11-22
tags: [cerebro, git, publicacao, onboarding]
---

# Publicar no GitHub

**Situação em 2026-11-22:** nada foi enviado (`git push` nunca rodou). O remoto `origin` já aponta para o repositório do dono. O que está commitado reproduz o laboratório a partir de um clone limpo (verificação abaixo); o que ficou de fora é de propósito e está listado aqui. Quem pode empurrar é o dono: só a pedido dele.

## Decisões do dono antes do primeiro push

| # | Decisão | Por que importa | Recomendação do Claude |
|---|---|---|---|
| 1 | **Visibilidade**: privado ou público | O repositório traz toda a pesquisa e a lógica de risco, nomes de servidor da corretora nas notas, o nome do dono nas aprovações (`lab/config/*.json`, `research/validation-protocol-v2.md`) e o nome de usuário do Windows no dump do registro (`research/registry-dump.sql`) | **Privado**, convidando as pessoas pelo nome. Tornar público só depois de tirar esses nomes |
| 2 | **Licença** | Hoje nenhuma: o README diz "todos os direitos reservados", e sem licença ninguém pode reutilizar legalmente | Só para convidados: deixar como está. Para outros usarem e derivarem: **MIT**, mantendo o aviso de que não é recomendação de investimento |
| 3 | **Configs da conta real** (`live/config/live-b3-*.json` e `.sha256`, com `allow_real: true`) | Quem clonasse poderia religar um robô de dinheiro real por engano | **Manter fora do repositório compartilhado**: ignorar no `.gitignore`, publicar só um exemplo com `allow_real: false`, e fazer `test_the_three_shipped_real_configs_are_valid_and_pinned` pular quando os arquivos não existirem |
| 4 | **Frente "controles ao vivo"** (botões da conta real no portal) | Está no disco, sem commit: `live/core/control.py`, `live/core/engine.py`, `live/run.py`, partes de `lab/dashboard.py` e `lab/demo_b3.py`, `lab/dashboard_assets/live_b3.js`, `docs/runbook-ao-vivo.md` e os testes `test_live_control`, `test_live_real_override`, `test_lab_dashboard_control`, `test_live_readiness_safety` | Commitar tudo junto, e só quando o dono aprovar o merge da branch `feat/portal-controls` ([[2026-11-17-portal-controles-ao-vivo]]) |
| 5 | **Lote B-010 abandonado** | `b3/families/b010_agent.py` e `research/b3/esteira/context/B-010.md` são de um lote que o guard derrubou em 2026-11-18 antes do registro (as famílias E-089 a E-098 não estão no `families.jsonl`). Commitá-los criaria famílias sem registro | Apagar os dois arquivos. Se o dono quiser as famílias, registrar um lote novo (conta como tentativas novas) |
| 6 | **Nome do dono nas aprovações** | Aparece em `approved_by` e no texto de emendas | Manter (é crédito) ou trocar por "dono" antes de publicar |

## O que está no Git e o que fica local

- **Versionado:** código (`b3/`, `lab/`, `live/`, `ops/`), configs pré-registradas (`b3/config/`), configs dos robôs de **demo**, ledgers e relatórios (`research/`), testes, este cofre, agentes e skills (`.claude/`), CI (`.github/`).
- **Local (ignorado):** `.env*` (menos os `.env.example`), dados de mercado (`user_data/data/`), bancos (`research/lab.sqlite`, `live/journal*.sqlite`), `ops/state/`, logs, `live/state/`, `live/commands/`, `.venv/`, `.claude/settings.local.json`.
- Quem clona reconstrói o local seguindo [[Como-rodar-em-outro-ambiente]]. Os dados B3 só existem com o terminal da Clear; sem eles, a pesquisa pesada não roda, mas cofre, testes e leitura dos resultados funcionam ([[Onboarding-equipe]]).

## Verificar um clone limpo

```bash
git clone <url> trade-lab && cd trade-lab
python bootstrap.py                                   # venv, dependências, pastas locais, diagnóstico
.venv/Scripts/python -m pytest tests/test_cerebro_vault.py tests/b3 tests/live -q    # o que a CI roda
```

Resultado em 2026-11-22: _a preencher_.

## Antes de cada push

1. `git status`: nenhum `.env`, banco ou dado de mercado.
2. Segredos: `python -m pytest tests/test_cerebro_vault.py` varre o cofre; busque também `password`, `api_key` e `secret` nos arquivos novos.
3. Testes: o comando da CI acima.
4. `git remote -v` confere para onde vai.
5. A esteira também comita (`exp(esteira):`). Em outra máquina, `git pull --rebase` antes de empurrar.
6. Commit só dos seus caminhos ([[Regras-inviolaveis]]).

## O que a CI cobre

Cofre, `tests/b3` e `tests/live`. A suíte antiga (`tests/archive`, linha cripto) tem falhas preexistentes por interferência entre testes e fica fora da CI ([[Pendencias-e-calendario]]).
