---
tipo: manual
atualizado: 2026-11-20
tags: [cerebro, onboarding, equipe, clone]
---

# Onboarding: do clone ao primeiro resultado

Para quem acabou de clonar o repositório (pessoa ou Claude). Tempo: ~15 minutos até os testes passarem, mais o que o MetaTrader exigir.

## 1. Clonar e preparar

```bash
git clone https://github.com/Kelme108/quant-trading-lab.git
cd quant-trading-lab
python bootstrap.py --test       # cria .venv, instala requirements.txt, cria pastas locais, roda a suíte de sanidade
python bootstrap.py --check      # diagnóstico: o que está ok e o que falta (dados, MT5, claude, docker)
```

Requisito: Python 3.13+ (referência: 3.14). Windows, Linux e macOS rodam a pesquisa e os testes. **O MetaTrader 5 só roda no Windows.**

## 2. Ler, nesta ordem

1. [[Regras-inviolaveis]]: o que nunca fazer.
2. [[Estado-atual]]: onde o trabalho parou.
3. [[Mapa-do-repositorio]] e [[Glossario]].
4. `CONTRIBUTING.md` (raiz): branches, PR, segredos, quem roda o quê.

## 3. O que funciona em cada nível de acesso

| Você tem | Funciona |
|---|---|
| Só o clone | Ler tudo; rodar testes; portal local com os resultados versionados; escrever código e notas |
| Clone + dados B3 (`user_data/data/b3/clear/`) | Esteira, menu de saídas, buscas, estudos (`python -m b3.esteira status`, `python -m b3.exit_menu run ...`) |
| Clone + terminal Clear demo aberto e logado (Windows) | Baixar histórico, rodar os robôs de demo (`ops\windows\demo-b3.cmd <robô>`) |
| Claude Code instalado | Agentes da esteira e do pipeline ([[Agentes-e-skills]]); gasto limitado pelo teto diário |
| Docker | Só a linha cripto, pausada ([[Cripto-Freqtrade]]) |

Os dados de mercado **não estão no git**. Peça ao dono do projeto (ou baixe com o terminal Clear) e veja [[Dados]] e [[Como-rodar-em-outro-ambiente]].

## 4. Regras de convivência (resumo)

- **Um computador roda a esteira e os robôs.** Combine antes de ligar em outro.
- **Não edite arquivos rastreados na máquina que roda a esteira** sem pausá-la (`ops/state/STOP_ESTEIRA`).
- **Nunca** commite segredo, número de conta, e-mail ou caminho com seu usuário. Existe teste que barra isso nas notas (`tests/test_cerebro_vault.py`).
- **Só o dono** muda gates, splits, teste final e configs `approved_by_owner`.
- PR pequeno, com a checklist de `.github/pull_request_template.md`.

## 5. Comandos que você vai usar

```bash
python -m pytest tests/b3 tests/live tests/test_cerebro_vault.py -q   # rode da raiz; confira o código de saída
python -m b3.esteira status                                           # famílias e limites
python -m b3.esteira_cycle status                                     # ciclo horário: gasto do dia, pausa
python -m b3.exit_menu run --family E-118 --market WIN                # saídas S1..S4 numa família
python -m lab.dashboard serve --open                                  # portal em 127.0.0.1:8765, somente leitura
```

## 6. Como registrar o que você aprendeu

- Estado mudou? Atualize [[Estado-atual]] (com a data).
- Decisão do dono? Copie [[modelo-decisao]] para `decisoes/AAAA-MM-DD-assunto.md` e ligue em [[Decisoes-indice]].
- Resultado de pesquisa? Ledger em `research/` e resumo em [[Resultados-B3]]; operação da demo em [[Demo-diario]].
- Algo para o dono decidir? Coloque em [[Pendencias-e-calendario]].
