---
tipo: manual
atualizado: 2026-11-19
tags: [cerebro, ambiente, clone]
---

# Como rodar em outro ambiente

Objetivo: depois de `git clone`, um Claude (ou uma pessoa) entende o projeto e consegue reproduzir o que for reproduzível. O que **não** vem no clone está listado abaixo.

## 1. O que o clone traz e o que não traz

| Traz | **Não** traz (reconstruir ou pedir ao dono) |
|---|---|
| Todo o código (`b3/`, `lab/`, `live/`), testes, configs pré-registradas, planos, este cofre | **Dados de mercado** (`user_data/data/`): B3 vem do terminal Clear; cripto vem da Binance pública |
| Ledgers e resultados da pesquisa (`research/b3/`, `research/proxies/`) | `research/lab.sqlite` (registro da linha cripto) e `live/journal*.sqlite` (diários dos robôs) |
| `research/registry-dump.sql` (cópia em SQL do registro cripto) | `ops/state/` (pausas, logs, saída do menu de saídas) e `live/state/`, `live/logs/` |
| Launchers e instaladores em `ops/` | `live/.env`, `live/.env.real`, `live/config/live.json` (credenciais e config real) |

> O histórico de WIN/WDO só pode ser baixado com um **terminal MetaTrader 5 da Clear aberto e logado na conta demo**. Sem ele, a linha B3 de pesquisa e os robôs não rodam, mas todo o código e os resultados registrados continuam legíveis.

## 2. Requisitos

- **Python 3.13+** (referência: 3.14). Dependências em `requirements.txt` (núcleo: `numpy`, `pandas`, `pyarrow`, `tzdata`, `pytest`) e `requirements-research.txt` (pesquisa de padrões: `lightgbm`, `scikit-learn`, `scipy`). O `bootstrap.py` instala tudo num `.venv`.
- **Pacote `MetaTrader5`** (`live/requirements.txt`): **só Windows**, com o terminal aberto. Instale num venv dedicado `live/.venv`.
- **Claude Code** (CLI `claude`) para a esteira e o pipeline de agentes.
- **Docker + Compose v2** só para a linha cripto (Freqtrade 2026.9).
- Os launchers `ops/windows/*.cmd` descobrem sozinhos a raiz do repositório e o Python (`ops/windows/_env.cmd`: `.venv` da raiz, depois `C:\Python314`, depois `python` do PATH). Os instaladores `.ps1` usam a pasta do próprio script. Nada depende de `D:\Trade-Initial`.

## 3. Passo a passo (sem dados)

```bash
git clone https://github.com/Kelme108/quant-trading-lab.git
cd quant-trading-lab
python bootstrap.py --test        # cria .venv, instala requirements.txt, cria as pastas locais e roda a suíte de sanidade
python bootstrap.py --check       # diagnóstico: o que está ok e o que falta
# ative o ambiente (.venv\Scripts\activate no Windows; source .venv/bin/activate no Linux/macOS) e use:
python -m b3.esteira status
python -m lab.dashboard serve --open            # portal em http://127.0.0.1:8765
```

Passo a passo completo e o que funciona em cada nível de acesso: [[Onboarding-equipe]]. Regras de colaboração: `CONTRIBUTING.md`. Modelo das variáveis de ambiente: `live/.env.example` (robôs de demo não usam senha).

Se um teste falhar por falta de dado local, a mensagem diz qual arquivo falta.

## 4. Com acesso à conta demo (Windows)

1. Dono abre o terminal Clear e entra na conta **demo** (nunca a real).
2. Baixar histórico (anexa ao terminal sem senha): `python -m b3.data.mt5_history ... --attach b3/config/broker_mt5.json`. Detalhes em [[Dados]].
3. Para ligar um robô: `ops\windows\demo-b3.cmd demo-b3-p032-win` (o nome é o do JSON em `live/config/`). Lista em [[Robos-demo]].
4. Para a esteira: tarefa `TradeInitial-EsteiraCycle` (instalador `ops/windows/install-esteira-task.ps1`, rodado pelo dono). Pare com `ops/state/STOP_ESTEIRA`.

## 5. Linux

Há manual de migração em [../migracao-linux.md](../migracao-linux.md) e scripts em `ops/linux/`, **escritos para a linha cripto** e nunca executados em Linux. O MT5 não roda em Linux sem camada extra: a linha B3 ao vivo continua no Windows.

## 6. Antes de qualquer ação, leia

[[Regras-inviolaveis]]. Principalmente: nada de dinheiro real, nada de credencial em arquivo, validação só uma vez, e pausar a esteira antes de editar o repositório.

## 7. Coisas que costumam dar errado

- `ModuleNotFoundError: 'b3'` ou `'live'`: rode da raiz do repositório (ou com `PYTHONPATH=.`).
- Hora dos ticks do MT5: veja [[2026-11-16-relogio-tick-mt5]].
- Calendário 2027 ausente: o código recusa anos sem feriado oficial. Isso é intencional ([[Pendencias-e-calendario]]).
- Duas sessões rodando a mesma fila: confira processos antes de iniciar ([[Operacao-Windows]]).
